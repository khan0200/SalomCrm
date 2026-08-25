"""
SSH deployment for SalomCRM.

The server runs the backend as a systemd unit (salomcrm-backend.service)
behind nginx, with the virtualenv at the repo root (NOT inside backend/).
Do not introduce a second process manager here: running gunicorn under pm2
alongside the systemd unit makes both fight over port 8000 and takes the
site down.

Usage:
    python deploy.py             # deploy latest main
    python deploy.py --logs      # tail backend logs
    python deploy.py --status    # service + health check only

Credentials come from the environment, so no password is stored in this file:
    DEPLOY_HOST      (default 178.238.231.210)
    DEPLOY_USER      (default root)
    DEPLOY_PASSWORD  or DEPLOY_KEY (path to a private key)
"""
import os
import sys
import argparse

try:
    import paramiko
except ImportError:
    sys.exit("paramiko is required:  pip install paramiko")

# Server output (systemd's bullet, box drawing, etc.) is UTF-8; the Windows
# console defaults to cp1252 and would raise UnicodeEncodeError on it.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


HOST = os.environ.get("DEPLOY_HOST", "178.238.231.210")
USER = os.environ.get("DEPLOY_USER", "root")
PASSWORD = os.environ.get("DEPLOY_PASSWORD")
KEYFILE = os.environ.get("DEPLOY_KEY")

APP_DIR = os.environ.get("DEPLOY_APP_DIR", "/var/www/SalomCrm")
BRANCH = os.environ.get("DEPLOY_BRANCH", "main")
BACKEND_PORT = "8000"
SERVICE = "salomcrm-backend.service"


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if KEYFILE:
        client.connect(HOST, username=USER, key_filename=KEYFILE, timeout=20,
                       allow_agent=False, look_for_keys=False)
    elif PASSWORD:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=20,
                       allow_agent=False, look_for_keys=False)
    else:
        sys.exit(
            "No credentials found. Set DEPLOY_PASSWORD or DEPLOY_KEY first:\n"
            '    $env:DEPLOY_PASSWORD = "..."   (PowerShell)\n'
            '    export DEPLOY_PASSWORD="..."   (bash)'
        )
    return client


def run(client, command, check=True, label=None, timeout=600):
    """Run a command on the server, streaming its output."""
    if label:
        print("\n=== %s ===" % label)
    print("$ %s" % command)
    stdin, stdout, stderr = client.exec_command(command, get_pty=True, timeout=timeout)
    lines = []
    for line in iter(stdout.readline, ""):
        line = line.rstrip()
        if line:
            print("  %s" % line)
            lines.append(line)
    code = stdout.channel.recv_exit_status()
    err = stderr.read().decode(errors="replace").strip()
    if err:
        print("  [stderr] %s" % err)
    if check and code != 0:
        raise SystemExit("\nFAILED (exit %s): %s" % (code, command))
    return code, "\n".join(lines)


def check_app_dir(client):
    code, _ = run(client, "test -d %s/.git" % APP_DIR, check=False,
                  label="Locating project")
    if code != 0:
        raise SystemExit(
            "No git checkout at %s on %s.\n"
            "Set DEPLOY_APP_DIR if the project lives elsewhere." % (APP_DIR, HOST)
        )
    print("  -> using %s" % APP_DIR)
    return APP_DIR


def health_check(client):
    run(client, "systemctl status %s --no-pager | head -8" % SERVICE,
        check=False, label="Service status")
    cmd = (
        "curl -s -o /dev/null -w 'backend:%{http_code}\\n' http://127.0.0.1:"
        + BACKEND_PORT + "/api/docs/; "
        "curl -s -o /dev/null -w 'site:%{http_code}\\n' http://127.0.0.1/"
    )
    _, out = run(client, cmd, check=False, label="Health check")
    return out


def upload_frontend(client, path):
    """
    Upload the locally built frontend/dist to the server.

    Node is not installed on the server, so the bundle cannot be built there.
    frontend/dist is also gitignored, so `git pull` never brings it across —
    it has to be built locally (npm run build) and copied up, or the site
    keeps serving the previous bundle.
    """
    local_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
    index_html = os.path.join(local_dist, "index.html")
    if not os.path.isfile(index_html):
        raise SystemExit(
            "No local build at %s.\nRun:  cd frontend && npm run build" % local_dist
        )

    print("\n=== Uploading frontend build ===")
    print("  local: %s" % local_dist)

    remote_dist = "%s/frontend/dist" % path
    remote_tmp = "%s/frontend/dist.incoming" % path

    # Stage into a temp dir, then swap, so a failed upload never leaves the
    # site serving a half-written bundle.
    run(client, "rm -rf %s && mkdir -p %s" % (remote_tmp, remote_tmp), check=True)

    sftp = client.open_sftp()
    count = 0
    try:
        for root, _dirs, files in os.walk(local_dist):
            rel = os.path.relpath(root, local_dist).replace("\\", "/")
            remote_dir = remote_tmp if rel == "." else "%s/%s" % (remote_tmp, rel)
            if rel != ".":
                try:
                    sftp.mkdir(remote_dir)
                except IOError:
                    pass
            for name in files:
                sftp.put(os.path.join(root, name), "%s/%s" % (remote_dir, name))
                count += 1
                print("  + %s/%s" % (rel if rel != "." else "", name))
    finally:
        sftp.close()

    run(client,
        "rm -rf %s.old && mv %s %s.old 2>/dev/null; mv %s %s && rm -rf %s.old"
        % (remote_dist, remote_dist, remote_dist, remote_tmp, remote_dist, remote_dist),
        check=True)
    print("  uploaded %d files" % count)


def deploy(client, path):
    run(client, "cd %s && git fetch origin && git reset --hard origin/%s" % (path, BRANCH),
        label="Pulling latest code")
    run(client, "cd %s && git log -1 --oneline" % path)

    # venv lives at the repo root, one level above backend/
    run(client,
        "cd %s/backend && ../venv/bin/pip install -q -r requirements.txt gunicorn" % path,
        label="Backend dependencies")
    run(client, "cd %s/backend && ../venv/bin/python manage.py migrate --noinput" % path,
        label="Database migrations")
    run(client, "cd %s/backend && ../venv/bin/python manage.py collectstatic --noinput" % path,
        label="Collecting static files")

    upload_frontend(client, path)

    run(client, "systemctl restart %s" % SERVICE, label="Restarting backend")

    # nginx here is not managed by systemd (it is started by the hosting
    # panel), so `systemctl reload nginx` fails. Reload via the binary if it
    # is running; a static dist swap does not strictly need it either way.
    run(client,
        "nginx -t >/dev/null 2>&1 && nginx -s reload 2>/dev/null"
        " && echo 'nginx reloaded' || echo 'nginx reload skipped (serves new files anyway)'",
        check=False, label="Reloading nginx")

    run(client, "sleep 4", check=False)
    out = health_check(client)

    if "backend:200" in out.replace(" ", ""):
        print("\nDeploy complete — backend healthy.")
    else:
        print("\nWARNING: backend did not return 200. Inspect with: python deploy.py --logs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", action="store_true", help="tail backend logs")
    parser.add_argument("--status", action="store_true", help="service status + health check only")
    args = parser.parse_args()

    print("Connecting to %s@%s ..." % (USER, HOST))
    client = connect()
    print("Connected.")
    try:
        path = check_app_dir(client)
        if args.logs:
            run(client, "journalctl -u %s -n 80 --no-pager" % SERVICE, check=False)
        elif args.status:
            health_check(client)
        else:
            deploy(client, path)
    finally:
        client.close()


if __name__ == "__main__":
    main()
