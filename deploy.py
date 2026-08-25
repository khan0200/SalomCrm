"""
SSH + pm2 deployment for SalomCRM.

The backend runs under pm2 as "salomcrm-backend" (gunicorn), behind nginx.
Node/npm/pm2 live in aaPanel's directory and are NOT on the default SSH
PATH, so every remote command is prefixed with NODE_BIN.

IMPORTANT: the backend was previously managed by systemd
(salomcrm-backend.service). systemd and pm2 must never both run gunicorn:
they fight over port 8000 and restart each other in a loop. deploy() stops
and disables the systemd unit before starting pm2.

Do not touch the "salomkorea" pm2 process - that is a different project.

Usage:
    python deploy.py             # deploy latest main
    python deploy.py --logs      # tail backend logs
    python deploy.py --status    # pm2 list + health check only

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

# Server output (pm2 tables, systemd bullets) is UTF-8; the Windows console
# defaults to cp1252 and would raise UnicodeEncodeError on it.
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
PM2_APP = "salomcrm-backend"
SYSTEMD_UNIT = "salomcrm-backend.service"

# aaPanel's Node install - not on the default non-interactive SSH PATH.
NODE_BIN = os.environ.get("DEPLOY_NODE_BIN", "/www/server/nodejs/v24.19.0/bin")
ENV = "export PATH=%s:$PATH; " % NODE_BIN


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


def run(client, command, check=True, label=None, timeout=900, node=False):
    """Run a command on the server, streaming its output."""
    if label:
        print("\n=== %s ===" % label)
    shown = command
    command = (ENV + command) if node else command
    print("$ %s" % shown)
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
        raise SystemExit("\nFAILED (exit %s): %s" % (code, shown))
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


def retire_systemd(client):
    """
    Hand port 8000 over from systemd to pm2.

    Leaving the unit running (or merely enabled) means both managers try to
    bind :8000 and restart each other forever - the failure mode that took
    the site down before.
    """
    code, out = run(client, "systemctl is-active %s" % SYSTEMD_UNIT,
                    check=False, label="Retiring systemd unit")
    if "active" in out and "inactive" not in out:
        run(client, "systemctl stop %s" % SYSTEMD_UNIT, check=False)
        run(client, "systemctl disable %s" % SYSTEMD_UNIT, check=False)
        print("  systemd unit stopped and disabled")
    else:
        run(client, "systemctl disable %s" % SYSTEMD_UNIT, check=False)
        print("  systemd unit already inactive")

    # Make sure no NON-pm2 process is still holding the port. A listener whose
    # ancestor is the PM2 God Daemon is our own app and must be left alone -
    # pm2 restart below handles it. Anything else (a stray systemd gunicorn)
    # would fight pm2 for :8000, so refuse rather than create a restart loop.
    _, holder = run(
        client,
        "pid=$(ss -tlnpH 'sport = :%s' 2>/dev/null | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2); "
        "if [ -z \"$pid\" ]; then echo FREE; "
        "elif pstree -sp \"$pid\" 2>/dev/null | grep -q 'PM2'; then echo PM2-OWNED; "
        "else echo \"FOREIGN:$(ps -o cmd= -p $pid)\"; fi" % BACKEND_PORT,
        check=False, label="Checking port %s" % BACKEND_PORT)

    if "PM2-OWNED" in holder:
        print("  port %s already served by pm2 (will restart in place)" % BACKEND_PORT)
    elif "FREE" in holder:
        print("  port %s is free" % BACKEND_PORT)
    else:
        run(client, "fuser -k %s/tcp 2>/dev/null; sleep 2; true" % BACKEND_PORT, check=False)
        _, again = run(client,
                       "ss -tlnpH 'sport = :%s' 2>/dev/null | grep -q . && echo HELD || echo FREE"
                       % BACKEND_PORT, check=False)
        if "HELD" in again:
            raise SystemExit(
                "Port %s is held by a non-pm2 process that would not stop:\n%s\n"
                "Refusing to start pm2 on an occupied port." % (BACKEND_PORT, holder)
            )
        print("  cleared a foreign listener on port %s" % BACKEND_PORT)


def health_check(client):
    run(client, "pm2 list", check=False, label="pm2 status", node=True)
    cmd = (
        "curl -s -o /dev/null -w 'backend:%{http_code}\\n' http://127.0.0.1:"
        + BACKEND_PORT + "/api/docs/; "
        "curl -s -o /dev/null -w 'site:%{http_code}\\n' http://127.0.0.1/"
    )
    _, out = run(client, cmd, check=False, label="Health check")
    return out


def deploy(client, path):
    run(client, "cd %s && git fetch origin && git reset --hard origin/%s" % (path, BRANCH),
        label="Pulling latest code")
    run(client, "cd %s && git log -1 --oneline | cat" % path)

    # venv lives at the repo root, one level above backend/
    run(client,
        "cd %s/backend && ../venv/bin/pip install -q -r requirements.txt gunicorn" % path,
        label="Backend dependencies")
    run(client, "cd %s/backend && ../venv/bin/python manage.py migrate --noinput" % path,
        label="Database migrations")
    run(client, "cd %s/backend && ../venv/bin/python manage.py collectstatic --noinput" % path,
        label="Collecting static files")

    run(client, "cd %s/frontend && npm ci --no-audit --no-fund" % path,
        label="Frontend dependencies", node=True)
    run(client, "cd %s/frontend && npm run build" % path,
        label="Building frontend", node=True)

    retire_systemd(client)

    code, _ = run(client, "pm2 describe %s > /dev/null 2>&1" % PM2_APP,
                  check=False, node=True)
    if code == 0:
        run(client, "pm2 restart %s --update-env" % PM2_APP,
            label="Restarting backend (pm2)", node=True)
    else:
        run(client,
            "cd %s/backend && pm2 start ../venv/bin/gunicorn --name %s --interpreter none "
            "-- config.wsgi:application --bind 127.0.0.1:%s --workers 3 --timeout 120"
            % (path, PM2_APP, BACKEND_PORT),
            label="Starting backend (pm2)", node=True)

    run(client, "pm2 save", check=False, node=True)

    # nginx here is started by the hosting panel, not systemd, so
    # `systemctl reload nginx` fails even though nginx is serving fine.
    run(client,
        "nginx -t >/dev/null 2>&1 && nginx -s reload 2>/dev/null"
        " && echo 'nginx reloaded' || echo 'nginx reload skipped (serves new files anyway)'",
        check=False, label="Reloading nginx")

    run(client, "sleep 5", check=False)
    out = health_check(client)

    if "backend:200" in out.replace(" ", ""):
        print("\nDeploy complete - backend healthy under pm2.")
    else:
        print("\nWARNING: backend did not return 200. Inspect with: python deploy.py --logs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", action="store_true", help="tail backend logs")
    parser.add_argument("--status", action="store_true", help="pm2 list + health check only")
    args = parser.parse_args()

    print("Connecting to %s@%s ..." % (USER, HOST))
    client = connect()
    print("Connected.")
    try:
        path = check_app_dir(client)
        if args.logs:
            run(client, "pm2 logs %s --lines 80 --nostream" % PM2_APP,
                check=False, node=True)
        elif args.status:
            health_check(client)
        else:
            deploy(client, path)
    finally:
        client.close()


if __name__ == "__main__":
    main()
