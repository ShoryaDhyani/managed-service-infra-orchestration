import os
import re
import subprocess
import json
import mimetypes
import threading
from pathlib import Path

import boto3
from redis import Redis
from dotenv import load_dotenv
import requests

load_dotenv()

publisher = Redis.from_url(os.getenv("REDIS_URL"))

s3_client = boto3.client(
    "s3",
    region_name="ap-south-1",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
)

PROJECT_ID = os.environ.get("PROJECT_ID")
TYPE = os.environ.get("PROJECT_TYPE")

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".cache", ".next", ".vite"}

DEFAULT_NODE_VERSION = "20"

LOCKFILE_VERSION_TO_NODE = {
    1: "14",
    2: "18",
    3: "20",
}

BUILD_OUTPUT_DIRS = (
    "dist",
    "build",
    ".output",
    "out",
    ".next",
    ".nuxt",
    "public",
)


def find_build_output_dir(project_root: Path) -> Path | None:
    """
    Find the build output directory.

    Priority:
      1. Common build directory names.
      2. Any directory containing index.html.
      3. Most recently modified candidate.
    """

    # Try common output directories first.
    for name in BUILD_OUTPUT_DIRS:
        candidate = project_root / name
        if candidate.exists() and candidate.is_dir():
            publish_log(f"Found build directory: {candidate}")
            return candidate

    # Search recursively for directories containing index.html.
    candidates = []

    for index_file in project_root.rglob("index.html"):
        parent = index_file.parent

        # Ignore source folders.
        if any(skip in parent.parts for skip in (
            "node_modules",
            ".git",
            "src",
            "__pycache__",
        )):
            continue

        candidates.append(parent)

    if candidates:
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        publish_log(f"Detected build directory: {candidates[0]}")
        return candidates[0]

    publish_log("No build output directory found.")
    return None

# nvm is baked into the Docker image, hardcode the path so it stays stable.
NVM_DIR = "/root/.nvm"
NVM_SOURCE = (
    f'export NVM_DIR="{NVM_DIR}" && '
    f'[ -s "{NVM_DIR}/nvm.sh" ] && . "{NVM_DIR}/nvm.sh"'
)

BUILD_OUTPUT_DIRS = ("dist", "build", ".output", "out")


# ── Logging ────────────────────────────────────────────────────────────────

def publish_log(log: str):
    try:
        publisher.publish(f"logs:{PROJECT_ID}", json.dumps({"log": log}))
        print(log, flush=True)

    except Exception as e:
        print(f"Failed to publish log: {e}", flush=True)


def stream_output(pipe, prefix: str = ""):
    for line in iter(pipe.readline, ""):
        text = line.rstrip()
        if text:
            msg = f"{prefix}{text}"
            print(msg, flush=True)
            publish_log(msg)


# ── Shell execution ────────────────────────────────────────────────────────

