@echo off
setlocal

:: 1. Configuration (UPDATE THESE VALUES)
set DROPLET_IP=YOUR_DROPLET_IP_HERE
set DROPLET_USER=root

echo --------------------------------------------------------
echo 🌟 STARTING INITIAL SERVER SETUP...
echo --------------------------------------------------------
echo 🕒 This will take a few minutes to install Nginx, Python, PostgreSQL, etc.
echo --------------------------------------------------------

:: 2. Create scripts directory on server
ssh %DROPLET_USER%@%DROPLET_IP% "mkdir -p /home/islamic-library/scripts"

:: 3. Remote Execute Setup Script
echo 📋 Uploading and running setup_server.sh...
scp scripts/setup_server.sh %DROPLET_USER%@%DROPLET_IP%:/home/islamic-library/scripts/setup_server.sh
ssh %DROPLET_USER%@%DROPLET_IP% "chmod +x /home/islamic-library/scripts/setup_server.sh && /home/islamic-library/scripts/setup_server.sh"

echo --------------------------------------------------------
echo ✅ INITIAL SERVER SETUP COMPLETE!
echo 🌍 Public Link: http://%DROPLET_IP%
echo --------------------------------------------------------
pause
