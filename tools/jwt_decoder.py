"""
TARRIFIC HOST BOT - JWT Decoder
Decode and analyze JWT tokens
"""
import base64
import json
import re

def decode_jwt(token):
    """Decode JWT token"""
    token = token.strip()

    if not token:
        return "❌ Empty token"

    # Check format
    parts = token.split('.')
    if len(parts) != 3:
        return (
            "❌ INVALID JWT FORMAT

"
            "JWT must have 3 parts separated by dots:
"
            "header.payload.signature

"
            f"Your input has {len(parts)} part(s)."
        )

    try:
        # Decode header
        header_b64 = parts[0]
        # Add padding if needed
        header_b64 += '=' * (4 - len(header_b64) % 4)
        header_json = base64.urlsafe_b64decode(header_b64).decode('utf-8')
        header = json.loads(header_json)

        # Decode payload
        payload_b64 = parts[1]
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)

        # Signature (can't decode, just show)
        signature = parts[2]

        # Format output
        result = "🔐 JWT DECODED

"

        result += "HEADER
"
        result += "```json
"
        result += json.dumps(header, indent=2)
        result += "
```

"

        result += "PAYLOAD
"
        result += "```json
"
        result += json.dumps(payload, indent=2)
        result += "
```

"

        result += f"SIGNATURE
"
        result += f"`{signature[:50]}{'...' if len(signature) > 50 else ''}`

"

        # Security analysis
        result += "🔍 ANALYSIS
"

        alg = header.get('alg', 'unknown')
        result += f"• Algorithm: {alg}
"

        if alg == 'none':
            result += "⚠️ CRITICAL: Algorithm is 'none' - token can be forged!
"
        elif alg in ['HS256', 'HS384', 'HS512']:
            result += "• HMAC-SHA based - requires secret key
"
        elif alg in ['RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512']:
            result += "• RSA/ECDSA based - requires private key to sign
"

        # Check for sensitive claims
        sensitive_claims = ['password', 'ssn', 'credit_card', 'secret', 'private']
        payload_str = json.dumps(payload).lower()
        found_sensitive = [claim for claim in sensitive_claims if claim in payload_str]

        if found_sensitive:
            result += f"⚠️ Sensitive data detected: {', '.join(found_sensitive)}
"

        # Check expiry
        if 'exp' in payload:
            from datetime import datetime
            exp_time = datetime.fromtimestamp(payload['exp'])
            now = datetime.now()
            if exp_time < now:
                result += f"🔴 Token expired on {exp_time.strftime('%Y-%m-%d %H:%M:%S')}
"
            else:
                result += f"🟢 Valid until {exp_time.strftime('%Y-%m-%d %H:%M:%S')}
"

        if 'iat' in payload:
            from datetime import datetime
            iat_time = datetime.fromtimestamp(payload['iat'])
            result += f"• Issued at: {iat_time.strftime('%Y-%m-%d %H:%M:%S')}
"

        result += "
⚠️ Never share JWT tokens with untrusted parties!"

        return result

    except Exception as e:
        return (
            f"❌ DECODE ERROR

"
            f"Error: {str(e)}

"
            "Make sure the token is a valid Base64URL-encoded JWT."
        )
