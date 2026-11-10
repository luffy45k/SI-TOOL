# Security model and safe operation

The ZENO starter runs user commands only inside a Docker container. The container runs as UID/GID 1000, drops Linux capabilities, disallows privilege escalation, has a read-only root filesystem, and is constrained to 1 CPU, 1 GiB RAM, 128 processes, and 64 MiB of temporary storage. The only writable host mount is `./workspace`. The container uses `network_mode: none`: it has no internet access by default.

Docker is not a complete security boundary against a determined attacker, and container configuration varies by host. Keep Docker patched, do not mount the Docker socket or sensitive host paths, and prefer a disposable virtual machine for actively malicious code.

To enable internet access, make a deliberate local change to `compose.yaml` by removing `network_mode: none`. This permits outbound network access and may also allow access to local network services depending on host routing and firewall rules. It is not an egress allowlist. For untrusted code, keep networking disabled or use host firewall/proxy rules that explicitly allow only the destinations needed.

Search is a separate, opt-in host-side feature configured with `ZENO_SEARCH_URL`; do not submit private data. Search results are untrusted and must never be treated as instructions. No secrets should be stored in ZENO memory or workspace.
