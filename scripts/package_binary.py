"""Create an architecture-labelled archive and SHA-256 checksum."""
import argparse
import hashlib
from pathlib import Path
import platform
import re
import tarfile
import tomllib

parser = argparse.ArgumentParser()
parser.add_argument("--arch", choices=["amd64", "arm64"], required=True)
parser.add_argument("--tag", default="")
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[a-zA-Z0-9.+-]*)", version):
    raise SystemExit("Unsafe package version")
if args.tag and args.tag != "v" + version:
    raise SystemExit("Release tag must match the package version: v" + version)
expected = {"amd64": "x86_64", "arm64": "aarch64"}[args.arch]
if platform.machine() != expected:
    raise SystemExit("Build architecture does not match archive label")
output = root / "dist/release"
output.mkdir(parents=True, exist_ok=True)
archive = output / f"ssc-{version}-linux-{args.arch}.tar.gz"
with tarfile.open(archive, "w:gz") as bundle:
    bundle.add(root / "dist/binary/ssc", arcname="ssc")
    bundle.add(root / "docs/BINARY.md", arcname="README.md")
    bundle.add(root / ".env.example", arcname=".env.example")
archive.with_suffix(archive.suffix + ".sha256").write_text(f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n")
print(archive)
