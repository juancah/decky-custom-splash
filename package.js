// scripts/package.js
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const fsp = fs.promises;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const root = __dirname; // project root
const releaseDir = path.join(root, "releases/SDH-CustomSplash");

const include = [
  "dist",
  "backend",
  "main.py",
  "plugin.json",
  "decky.pyi",
  "package.json",
  "README.md",
  "lib",
  "assets",
  "defaults"
];

// recursively copy directory
async function copyDir(src, dest) {
  await fsp.mkdir(dest, { recursive: true });
  const entries = await fsp.readdir(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      await copyDir(srcPath, destPath);
    } else if (entry.isFile()) {
      await fsp.copyFile(srcPath, destPath);
    }
  }
}

// delete directory if exists
async function rmDirSafe(dir) {
  if (!fs.existsSync(dir)) return;
  const entries = await fsp.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await rmDirSafe(fullPath);
    } else {
      await fsp.unlink(fullPath);
    }
  }
  await fsp.rmdir(dir);
}

async function main() {
  await rmDirSafe(releaseDir);
  await fsp.mkdir(releaseDir, { recursive: true });

  for (const item of include) {
    const src = path.join(root, item);
    if (fs.existsSync(src)) {
      const dest = path.join(releaseDir, item);
      const stat = await fsp.stat(src);
      if (stat.isDirectory()) {
        await copyDir(src, dest);
      } else {
        await fsp.copyFile(src, dest);
      }
      console.log(`Copied ${item}`);
    } else {
      console.warn(`Skipped missing ${item}`);
    }
  }

  console.log(`\n✅ Release folder ready at: ${releaseDir}`);
  console.log(`Now run: cd releases && zip -r SDH-CustomSplash.zip SDH-CustomSplash`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
