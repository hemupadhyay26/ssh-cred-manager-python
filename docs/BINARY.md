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


## Automated builds

GitHub Actions builds and tests Linux AMD64 and ARM64 binaries on pull requests.
Publishing a release runs the same builds from the release tag and attaches
verified archives and checksums. The tag must match the package version.
There is no separate local build setup.
