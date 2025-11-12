# Network Monitor

A real-time network monitoring application that visualizes devices connected to your network. The application displays the network topology with the host server in the center and connected devices arranged around it, with activity indicators showing active transmission/reception.

## Features

- 🔍 Automatic network scanning every 5 seconds
- 📊 Real-time network topology visualization
- 💡 Activity indicators showing active network traffic
- 🎨 Modern, clean UI with gradient backgrounds and animations
- 📱 Responsive design

## Requirements

- Python 3.7+
- Network access to scan the local network
- Administrator/root privileges may be required for network scanning (depending on OS)

## Installation (Ubuntu Server)

1. **Update system packages:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip
```

2. **Navigate to the project directory:**
```bash
cd /path/to/server-net
```

3. **Install Python dependencies:**
```bash
pip3 install -r requirements.txt
```

   Or if you prefer to install for the current user only:
```bash
pip3 install --user -r requirements.txt
```

4. **Make sure the server IP in `app.py` matches your server's IP address** (currently set to `10.251.152.156`)

## Running the Application

### Option 1: Run directly in terminal

1. **Start the Flask server:**
```bash
python3 app.py
```

2. **Access from your browser:**
```
http://10.251.152.156:5000
```

   Or from the server itself:
```
http://localhost:5000
```

   The application will keep running until you press `Ctrl+C`.

### Option 2: Run as a background service (Recommended)

1. **Create a systemd service file:**
```bash
sudo nano /etc/systemd/system/network-monitor.service
```

2. **Add the following content** (adjust paths as needed):
```ini
[Unit]
Description=Network Monitor Application
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/server-net
ExecStart=/usr/bin/python3 /path/to/server-net/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **Replace placeholders:**
   - `your-username` with your Ubuntu username
   - `/path/to/server-net` with the actual path to your project

4. **Enable and start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable network-monitor.service
sudo systemctl start network-monitor.service
```

5. **Check service status:**
```bash
sudo systemctl status network-monitor.service
```

6. **View logs:**
```bash
sudo journalctl -u network-monitor.service -f
```

### Option 3: Run in screen/tmux session

1. **Install screen (if not already installed):**
```bash
sudo apt install screen
```

2. **Start a screen session:**
```bash
screen -S network-monitor
```

3. **Run the application:**
```bash
python3 app.py
```

4. **Detach from screen:** Press `Ctrl+A` then `D`

5. **Reattach later:**
```bash
screen -r network-monitor
```

## Firewall Configuration

If you can't access the application from outside the VM, you may need to open port 5000:

```bash
sudo ufw allow 5000/tcp
sudo ufw reload
```

Or if using iptables:
```bash
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

## How It Works

- The application automatically detects the network range from the server IP
- It scans the network using ping to detect active devices
- Network activity is monitored through ARP table and network interface statistics
- The frontend updates every 2 seconds to show the latest network state
- Devices are positioned in a circular pattern around the host
- Green activity indicators pulse when devices are actively transmitting/receiving

## Network Configuration

The server IP is configured in `app.py` as `SERVER_IP = "10.251.152.130"`. The application will automatically determine the network range (typically /24) from this IP.

## Security Note

This application requires network scanning capabilities. On some systems, you may need to run with elevated privileges. Be aware of your network's security policies when deploying this application.

