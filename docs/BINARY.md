# Standalone Linux binary

Download the archive for your CPU from the GitHub release:

- `ssc-VERSION-linux-amd64.tar.gz` for Intel/AMD x86_64.
- `ssc-VERSION-linux-arm64.tar.gz` for ARM64/aarch64.

These are Linux binaries built on Ubuntu 22.04 with glibc 2.35. Use Linux with
glibc 2.35 or newer (for example Ubuntu 22.04+ or Debian 12+); Alpine/musl,
32-bit ARM, macOS, and Windows executables are not included. WSL Ubuntu works.

```bash
sha256sum -c ssc-VERSION-linux-amd64.tar.gz.sha256
tar -xzf ssc-VERSION-linux-amd64.tar.gz
chmod +x ssc
./ssc version
./ssc tui
./ssc connect
```

Python, uv, and Docker are not required to run the binary. Install the system
SSH client and tmux for real SSH and the persistent connection bar; rsync is
required for file transfers and must also exist on the remote server. Ubuntu:

```bash
sudo apt-get install openssh-client tmux rsync
```

Credentials, keys, and preferences remain in `~/.ssh-cred-manager`; SSH keys
are also discovered in `~/.ssh`. Optionally set `SSC_CONFIG_DIR` for another
application storage directory. No user credentials or keys are bundled.

For demos, create `.env` beside the binary with `ENV=development`, then run
`./ssc demo-seed`. Explicit process ENV takes priority. Other modes hide and
block demos. Run `scroll 200` in a demo connection to test overflow.

Theme selection and reset remain in Ctrl+P's command palette and persist.
You may manually place `ssc` in a directory on PATH to use `ssc tui` directly.

The one-file binary extracts runtime libraries into a temporary directory at
startup, so the system temporary directory must allow executable files.

## Build and test locally (Linux or WSL)

Install uv and the system tools `ssh`, `tmux`, `rsync`, and `binutils`, then run
from the repository root:

```bash
./scripts/build_binary.sh
.venv/bin/python scripts/test_binary.py dist/binary/ssc
./dist/binary/ssc --version
```

The automated smoke test creates temporary credentials and removes them when
it finishes. For a separate interactive demo:

```bash
export SSC_CONFIG_DIR="$(mktemp -d -t ssc-binary-demo.XXXXXX)"
export ENV=development
./dist/binary/ssc demo-seed
./dist/binary/ssc tui
# Or: ./dist/binary/ssc connect demo-web-dev
# Inside the demo shell: scroll 1000; then exit
```

After closing the dashboard and connections, clean up the demo and build output:

```bash
case "$SSC_CONFIG_DIR" in
  /tmp/ssc-binary-demo.*) rm -rf -- "$SSC_CONFIG_DIR" ;;
esac
unset SSC_CONFIG_DIR ENV
rm -rf -- build/pyinstaller dist/binary dist/release
```

Keep `.venv` for normal development; remove it separately if you also want to
remove installed development dependencies. Build on each target architecture;
the local script does not cross-compile.
