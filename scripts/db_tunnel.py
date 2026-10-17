"""SSH tunnel to the production PostgreSQL (local only).

Postgres on the VPS listens on 127.0.0.1:5432 and is not reachable from outside,
so dev.bat starts this tunnel: 127.0.0.1:15432 (local) -> 127.0.0.1:5432 (VPS).
Credentials come from the git-ignored .env (VPS_HOST, VPS_SSH_USER, VPS_ROOT_PASSWORD).
"""
import os
import select
import socketserver
import sys
import threading
import time
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
    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            try:
                chan = client.get_transport().open_channel(
                    "direct-tcpip", REMOTE, self.request.getpeername()
                )
            except Exception as exc:
                print(f"[tunnel] channel failed: {exc}", flush=True)
                return
            while True:
                ready, _, _ = select.select([self.request, chan], [], [])
                if self.request in ready:
                    data = self.request.recv(32768)
                    if not data:
                        break
                    chan.sendall(data)
                if chan in ready:
                    data = chan.recv(32768)
                    if not data:
                        break
                    self.request.sendall(data)
            chan.close()

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
        while client.get_transport().is_active():
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    print("[tunnel] closed", flush=True)
    server.shutdown()
    client.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
