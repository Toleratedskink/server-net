from flask import Flask, render_template, jsonify
from flask_cors import CORS
import subprocess
import socket
import ipaddress
import psutil
import threading
import time
import platform
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Server IP configuration
# You can set this manually, or leave as None to auto-detect
CONFIGURED_SERVER_IP = "10.251.152.130"  # Server and VM IP

def get_server_ip():
    """Get the server IP - use configured value or auto-detect"""
    if CONFIGURED_SERVER_IP:
        # Verify the configured IP exists on this system
        interfaces = psutil.net_if_addrs()
        for interface_name, addrs in interfaces.items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address == CONFIGURED_SERVER_IP:
                    return CONFIGURED_SERVER_IP
        
        # If configured IP not found, auto-detect
        print(f"Warning: Configured IP {CONFIGURED_SERVER_IP} not found on this system. Auto-detecting...")
    
    # Auto-detect: get the first non-loopback IPv4 address
    interfaces = psutil.net_if_addrs()
    for interface_name, addrs in interfaces.items():
        # Skip loopback and docker interfaces
        if 'lo' in interface_name.lower() or 'docker' in interface_name.lower():
            continue
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip = addr.address
                # Skip localhost and link-local addresses
                if not ip.startswith('127.') and not ip.startswith('169.254.'):
                    print(f"Auto-detected server IP: {ip}")
                    return ip
    
    # Fallback to configured IP or localhost
    return CONFIGURED_SERVER_IP or "127.0.0.1"

# Get the actual server IP
SERVER_IP = get_server_ip()

# Network information
network_info = {
    'host_ip': SERVER_IP,
    'network_range': None,
    'devices': {},
    'last_scan': None
}

# Activity tracking
device_activity = defaultdict(lambda: {'tx_bytes': 0, 'rx_bytes': 0, 'last_update': time.time()})

def get_network_range(ip):
    """Determine the network range from the server IP"""
    try:
        # Get network interface information
        interfaces = psutil.net_if_addrs()
        for interface_name, addrs in interfaces.items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address == ip:
                    # Try to get netmask from the interface
                    if netmask := addr.netmask:
                        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                        return str(network)
        
        # Fallback: assume /24 network
        network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
        return str(network)
    except Exception as e:
        print(f"Error determining network range: {e}")
        # Default to /24
        return f"{ip}/24"

def get_arp_table():
    """Get ARP table to find active devices"""
    arp_table = {}
    try:
        arp_output = subprocess.check_output(['arp', '-a'], timeout=2).decode('utf-8')
        for line in arp_output.split('\n'):
            if '(' in line and ')' in line:
                try:
                    parts = line.split()
                    ip = parts[1].strip('()')
                    # Validate IP is in our network range
                    try:
                        ipaddress.IPv4Address(ip)
                        arp_table[ip] = True
                    except:
                        pass
                except:
                    pass
    except Exception as e:
        print(f"Error reading ARP table: {e}")
    return arp_table

