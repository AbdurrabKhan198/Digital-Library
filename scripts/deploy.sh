#!/bin/bash

# Configuration
PROJECT_DIR="/home/islamic-library"
REPO_URL="https://github.com/AbdurrabKhan198/Digital-Library.git"

echo "🚀 Starting Deployment on DigitalOcean Droplet..."

# 1. Update/Clone Project
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📂 Cloning repository for the first time..."
    git clone $REPO_URL $PROJECT_DIR
    cd $PROJECT_DIR
else
    echo "🔄 Pulling latest changes from GitHub..."
    cd $PROJECT_DIR
    git pull origin main
fi

# 2. Virtual Environment Setup
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Install/Update Packages
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Database & Static Files
echo "🏗️  Running migrations..."
python manage.py migrate --noinput
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# 5. Check Gunicorn Service
SERVICE_FILE="/etc/systemd/system/gunicorn.service"
if [ ! -f "$SERVICE_FILE" ]; then
    echo "⚠️  Gunicorn service not found. Make sure to run the initial setup script first!"
else
    echo "🔄 Restarting Gunicorn..."
    sudo systemctl restart gunicorn
    sudo systemctl enable gunicorn
fi

# 6. Check Nginx
echo "🌐 Reloading Nginx..."
sudo systemctl reload nginx

echo "✅ DEPLOYMENT COMPLETE! Your site should be live at your server's IP."
