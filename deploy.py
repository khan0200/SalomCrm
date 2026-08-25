"""
SSH + pm2 deployment for SalomCRM (no Docker).

Usage:
    python deploy.py             # deploy latest main
    python deploy.py --setup     # first run: install system deps, pm2, nginx
    python deploy.py --logs      # tail backend logs

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


HOST = os.environ.get("DEPLOY_HOST", "178.238.231.210")
USER = os.environ.get("DEPLOY_USER", "root")
PASSWORD = os.environ.get("DEPLOY_PASSWORD")
KEYFILE = os.environ.get("DEPLOY_KEY")

APP_DIR = os.environ.get("DEPLOY_APP_DIR", "/root/SalomCrm")
BRANCH = os.environ.get("DEPLOY_BRANCH", "main")
BACKEND_PORT = "8000"
PM2_BACKEND = "salomcrm-backend"


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if KEYFILE:
        client.connect(HOST, username=USER, key_filename=KEYFILE, timeout=20)
    elif PASSWORD:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=20)
    else:
        sys.exit(
            "No credentials found. Set DEPLOY_PASSWORD or DEPLOY_KEY first:\n"
            '    $env:DEPLOY_PASSWORD = "..."   (PowerShell)\n'
            '    export DEPLOY_PASSWORD="..."   (bash)'
        )
    return client


def run(client, command, check=True, label=None):
    """Run a command on the server, streaming its output."""
    if label:
        print("\n=== %s ===" % label)
    print("$ %s" % command)
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
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


def find_app_dir(client):
    finder = (
        'test -d %s/.git && echo %s || '
        'find /root /var/www /home /opt -maxdepth 3 -name ".git" -type d 2>/dev/null '
        '| grep -i salom | head -1 | xargs -r dirname'
    ) % (APP_DIR, APP_DIR)
    code, out = run(client, finder, check=False, label="Locating project")
    path = out.strip().splitlines()[-1].strip() if out.strip() else ""
    if not path:
        raise SystemExit(
            "Project not found on %s. Clone it first:\n"
            "  git clone https://github.com/khan0200/SalomCrm.git %s" % (HOST, APP_DIR)
        )
    print("  -> using %s" % path)
    return path


NGINX_TEMPLATE = """server {
    listen 80;
    server_name _;
    client_max_body_size 25M;

    root APP_PATH/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:PORT;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:PORT;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias APP_PATH/backend/staticfiles/;
    }

    location /media/ {
        alias APP_PATH/backend/media/;
    }
}
"""


def setup(client, path):
    """One-time provisioning: system packages, Node, pm2, nginx."""
    run(client, "apt-get update -qq", label="System packages")
    run(client,
        "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "
        "python3-venv python3-pip libpq-dev gcc nginx curl git")

    if run(client, "command -v node", check=False)[0] != 0:
        run(client,
            "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - "
            "&& apt-get install -y -qq nodejs",
            label="Installing Node 20")

    if run(client, "command -v pm2", check=False)[0] != 0:
        run(client, "npm install -g pm2", label="Installing pm2")

    conf = NGINX_TEMPLATE.replace("APP_PATH", path).replace("PORT", BACKEND_PORT)
    run(client,
        "cat > /etc/nginx/sites-available/salomcrm <<'NGINXCONF'\n%sNGINXCONF" % conf,
        label="Writing nginx config")
    run(client,
        "ln -sf /etc/nginx/sites-available/salomcrm /etc/nginx/sites-enabled/salomcrm "
        "&& rm -f /etc/nginx/sites-enabled/default && nginx -t && systemctl reload nginx")
    print("\nProvisioning complete.")


def deploy(client, path):
    run(client, "cd %s && git fetch origin && git reset --hard origin/%s" % (path, BRANCH),
        label="Pulling latest code")
    run(client, "cd %s && git log -1 --oneline" % path)

    run(client,
        "cd %s/backend && (test -d venv || python3 -m venv venv) && "
        "./venv/bin/pip install -q --upgrade pip && "
        "./venv/bin/pip install -q -r requirements.txt gunicorn" % path,
        label="Backend dependencies")
    run(client, "cd %s/backend && ./venv/bin/python manage.py migrate --noinput" % path,
        label="Database migrations")
    run(client, "cd %s/backend && ./venv/bin/python manage.py collectstatic --noinput" % path,
        label="Collecting static files")

    run(client, "cd %s/frontend && npm ci --silent" % path, label="Frontend dependencies")
    run(client, "cd %s/frontend && npm run build" % path, label="Building frontend")

    if run(client, "pm2 describe %s > /dev/null 2>&1" % PM2_BACKEND, check=False)[0] == 0:
        run(client, "pm2 restart %s --update-env" % PM2_BACKEND, label="Restarting backend")
    else:
        run(client,
            "cd %s/backend && pm2 start ./venv/bin/gunicorn --name %s --interpreter none "
            "-- config.wsgi:application --bind 127.0.0.1:%s --workers 3 --timeout 120"
            % (path, PM2_BACKEND, BACKEND_PORT),
            label="Starting backend under pm2")

    run(client, "pm2 save", check=False)
    run(client, "systemctl reload nginx", check=False, label="Reloading nginx")

    run(client, "pm2 list", check=False, label="Status")
    code, out = run(client,
        "sleep 3; curl -s -o /dev/null -w '%%{http_code}' http://127.0.0.1:%s/api/docs/" % BACKEND_PORT,
        check=False, label="Health check")
    status = out.strip().splitlines()[-1].strip() if out.strip() else "?"
    if status.startswith(("2", "3")):
        print("\n  Backend healthy (HTTP %s)." % status)
    else:
        print("\n  WARNING: health check returned '%s'. Inspect with: python deploy.py --logs" % status)
    print("\nDeploy complete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true", help="provision the server (first run)")
    parser.add_argument("--logs", action="store_true", help="tail backend logs")
    args = parser.parse_args()

    print("Connecting to %s@%s ..." % (USER, HOST))
    client = connect()
    print("Connected.")
    try:
        path = find_app_dir(client)
        if args.logs:
            run(client, "pm2 logs %s --lines 80 --nostream" % PM2_BACKEND, check=False)
        else:
            if args.setup:
                setup(client, path)
            deploy(client, path)
    finally:
        client.close()


if __name__ == "__main__":
    main()
