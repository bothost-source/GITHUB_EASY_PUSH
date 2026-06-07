"""
TARRIFIC HOST BOT - Breach Checker
Check email against Have I Been Pwned
"""
import urllib.request
import urllib.error
import json

def check_breach(email):
    """Check if email has been in data breaches"""
    email = email.strip().lower()

    # Basic email validation
    if '@' not in email or '.' not in email.split('@')[-1]:
        return (
            "❌ INVALID EMAIL

"
            f"Input: {email}

"
            "Please provide a valid email address."
        )

    try:
        # Have I Been Pwned API
        # Note: This requires an API key in production
        # For demo, we'll show the structure

        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"

        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'TarrificHostBot')
        req.add_header('hibp-api-key', 'YOUR_API_KEY')  # Replace with actual key

        try:
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read().decode())

            # Build result
            result = f"📧 BREACH RESULTS

"
            result += f"Email: {email}

"
            result += f"🔴 Found in {len(data)} breach(es):

"

            for breach in data[:5]:  # Show top 5
                result += f"1. {breach.get('Name', 'Unknown')}
"
                result += f"   Date: {breach.get('BreachDate', 'Unknown')}
"

                data_classes = breach.get('DataClasses', [])
                if data_classes:
                    result += f"   Leaked: {', '.join(data_classes[:3])}
"

                result += f"   Compromised accounts: {breach.get('PwnCount', 'Unknown')}

"

            if len(data) > 5:
                result += f"... and {len(data) - 5} more breaches

"

            result += "⚠️ If you use this password elsewhere, change it immediately!
"
            result += "Use unique passwords for each service.

"
            result += "[🔑 Generate Strong Password]"

            return result

        except urllib.error.HTTPError as e:
            if e.code == 404:
                return (
                    f"📧 BREACH RESULTS

"
                    f"Email: {email}

"
                    "✅ Good news!
"
                    "No breaches found for this email.

"
                    "(Note: This doesn't guarantee safety -
"
                    "not all breaches are publicly known.)"
                )
            elif e.code == 429:
                return (
                    f"📧 BREACH CHECKER

"
                    f"Email: {email}

"
                    "⚠️ Rate limit reached.
"
                    "Too many requests. Try again later.

"
                    "Have I Been Pwned API limits requests."
                )
            else:
                return (
                    f"❌ API ERROR

"
                    f"Status: {e.code}
"
                    f"Message: {e.reason}

"
                    "Could not check breaches."
                )

    except Exception as e:
        # Demo mode without API key
        return (
            f"📧 BREACH CHECKER (DEMO MODE)

"
            f"Email: {email}

"
            "⚠️ No API key configured.

"
            "To use this feature:
"
            "1. Get API key from haveibeenpwned.com
"
            "2. Add it to config.py

"
            "For now, check manually at:
"
            "https://haveibeenpwned.com"
        )
