"""
TARRIFIC HOST BOT - WHOIS & DNS Tools
WHOIS lookup, DNS records, subdomain finder
"""
import socket
import subprocess
import json

def whois_lookup(domain):
    """Perform WHOIS lookup"""
    domain = domain.strip().lower()

    # Remove protocol if present
    domain = domain.replace('https://', '').replace('http://', '').split('/')[0]

    try:
        # Try using whois command if available
        result = subprocess.run(
            ['whois', domain],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            output = result.stdout

            # Extract key info
            lines = output.split('
')
            info = {}

            for line in lines:
                if ':' in line and not line.startswith('%'):
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        if key not in info:
                            info[key] = []
                        info[key].append(value)

            # Build result
            result_text = f"🌍 WHOIS: {domain}

"

            important_keys = [
                'Domain Name', 'Registrar', 'Creation Date', 'Expiration Date',
                'Updated Date', 'Name Server', 'Registrant Name', 'Registrant Email',
                'Status'
            ]

            for key in important_keys:
                if key in info:
                    values = info[key][:3]  # Limit to 3 values
                    result_text += f"{key}:
"
                    for v in values:
                        result_text += f"  {v}
"
                    result_text += "
"

            if not info:
                result_text += "Raw output (parsed):
"
                result_text += output[:1000]

            return result_text
        else:
            return (
                f"❌ WHOIS FAILED

"
                f"Domain: {domain}
"
                f"Error: {result.stderr[:200]}

"
                "WHOIS command not available or domain not found."
            )

    except FileNotFoundError:
        # whois command not available, use basic info
        return basic_domain_info(domain)
    except Exception as e:
        return (
            f"❌ WHOIS ERROR

"
            f"Domain: {domain}
"
            f"Error: {str(e)}

"
            "Could not perform WHOIS lookup."
        )

def basic_domain_info(domain):
    """Get basic domain info without whois command"""
    try:
        ip = socket.gethostbyname(domain)
        return (
            f"🌍 DOMAIN INFO: {domain}

"
            f"IP Address: {ip}

"
            "⚠️ WHOIS command not available on server.
"
            "Install whois for full details.

"
            "Use DNS Lookup for more info."
        )
    except:
        return (
            f"❌ DOMAIN NOT FOUND

"
            f"Could not resolve: {domain}
"
            "Check the domain name."
        )

def dns_lookup(domain):
    """Lookup DNS records"""
    domain = domain.strip().lower()
    domain = domain.replace('https://', '').replace('http://', '').split('/')[0]

    result = f"🌍 DNS RECORDS: {domain}

"

    # A record
    try:
        ip = socket.gethostbyname(domain)
        result += f"A Record:
  {ip}

"
    except:
        result += "A Record:
  Not found

"

    # Try to get more records using nslookup/dig
    record_types = ['MX', 'NS', 'TXT']

    for record_type in record_types:
        try:
            if record_type == 'MX':
                import dns.resolver
                answers = dns.resolver.resolve(domain, 'MX')
                result += f"{record_type} Records:
"
                for rdata in answers:
                    result += f"  {rdata.exchange} (priority: {rdata.preference})
"
                result += "
"
        except:
            try:
                # Fallback using socket
                if record_type == 'NS':
                    result += f"{record_type} Records:
"
                    result += "  (Requires dns.resolver module)

"
                else:
                    result += f"{record_type} Records:
"
                    result += "  (Requires dns.resolver module)

"
            except:
                result += f"{record_type} Records:
  Error

"

    result += "
⚠️ For full DNS records, install dnspython:
"
    result += "pip install dnspython"

    return result

def find_subdomains(domain):
    """Find common subdomains"""
    domain = domain.strip().lower()
    domain = domain.replace('https://', '').replace('http://', '').split('/')[0]

    # Common subdomains to check
    common_subs = [
        'www', 'mail', 'ftp', 'admin', 'api', 'blog', 'shop',
        'dev', 'test', 'staging', 'app', 'mobile', 'cdn',
        'secure', 'vpn', 'remote', 'webmail', 'portal',
        'support', 'help', 'docs', 'wiki', 'git', 'jenkins'
    ]

    result = f"🌍 SUBDOMAIN FINDER: {domain}

"
    result += "Checking common subdomains...

"

    found = []

    for sub in common_subs:
        subdomain = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(subdomain)
            found.append((subdomain, ip))
        except:
            pass

    if found:
        result += f"✅ FOUND ({len(found)}):

"
        for sub, ip in found:
            result += f"  {sub}
"
            result += f"  └─ {ip}

"
    else:
        result += "❌ No common subdomains found.

"
        result += "This could mean:
"
        result += "• Subdomains use non-standard names
"
        result += "• DNS doesn't resolve them
"
        result += "• Domain has no subdomains

"

    result += "⚠️ This checks only common subdomains.
"
    result += "For comprehensive scanning, use specialized tools."

    return result
