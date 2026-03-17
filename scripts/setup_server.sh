#!/bin/bash

# Configuration
DROPLET_IP=$(curl -s ifconfig.me)  # Automatically get the public IP
PROJECT_NAME="islamic-library"
USER_HOME="/home"
PROJECT_DIR="$USER_HOME/$PROJECT_NAME"

echo "🌟 STARTING AUTOMATIC DROPELET SETUP 🌟"

# 1. System Updates & Packages
echo "🔄 Updating system and installing essential packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx postgresql postgresql-contrib curl

# 2. Database Creation (PostgreSQL)
echo "🐘 Creating PostgreSQL Database..."
DB_NAME="islamic_library"
DB_USER="lib_user"
DB_PASSWORD=$(openssl rand -base64 12)

sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# 3. Project Directory Management
echo "📂 Setting up project directory..."
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR
cd $PROJECT_DIR

# 4. Git Connection (Forced Pull)
echo "🔗 Fetching project files from GitHub..."
git init
git remote add origin https://github.com/AbdurrabKhan198/Digital-Library.git 2>/dev/null || true
git fetch origin main
git checkout -f main
git reset --hard origin/main

# 5. Virtual Environment & Requirements
echo "📦 Setting up python environment..."
python3 -m venv venv
source venv/bin/activate
pip install gunicorn psycopg2-binary django-storages boto3 Pillow python-decouple django-cleanup django-ckeditor whitenoise

# 6. Environment Variables (.env)
echo "🔑 Creating .env file..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
cat <<EOF > .env
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DROPLET_IP,baytalhikmahonline.org
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
USE_S3=False
SECURE_SSL_REDIRECT=False
EOF

# 7. Django Initial Setup
echo "🛠️  Preparing Django (Migrate & Static)..."
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# 8. Create Gunicorn Service
echo "🚀 Configuring Gunicorn..."
sudo bash -c "cat <<EOF > /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon for $PROJECT_NAME
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock myproject.wsgi:application

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# 9. Configure Nginx
echo "🌐 Configuring Nginx Reverse Proxy..."
sudo bash -c "cat <<EOF > /etc/nginx/sites-available/$PROJECT_NAME
server {
    listen 80;
    server_name $DROPLET_IP baytalhikmahonline.org;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $PROJECT_DIR;
    }
    location /media/ {
        root $PROJECT_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
EOF"

sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled
sudo nginx -t && sudo systemctl restart nginx

# 10. Final Firewall
echo "🛡️  Configuring Firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

echo "--------------------------------------------------------"
echo "✅ SUCCESS! EVERYTHING IS AUTOMATED."
echo "🌍 Visit: http://$DROPLET_IP"
echo "⚙️  Database Info saved in $PROJECT_DIR/.env"
echo "--------------------------------------------------------"
