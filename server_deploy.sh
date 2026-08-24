#!/usr/bin/env bash
set -e

# ==============================================================================
# Salom CRM - Production Server Deployment Script
# Path: /var/www/SalomCrm
# ==============================================================================

echo "========================================="
echo "🚀 Deploying Salom CRM to Production..."
echo "========================================="

PROJECT_DIR="/var/www/SalomCrm"
cd "$PROJECT_DIR"

# 1. Pull latest code from GitHub
echo "📥 Pulling latest changes from main branch..."
git fetch origin main
git reset --hard origin/main

# 2. Update Python dependencies & Database migrations
echo "🐍 Updating Backend..."
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    pip install -r backend/requirements.txt --quiet
    python backend/manage.py migrate --noinput
    python backend/manage.py collectstatic --noinput
else
    echo "⚠️ venv not found at $PROJECT_DIR/venv. Using system python3..."
    python3 backend/manage.py migrate --noinput
    python3 backend/manage.py collectstatic --noinput
fi

# 3. Build Frontend
echo "⚛️ Building Frontend..."
cd "$PROJECT_DIR/frontend"
npm install --silent
npm run build
cd "$PROJECT_DIR"

# 4. Restart Backend & Reload Nginx
echo "🔄 Restarting Backend Service (PM2)..."
if command -v pm2 &> /dev/null; then
    pm2 restart salomcrm-backend || pm2 start ecosystem.config.js
    pm2 save
fi

echo "🌐 Reloading Nginx..."
if command -v systemctl &> /dev/null; then
    systemctl reload nginx || systemctl restart nginx
fi

echo "========================================="
echo "✅ Deployment completed successfully!"
echo "🌐 URL: https://crm.salomkorea.uz or http://178.238.231.210"
echo "========================================="
