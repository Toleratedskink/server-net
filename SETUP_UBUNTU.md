# Quick Setup Guide for Ubuntu Server VM

## Step-by-Step Instructions

### 1. Transfer files to your VM (if needed)
If you're copying files from your local machine:
```bash
# From your local machine, use scp:
scp -r server-net/ your-username@10.251.152.156:/home/your-username/
```

### 2. SSH into your Ubuntu VM
```bash
ssh your-username@10.251.152.156
```

### 3. Install Python and dependencies
```bash
# Update package list
sudo apt update

# Install Python 3, pip, and venv (if not already installed)
sudo apt install -y python3 python3-pip python3-venv

# Navigate to project directory
cd ~/server-net

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

**Note:** You'll need to activate the virtual environment each time you want to run the app manually:
```bash
source venv/bin/activate
python3 app.py
```

Or if using the systemd service, we'll update the service file to use the virtual environment.

### 4. Test run (optional)
Run it once to make sure everything works:
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the app
python3 app.py
```

You should see output like:
```
Network range: 10.251.152.0/24
Scan complete. Found X devices
```

Press `Ctrl+C` to stop it.

### 5. Set up as a systemd service (recommended)

**Edit the service file:**
```bash
sudo nano /etc/systemd/system/network-monitor.service
```

**Copy and paste this** (replace `YOUR_USERNAME` with your actual username):
```ini
[Unit]
Description=Network Monitor Application
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/server-net
ExecStart=/home/YOUR_USERNAME/server-net/venv/bin/python3 /home/YOUR_USERNAME/server-net/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Note:** This uses the Python from the virtual environment (`venv/bin/python3`), so make sure you've created the venv and installed dependencies first!

**Enable and start the service:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable network-monitor.service

# Start the service
sudo systemctl start network-monitor.service

# Check if it's running
sudo systemctl status network-monitor.service
```

### 6. Configure firewall (if needed)
```bash
# Check if ufw is active
sudo ufw status

# Allow port 5000
sudo ufw allow 5000/tcp

# Reload firewall
sudo ufw reload
```

### 7. Access the application
Open your browser and go to:
```
http://10.251.152.156:5000
```

## Useful Commands

**View logs:**
```bash
sudo journalctl -u network-monitor.service -f
```

**Stop the service:**
```bash
sudo systemctl stop network-monitor.service
```

**Start the service:**
```bash
sudo systemctl start network-monitor.service
```

**Restart the service:**
```bash
sudo systemctl restart network-monitor.service
```

**Disable auto-start on boot:**
```bash
sudo systemctl disable network-monitor.service
```

## Troubleshooting

**If the service fails to start:**
1. Check the logs: `sudo journalctl -u network-monitor.service -n 50`
2. Verify paths in the service file are correct
3. Make sure Python dependencies are installed: `pip3 list | grep -E "Flask|psutil"`
4. Test running manually: `source venv/bin/activate && python3 app.py`

**If you can't access from outside the VM:**

1. **Verify the app is running and listening on 0.0.0.0:**
   ```bash
   # Check if the service is running
   sudo systemctl status network-monitor.service
   
   # Check if port 5000 is listening on all interfaces (0.0.0.0)
   sudo ss -tlnp | grep 5000
   # Should show: 0.0.0.0:5000 or :::5000
   
   # Alternative command
   sudo netstat -tlnp | grep 5000
   ```

2. **Check firewall settings:**
   ```bash
   # Check UFW status
   sudo ufw status
   
   # If UFW is active, allow port 5000
   sudo ufw allow 5000/tcp
   sudo ufw reload
   ```

3. **Test from inside the VM first:**
   ```bash
   # From inside the VM, test localhost
   curl http://localhost:5000
   
   # Or test with the VM's IP
   curl http://10.251.152.156:5000
   ```

4. **Verify the app is configured correctly:**
   - The app should be listening on `0.0.0.0:5000` (already configured in app.py)
   - When you start the app, you should see messages like:
     ```
     Starting server on 0.0.0.0:5000
     Access from outside VM: http://10.251.152.156:5000
     ```

5. **Check VM network configuration:**
   - Make sure the VM's network adapter is in bridge mode (not NAT) if you want external access
   - Verify the VM can reach other devices on the network

6. **Test from your local machine:**
   ```bash
   # From your local machine (outside the VM)
   curl http://10.251.152.156:5000
   # Or open in browser: http://10.251.152.156:5000
   ```

**If network scanning doesn't work:**
- The app may need root privileges for some network operations
- Try running with sudo (not recommended for production, but for testing): `sudo python3 app.py`
- Check network interface permissions

