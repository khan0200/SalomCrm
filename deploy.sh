#!/usr/bin/env bash
set -e

# ==============================================================================
# Salom CRM - Automated Production Deployment Script
# ==============================================================================

echo "========================================="
echo "🚀 Starting Salom CRM Deployment..."
echo "========================================="

# 1. Check if docker and docker compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# 2. Pull latest git changes if inside a git repository
if [ -d .git ]; then
    echo "📥 Pulling latest code from Git..."
    git pull origin main || echo "⚠️ Git pull warning: continuing with local files..."
fi

# 3. Check for .env file
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "📝 Creating .env from .env.example..."
        cp .env.example .env
    else
        echo "⚠️ Warning: .env file not found. Make sure environment variables are properly set."
    fi
fi

# 4. Build and run containers
echo "🐳 Building and starting Docker containers..."
docker compose down --remove-orphans || true
docker compose up -d --build

# 5. Check container statuses
echo "🔍 Checking container status..."
sleep 3
docker compose ps

echo "========================================="
echo "✅ Salom CRM successfully deployed!"
echo "🌐 Frontend: http://<YOUR_SERVER_IP> or https://crm.salomkorea.uz"
echo "⚙️ Backend API: http://<YOUR_SERVER_IP>:8000/api/"
echo "📚 Swagger Docs: http://<YOUR_SERVER_IP>:8000/api/docs/"
echo "========================================="
