@echo off
setlocal

:: 1. Configuration (UPDATE THESE VALUES)
set DROPLET_IP=159.65.151.229
set DROPLET_USER=root
set PROJECT_DIR=/home/islamic-library

echo --------------------------------------------------------
echo 🚀 AUTOMATIC ONE-CLICK DEPLOYMENT STARTED...
echo --------------------------------------------------------

:: 2. Push latest changes to GitHub
echo ➕ Adding and committing local changes...
git add .
git commit -m "Auto-deploy: Update for server"
echo 📤 Pushing to GitHub...
git push origin main

:: 3. Connect to Droplet and Deploy
echo 🔌 Connecting to DigitalOcean Droplet via SSH...
ssh %DROPLET_USER%@%DROPLET_IP% "cd %PROJECT_DIR% && chmod +x scripts/deploy.sh && ./scripts/deploy.sh"

echo --------------------------------------------------------
echo ✅ DONE! Your website is updated on the Droplet.
echo 🌍 Public Link: http://%DROPLET_IP%
echo --------------------------------------------------------
pause
