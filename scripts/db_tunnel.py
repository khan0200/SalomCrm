"""SSH tunnel to the production PostgreSQL (local only).

Postgres on the VPS listens on 127.0.0.1:5432 and is not reachable from outside,
so dev.bat starts this tunnel: 127.0.0.1:15432 (local) -> 127.0.0.1:5432 (VPS).
Credentials come from the git-ignored .env (VPS_HOST, VPS_SSH_USER, VPS_ROOT_PASSWORD).
"""
import os
import socketserver
import sys
import threading
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent.parent
LOCAL_PORT = int(os.environ.get("DB_TUNNEL_PORT", "15432"))
REMOTE = ("127.0.0.1", 5432)


def load_env():
    env = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def connect(env):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        env["VPS_HOST"],
        username=env.get("VPS_SSH_USER", "root"),
        password=env["VPS_ROOT_PASSWORD"],
        timeout=20,
        banner_timeout=30,
    )
    client.get_transport().set_keepalive(20)
    return client


def make_handler(client):
    def forward(source, target):
        try:
            while True:
                data = source.recv(32768)
                if not data:
                    break
                target.sendall(data)
        except (OSError, EOFError):
            pass

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            try:
                chan = client.get_transport().open_channel(
                    "direct-tcpip", REMOTE, self.request.getpeername()
                )
            except Exception as exc:
                print(f"[tunnel] channel failed: {exc}", flush=True)
                return

            client_to_server = threading.Thread(
                target=forward, args=(self.request, chan), daemon=True
            )
            server_to_client = threading.Thread(
                target=forward, args=(chan, self.request), daemon=True
            )
            client_to_server.start()
            server_to_client.start()
            client_to_server.join()
            chan.close()
            self.request.shutdown(2)

    return Handler


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    env = load_env()
    client = connect(env)
    server = Server(("127.0.0.1", LOCAL_PORT), make_handler(client))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[tunnel] 127.0.0.1:{LOCAL_PORT} -> {env['VPS_HOST']}:{REMOTE[1]} ready", flush=True)
    try:
        client.get_transport().join()
    except KeyboardInterrupt:
        pass
    print("[tunnel] closed", flush=True)
    server.shutdown()
    client.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
