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

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the server IP in `app.py` matches your server's IP address (currently set to `10.251.152.130`)

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://10.251.152.130:5000
```

Or if accessing from the server itself:
```
http://localhost:5000
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