def scan_network(network_range):
    """Scan the network for active devices"""
    devices = {}
    network = ipaddress.IPv4Network(network_range, strict=False)
    
    # Add host device first
    devices[SERVER_IP] = {
        'ip': SERVER_IP,
        'hostname': socket.gethostname(),
        'is_host': True,
        'status': 'online',
        'last_seen': time.time()
    }
    
    # Method 1: Check ARP table first (most reliable, no ping needed)
    print("Checking ARP table...")
    arp_table = get_arp_table()
    arp_count = 0
    for ip in arp_table:
        if ip != SERVER_IP and ipaddress.IPv4Address(ip) in network:
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = ip
            devices[ip] = {
                'ip': ip,
                'hostname': hostname,
                'is_host': False,
                'status': 'online',
                'last_seen': time.time()
            }
            arp_count += 1
    print(f"Found {arp_count} device(s) in ARP table")
    
    # Method 2: Quick ping scan for additional devices (faster timeout)
    print("Scanning network with ping (this may take a while)...")
    ping_found = 0
    total_ips = len(list(network.hosts()))
    scanned = 0
    
    for ip in network.hosts():
        ip_str = str(ip)
        scanned += 1
        
        # Skip if already found in ARP or is host
        if ip_str in devices or ip_str == SERVER_IP:
            continue
        
        # Quick ping with shorter timeout
        try:
            ping_cmd = ['ping', '-c', '1']
            if platform.system() == 'Darwin':  # macOS
                ping_cmd.extend(['-W', '500'])  # 500ms timeout
            else:  # Linux
                ping_cmd.extend(['-w', '1'])  # 1 second timeout
            ping_cmd.append(ip_str)
            
            result = subprocess.run(
                ping_cmd,
                capture_output=True,
                timeout=2,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                try:
                    hostname = socket.gethostbyaddr(ip_str)[0]
                except:
                    hostname = ip_str
                
                devices[ip_str] = {
                    'ip': ip_str,
                    'hostname': hostname,
                    'is_host': False,
                    'status': 'online',
                    'last_seen': time.time()
                }
                ping_found += 1
                print(f"  Found device: {ip_str} ({hostname})")
        except:
            pass
        
        # Progress indicator every 50 IPs
        if scanned % 50 == 0:
            print(f"  Scanned {scanned}/{total_ips} IPs...")
    
    print(f"Ping scan found {ping_found} additional device(s)")
    return devices

def monitor_network_activity():
    """Monitor network activity for each device"""
    global device_activity
    
    # Store previous network stats to detect changes
    prev_net_io = {}
    
    while True:
        try:
            # Get current network I/O statistics
            net_io = psutil.net_io_counters(pernic=True)
            
            # Get ARP table to map IPs to MAC addresses
            try:
                arp_output = subprocess.check_output(['arp', '-a'], timeout=2).decode('utf-8')
            except:
                arp_output = ""
            
            # Parse ARP table
            arp_table = {}
            for line in arp_output.split('\n'):
                if '(' in line and ')' in line:
                    try:
                        parts = line.split()
                        ip = parts[1].strip('()')
                        mac = parts[3] if len(parts) > 3 else None
                        arp_table[ip] = mac
                    except:
                        pass
            
            # Check for network activity by comparing current vs previous stats
            current_time = time.time()
            for interface, stats in net_io.items():
                if interface in prev_net_io:
                    prev_stats = prev_net_io[interface]
                    # Check if there's been traffic
                    tx_diff = stats.bytes_sent - prev_stats['bytes_sent']
                    rx_diff = stats.bytes_recv - prev_stats['bytes_recv']
                    
                    # If there's significant traffic, mark devices in ARP as active
                    if tx_diff > 100 or rx_diff > 100:  # At least 100 bytes change
                        for ip in arp_table:
                            if ip in network_info.get('devices', {}):
                                if ip not in device_activity:
                                    device_activity[ip] = {'tx_bytes': 0, 'rx_bytes': 0, 'last_update': current_time}
                                device_activity[ip]['last_update'] = current_time
                                device_activity[ip]['tx_bytes'] += tx_diff
                                device_activity[ip]['rx_bytes'] += rx_diff
                
                prev_net_io[interface] = {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv
                }
            
            # Also mark devices in ARP table as recently seen (even without traffic change)
            for ip in arp_table:
                if ip in network_info.get('devices', {}):
                    if ip not in device_activity:
                        device_activity[ip] = {'tx_bytes': 0, 'rx_bytes': 0, 'last_update': current_time}
                    # Update last seen time if it's been a while
                    if current_time - device_activity[ip]['last_update'] > 5:
                        device_activity[ip]['last_update'] = current_time
            
            time.sleep(1)
        except Exception as e:
            print(f"Error monitoring activity: {e}")
            time.sleep(1)

def scan_network_periodically():
    """Periodically scan the network"""
    global network_info
    
    # Initialize network range
    if network_info['network_range'] is None:
        network_info['network_range'] = get_network_range(SERVER_IP)
        print(f"Server IP: {SERVER_IP}")
        print(f"Network range: {network_info['network_range']}")
        print(f"Will scan {len(list(ipaddress.IPv4Network(network_info['network_range'], strict=False).hosts()))} IP addresses")
    
    while True:
        try:
            print("\n" + "="*50)
            print("Starting network scan...")
            devices = scan_network(network_info['network_range'])
            network_info['devices'] = devices
            network_info['last_scan'] = time.time()
            device_count = len([d for d in devices.values() if not d.get('is_host', False)])
            print(f"\nScan complete. Found {device_count} device(s) (plus host)")
            if device_count > 0:
                print("Devices found:")
                for ip, device in devices.items():
                    if not device.get('is_host', False):
                        print(f"  - {device['ip']} ({device['hostname']})")
            print("="*50)
        except Exception as e:
            print(f"Error scanning network: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(10)  # Scan every 10 seconds (increased since ARP is fast)

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/network')
def get_network():
    """API endpoint to get network information"""
    # Check activity status for each device
    current_time = time.time()
    for ip, device_info in network_info['devices'].items():
        if ip in device_activity:
            last_update = device_activity[ip]['last_update']
            # Consider device active if updated in last 3 seconds
            device_info['is_active'] = (current_time - last_update) < 3
        else:
            device_info['is_active'] = False
    
    return jsonify({
        'host_ip': network_info['host_ip'],
        'network_range': network_info['network_range'],
        'devices': network_info['devices'],
        'last_scan': network_info['last_scan']
    })

if __name__ == '__main__':
    # Start background threads
    scan_thread = threading.Thread(target=scan_network_periodically, daemon=True)
    activity_thread = threading.Thread(target=monitor_network_activity, daemon=True)
    
    scan_thread.start()
    activity_thread.start()
    
    # Give threads a moment to initialize
    time.sleep(1)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)

