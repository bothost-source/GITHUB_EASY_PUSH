"""
TARRIFIC HOST BOT - Port Scanner
Scan common ports on target
"""
import socket
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Common ports and services
COMMON_PORTS = {
    21: 'FTP',
    22: 'SSH',
    23: 'Telnet',
    25: 'SMTP',
    53: 'DNS',
    80: 'HTTP',
    110: 'POP3',
    143: 'IMAP',
    443: 'HTTPS',
    3306: 'MySQL',
    3389: 'RDP',
    5432: 'PostgreSQL',
    5900: 'VNC',
    8080: 'HTTP-Alt',
    8443: 'HTTPS-Alt',
}

def scan_port(host, port):
    """Scan a single port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return port, result == 0
    except:
        return port, False

def scan_ports(target):
    """Scan common ports on target"""
    target = target.strip()

    if not target:
        return "❌ No target specified"

    # Resolve hostname if needed
    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        return (
            f"❌ HOST NOT FOUND

"
            f"Could not resolve: {target}
"
            "Check the domain or IP address."
        )

    # Scan ports
    open_ports = []
    closed_ports = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scan_port, ip, port): port for port in COMMON_PORTS.keys()}
        for future in futures:
            port, is_open = future.result()
            if is_open:
                open_ports.append(port)
            else:
                closed_ports.append(port)

    # Build result
    result = f"🔌 SCAN RESULTS

"
    result += f"Target: {target}
"
    result += f"IP: {ip}

"

    result += "PORT     STATUS   SERVICE
"
    result += "─────────────────────────
"

    for port in sorted(COMMON_PORTS.keys()):
        service = COMMON_PORTS[port]
        if port in open_ports:
            status = "🟢 Open"
        else:
            status = "🔴 Closed"
        result += f"{port:<8} {status:<8} {service}
"

    result += f"
{len(open_ports)} open | {len(closed_ports)} closed
"
    result += f"Scan time: ~{len(COMMON_PORTS) * 2}s

"

    if open_ports:
        result += "⚠️ Security note: Open ports may be vulnerable.
"
        result += "Only scan targets you own or have permission to scan."

    return result
