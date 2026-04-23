const fs = require("fs");
const path = require("path");

async function copy() {
  const from = path.join(__dirname, "..", "dist");
  const to = path.join(__dirname, "..", "..", "apiServer", "static");
  try {
    await fs.promises.rm(to, { recursive: true, force: true });
    await fs.promises.mkdir(to, { recursive: true });
    await fs.promises.cp(from, to, { recursive: true });
    console.log(`Copied ${from} -> ${to}`);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

copy();