def run_streamed(command: str, cwd: Path | None = None) -> int:
    """Run a bash command, streaming stdout/stderr. Returns exit code."""
    process = subprocess.Popen(
        command,
        shell=True,
        executable="/bin/bash",
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    t1 = threading.Thread(target=stream_output, args=(process.stdout,))
    t2 = threading.Thread(target=stream_output, args=(process.stderr, "error: "))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    return process.wait()


# ── Node version detection ─────────────────────────────────────────────────

def parse_exact_node_major(engine_spec: str) -> str | None:
    """
    Return an explicit major version only when the spec is a concrete target.
    Examples accepted:
      18
      18.x
      ^18.0.0
      ~18.2.1
      >=18 <19
    Examples rejected:
      >=6.9.0
      >=14
      *
    """
    if not engine_spec:
        return None

    spec = engine_spec.strip()

    m = re.fullmatch(r"(?:\^|~)?(\d+)(?:\.\d+)?(?:\.\d+)?", spec)
    if m:
        return m.group(1)

    m = re.fullmatch(r"(?:\^|~)?(\d+)\.x", spec, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    m = re.fullmatch(r">=\s*(\d+)(?:\.\d+)?(?:\.\d+)?\s*<\s*(\d+)", spec)
    if m:
        lower, upper = int(m.group(1)), int(m.group(2))
        if upper == lower + 1:
            return str(lower)

    return None


def read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_required_node_version(out_dir_path: Path) -> str:
    """
    Determine the best starting Node version to try.

    Priority:
      1. package.json -> engines.node, only if it is an explicit target
      2. package-lock.json -> packages[""].engines.node, only if explicit
      3. package-lock.json -> lockfileVersion heuristic
      4. DEFAULT_NODE_VERSION
    """
    pkg_path = out_dir_path / "package.json"
    lock_path = out_dir_path / "package-lock.json"

    if pkg_path.exists():
        try:
            pkg = read_json(pkg_path)
            raw = pkg.get("engines", {}).get("node", "")
            version = parse_exact_node_major(raw)
            if version:
                publish_log(f"package.json engines.node = '{raw}' -> using Node {version}")
                return version
            if raw:
                publish_log(f"package.json engines.node = '{raw}' is a range, starting from Node {DEFAULT_NODE_VERSION}")
        except Exception as e:
            publish_log(f"Warning: could not parse package.json: {e}")

    if lock_path.exists():
        try:
            lock = read_json(lock_path)

            packages = lock.get("packages", {})
            root_pkg = packages.get("", {})
            raw = root_pkg.get("engines", {}).get("node", "")
            version = parse_exact_node_major(raw)
            if version:
                publish_log(f"package-lock.json root engines.node = '{raw}' -> using Node {version}")
                return version

            lv = lock.get("lockfileVersion")
            version = LOCKFILE_VERSION_TO_NODE.get(lv)
            if version:
                publish_log(f"No explicit engines.node found; lockfileVersion={lv} -> using Node {version}")
                return version
        except Exception as e:
            publish_log(f"Warning: could not parse package-lock.json: {e}")

    publish_log(f"No version hint found; defaulting to Node '{DEFAULT_NODE_VERSION}'")
    return DEFAULT_NODE_VERSION


# ── Node setup ─────────────────────────────────────────────────────────────

def verify_nvm() -> bool:
    """Confirm nvm is accessible inside the container."""
    rc = run_streamed(f'{NVM_SOURCE} && command -v nvm')
    if rc != 0:
        publish_log(f"nvm not found at {NVM_DIR} - is it installed in the Docker image?")
        return False
    publish_log("nvm verified")
    return True


def install_node_version(version: str) -> bool:
    """Install and activate a Node version. Returns True on success."""
    rc = run_streamed(f'{NVM_SOURCE} && nvm install {version} && nvm use {version}')
    return rc == 0


def build_version_list(requested_version: str) -> list[str]:
    """
    Build a progressive downgrade list.

    Example:
      20 -> ["20", "18", "16", "14", "lts/*"]
      18 -> ["18", "16", "14", "lts/*"]
    """
    versions: list[str] = []

    major_match = re.search(r"(\d+)", requested_version or "")
    if major_match:
        major = int(major_match.group(1))
        while major >= 14:
            versions.append(str(major))
            major -= 2

    if DEFAULT_NODE_VERSION not in versions:
        versions.append(DEFAULT_NODE_VERSION)

    seen = set()
    ordered = []
    for version in versions:
        if version not in seen:
            seen.add(version)
            ordered.append(version)

    return ordered


def setup_node(requested_version: str) -> list[str] | None:
    """Verify nvm and return Node versions to try."""
    if not verify_nvm():
        return None
    return build_version_list(requested_version)


def clean_previous_build_artifacts(out_dir_path: Path):
    for folder in ("node_modules", "dist", "build", ".next", ".nuxt", ".output", "out"):
        target = out_dir_path / folder
        if target.exists():
            subprocess.run(["rm", "-rf", str(target)], check=False)


# def find_build_output_dir(out_dir_path: Path) -> Path | None:
#     for name in BUILD_OUTPUT_DIRS:
#         candidate = out_dir_path / name
#         if candidate.exists():
#             return candidate
#     return None


# ── Status reporting ───────────────────────────────────────────────────────

def report_failure(reason: str = ""):
    if reason:
        publish_log(f"Build failed: {reason}")
        print(f"Build failed: {reason}", flush=True)

    try:
        requests.post(
            f'{os.getenv("API_URL")}/buildstatus',
            json={"slug": PROJECT_ID, "projectStatus": "Failed"},
            headers={"Authorization": f'Bearer {os.getenv("SERVICE_TOKEN")}'},
        )
    except Exception as e:
        print(f"Failed to report build failure: {e}", flush=True)


# ── S3 upload ──────────────────────────────────────────────────────────────

def upload_file(file_path: Path, relative_path: Path):
    content_type, _ = mimetypes.guess_type(str(file_path))
    content_type = content_type or "application/octet-stream"
    with open(file_path, "rb") as f:
        s3_client.put_object(
            Bucket="msio-outputs-1",
            Key=f"__outputs/{PROJECT_ID}/{relative_path.as_posix()}",
            Body=f,
            ContentType=content_type,
        )


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("Executing main.py", flush=True)
    publish_log("Build Started...")

    out_dir_path = Path(__file__).parent / "output"
    if not out_dir_path.exists():
        report_failure(f"output directory not found at {out_dir_path}")
        return

    if TYPE == "node":
        node_version = get_required_node_version(out_dir_path)
        versions_to_try = setup_node(node_version)

        if versions_to_try is None:
            report_failure("could not access nvm")
            return

        publish_log(f"Node versions to try: {versions_to_try}")

        build_rc = 1
        successful_version = None

        for version in versions_to_try:
            publish_log(f"Trying Node.js {version}...")

            if not install_node_version(version):
                publish_log(f"Could not activate Node.js {version}")
                continue

            clean_previous_build_artifacts(out_dir_path)

            build_rc = run_streamed(
                f'{NVM_SOURCE} && '
                f'nvm use {version} && '
                f'node -v && npm -v && '
                f'cd "{out_dir_path}" && '
                f'npm install --no-audit --no-fund && '
                f'npm run build',
                cwd=out_dir_path,
            )

            publish_log(f"Build exited with code {build_rc} on Node.js {version}")

            if build_rc == 0:
                successful_version = version
                publish_log(f"Build succeeded using Node.js {version}")
                break

            publish_log(f"Build failed with Node.js {version}, trying next version...")

        if build_rc != 0:
            report_failure("Build failed on all attempted Node.js versions")
            return

        publish_log(f"Build Complete using Node.js {successful_version}")

        dist_folder_path = find_build_output_dir(out_dir_path)

        if dist_folder_path is None:
            publish_log("Project structure:")
            for p in sorted(out_dir_path.rglob("*")):
                publish_log(str(p.relative_to(out_dir_path)))

            report_failure("No build output directory found after build.")
            return

        publish_log(f"Uploading from: {dist_folder_path}")

    else:
        dist_folder_path = out_dir_path
        if not dist_folder_path.exists():
            report_failure(f"output folder not found at {dist_folder_path}")
            return

    publish_log(f"Starting to upload from {dist_folder_path.name}")

    for root, dirs, files in os.walk(dist_folder_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in files:
            file_path = Path(root) / filename
            relative_path = file_path.relative_to(dist_folder_path)

            publish_log(f"uploading {relative_path.as_posix()}")
            try:
                upload_file(file_path, relative_path)
                publish_log(f"uploaded {relative_path.as_posix()}")
            except Exception as e:
                report_failure(f"upload failed for {relative_path.as_posix()}: {e}")
                return

    publish_log("Done")
    try:
        requests.post(
            f'{os.getenv("API_URL")}/buildstatus',
            json={"slug": PROJECT_ID, "projectStatus": "live"},
            headers={"Authorization": f'Bearer {os.getenv("SERVICE_TOKEN")}'},
        )
    except Exception as e:
        report_failure(f"could not mark build as live: {e}")
        return

    print("Done...", flush=True)


try:
    main()
except Exception as e:
    print(f"Unhandled exception: {e}", flush=True)
    try:
        publisher.publish(f"logs:{PROJECT_ID}", json.dumps({"log": f"Unhandled exception: {e}"}))
    except Exception:
        pass
    try:
        requests.post(
            f'{os.getenv("API_URL")}/buildstatus',
            json={"slug": PROJECT_ID, "projectStatus": "Failed"},
            headers={"Authorization": f'Bearer {os.getenv("SERVICE_TOKEN")}'},
        )
    except Exception:
        pass
