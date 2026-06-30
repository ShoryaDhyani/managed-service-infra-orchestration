import os
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

# Redis setup
publisher = Redis.from_url(os.getenv("REDIS_URL"))

# S3 setup
s3_client = boto3.client(
    "s3",
    region_name="ap-south-1",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
)

PROJECT_ID = os.environ.get("PROJECT_ID")
TYPE = os.environ.get("PROJECT_TYPE")

# Directories that should never be uploaded
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".cache",
    ".next",
    ".vite",
}


def publish_log(log):
    publisher.publish(f"logs:{PROJECT_ID}", json.dumps({"log": log}))


def stream_output(pipe, prefix=""):
    for line in pipe:
        text = line.decode(errors="replace").strip()
        if text:
            print(f"{prefix}{text}")
            publish_log(f"{prefix}{text}")


def upload_file(file_path, relative_path):
    content_type, _ = mimetypes.guess_type(str(file_path))
    content_type = content_type or "application/octet-stream"

    with open(file_path, "rb") as f:
        s3_client.put_object(
            Bucket="msio-outputs-1",
            Key=f"__outputs/{PROJECT_ID}/{relative_path.as_posix()}",
            Body=f,
            ContentType=content_type,
        )


def main():
    print("Executing main.py")
    publish_log("Build Started...")

    out_dir_path = Path(__file__).parent / "output"

    if not out_dir_path.exists():
        publish_log(f"Error: output directory not found at {out_dir_path}")
        print(f"Error: output directory not found at {out_dir_path}")
        return

    if TYPE == "react":
        process = subprocess.Popen(
            f'cd "{out_dir_path}" && npm install && npm run build',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        t1 = threading.Thread(target=stream_output, args=(process.stdout,))
        t2 = threading.Thread(target=stream_output, args=(process.stderr, "error: "))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        return_code = process.wait()

        if return_code != 0:
            publish_log(f"Build failed with exit code {return_code}")
            print(f"Build failed with exit code {return_code}")

            requests.post(
                f'{os.getenv("API_URL")}/buildstatus',
                json={
                    "slug": PROJECT_ID,
                    "projectStatus": "Failed",
                },
                headers={
                    "Authorization": f'Bearer {os.getenv("SERVICE_TOKEN")}',
                },
            )
            return

        print("Build Complete")
        publish_log("Build Complete")

        dist_folder_path = out_dir_path / "dist"

    else:
        dist_folder_path = out_dir_path

    if not dist_folder_path.exists():
        publish_log("Error: dist folder not found after build")
        print("Error: dist folder not found after build")

        requests.post(
            f'{os.getenv("API_URL")}/buildstatus',
            json={
                "slug": PROJECT_ID,
                "projectStatus": "Failed",
            },
            headers={
                "Authorization": f'Bearer {os.getenv("SERVICE_TOKEN")}',
            },
        )
        return

    publish_log("Starting to upload")

    for root, dirs, files in os.walk(dist_folder_path):
        # Skip unwanted directories completely
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            file_path = Path(root) / filename
            relative_path = file_path.relative_to(dist_folder_path)

            print(f"uploading {relative_path}")
            publish_log(f"uploading {relative_path.as_posix()}")

            try:
                upload_file(file_path, relative_path)
                print(f"uploaded {relative_path}")
                publish_log(f"uploaded {relative_path.as_posix()}")

            except Exception as e:
                print(f"Failed to upload {relative_path}: {e}")
                publish_log(f"Failed to upload {relative_path.as_posix()}: {e}")

                requests.post(
                    f'{os.getenv("API_URL")}/buildstatus',
                    json={
                        "slug": PROJECT_ID,
                        "projectStatus": "Failed",
                    },
                    headers={
                        "Authorization": f'Bearer {os.getenv("SERVICE_TOKEN")}',
                    },
                )
                return

    publish_log("Done")

    requests.post(
        f'{os.getenv("API_URL")}/buildstatus',
        json={
            "slug": PROJECT_ID,
            "projectStatus": "live",
        },
        headers={
            "Authorization": f'Bearer {os.getenv("SERVICE_TOKEN")}',
        },
    )

    print("Done...")


main()