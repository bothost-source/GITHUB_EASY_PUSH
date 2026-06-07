"""
TARRIFIC HOST BOT - HTTP Header Analyzer
Check security headers on websites
"""
import urllib.request
import urllib.error
import ssl

# Security headers to check
SECURITY_HEADERS = {
    'Strict-Transport-Security': {
        'name': 'HSTS',
        'description': 'Forces HTTPS connections',
        'required': True,
    },
    'Content-Security-Policy': {
        'name': 'CSP',
        'description': 'Prevents XSS and injection attacks',
        'required': True,
    },
    'X-Frame-Options': {
        'name': 'X-Frame-Options',
        'description': 'Prevents clickjacking',
        'required': True,
    },
    'X-Content-Type-Options': {
        'name': 'X-Content-Type-Options',
        'description': 'Prevents MIME sniffing',
        'required': True,
    },
    'Referrer-Policy': {
        'name': 'Referrer-Policy',
        'description': 'Controls referrer info',
        'required': False,
    },
    'Permissions-Policy': {
        'name': 'Permissions-Policy',
        'description': 'Controls browser features',
        'required': False,
    },
    'X-XSS-Protection': {
        'name': 'X-XSS-Protection',
        'description': 'Legacy XSS protection',
        'required': False,
    },
}

def analyze_headers(url):
    """Analyze security headers on URL"""
    url = url.strip()

    if not url.startswith('http'):
        url = 'https://' + url

    try:
        # Create SSL context that allows us to check even with cert issues
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        try:
            response = urllib.request.urlopen(req, timeout=10, context=ctx)
        except:
            # Try GET if HEAD fails
            req = urllib.request.Request(url, method='GET')
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            response = urllib.request.urlopen(req, timeout=10, context=ctx)

        headers = dict(response.headers)

        # Analyze headers
        present = []
        missing = []

        for header, info in SECURITY_HEADERS.items():
            if header in headers:
                present.append((info['name'], info['description'], headers[header]))
            else:
                missing.append((info['name'], info['description'], info['required']))

        # Calculate grade
        required_present = sum(1 for _, _, req in missing if not req) + len(present)
        required_total = len(SECURITY_HEADERS)
        score = len(present) / len(SECURITY_HEADERS)

        if score >= 0.8:
            grade = "A"
        elif score >= 0.6:
            grade = "B"
        elif score >= 0.4:
            grade = "C"
        elif score >= 0.2:
            grade = "D"
        else:
            grade = "F"

        # Build result
        result = f"📡 SECURITY REPORT

"
        result += f"URL: {url}
"
        result += f"Grade: {grade}

"

        result += "✅ PRESENT
"
        for name, desc, value in present:
            result += f"  {name}
"
            result += f"  └─ {value[:60]}{'...' if len(value) > 60 else ''}

"

        result += "❌ MISSING
"
        for name, desc, required in missing:
            marker = "🔴" if required else "🟡"
            result += f"  {marker} {name}
"
            result += f"  └─ {desc}

"

        result += f"Score: {len(present)}/{len(SECURITY_HEADERS)} headers
"
        result += f"Required: {len([m for m in missing if m[2]])} missing

"

        if grade in ['D', 'F']:
            result += "⚠️ Critical headers missing!
"
            result += "Site may be vulnerable to XSS, clickjacking, or MITM."
        elif grade == 'A':
            result += "✅ Good security header coverage!"

        return result

    except urllib.error.HTTPError as e:
        return (
            f"❌ HTTP ERROR

"
            f"URL: {url}
"
            f"Status: {e.code}
"
            f"Message: {e.reason}

"
            "The server returned an error."
        )
    except urllib.error.URLError as e:
        return (
            f"❌ CONNECTION ERROR

"
            f"URL: {url}
"
            f"Error: {str(e.reason)}

"
            "Could not connect to the server."
        )
    except Exception as e:
        return (
            f"❌ ERROR

"
            f"URL: {url}
"
            f"Error: {str(e)}

"
            "Could not analyze headers."
        )
