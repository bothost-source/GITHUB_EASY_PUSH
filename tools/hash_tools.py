"""
TARRIFIC HOST BOT - Hash Tools
Identify, crack, generate, Base64
"""
import hashlib
import base64
import re

# Hash type patterns
HASH_PATTERNS = {
    'MD5': (r'^[a-f0-9]{32}$', '32 hex chars'),
    'SHA-1': (r'^[a-f0-9]{40}$', '40 hex chars'),
    'SHA-256': (r'^[a-f0-9]{64}$', '64 hex chars'),
    'SHA-512': (r'^[a-f0-9]{128}$', '128 hex chars'),
    'SHA-224': (r'^[a-f0-9]{56}$', '56 hex chars'),
    'SHA-384': (r'^[a-f0-9]{96}$', '96 hex chars'),
    'NTLM': (r'^[A-F0-9]{32}$', '32 uppercase hex'),
    'MySQL3': (r'^[a-f0-9]{16}$', '16 hex chars'),
    'MySQL5': (r'^[a-f0-9]{40}$', '40 hex chars (SHA-1)'),
    'CRC32': (r'^[a-f0-9]{8}$', '8 hex chars'),
    'bcrypt': (r'^\$2[ayb]\$\d{2}\$[A-Za-z0-9./]{53}$', 'bcrypt format'),
    'sha256crypt': (r'^\$5\$[A-Za-z0-9./]+\$[A-Za-z0-9./]{43}$', 'SHA-256 crypt'),
    'sha512crypt': (r'^\$6\$[A-Za-z0-9./]+\$[A-Za-z0-9./]{86}$', 'SHA-512 crypt'),
    'MD5CRYPT': (r'^\$1\$[A-Za-z0-9./]+\$[A-Za-z0-9./]{22}$', 'MD5 crypt'),
    'Apache MD5': (r'^\$apr1\$[A-Za-z0-9./]+\$[A-Za-z0-9./]{22}$', 'Apache MD5'),
    'Django PBKDF2': (r'^pbkdf2_sha256\$\d+\$[A-Za-z0-9+/]+\$[A-Za-z0-9+/=]+$', 'Django PBKDF2'),
}

def identify_hash(hash_string):
    """Identify hash type"""
    hash_string = hash_string.strip()

    if not hash_string:
        return "❌ Empty input"

    results = []

    for hash_type, (pattern, description) in HASH_PATTERNS.items():
        if re.match(pattern, hash_string):
            results.append(f"✅ {hash_type}: {description}")

    if not results:
        # Check for other formats
        if hash_string.startswith('$'):
            results.append("⚠️ Unknown crypt format")
        elif len(hash_string) == 32 and all(c in '0123456789abcdef' for c in hash_string.lower()):
            results.append("✅ Likely MD5 (32 hex)")
        elif len(hash_string) == 40 and all(c in '0123456789abcdef' for c in hash_string.lower()):
            results.append("✅ Likely SHA-1 (40 hex)")
        elif len(hash_string) == 64 and all(c in '0123456789abcdef' for c in hash_string.lower()):
            results.append("✅ Likely SHA-256 (64 hex)")
        elif len(hash_string) == 128 and all(c in '0123456789abcdef' for c in hash_string.lower()):
            results.append("✅ Likely SHA-512 (128 hex)")
        else:
            results.append("❌ Unknown format")

    text = f"#️⃣ HASH IDENTIFICATION

"
    text += f"Input: `{hash_string[:50]}{'...' if len(hash_string) > 50 else ''}`
"
    text += f"Length: {len(hash_string)} chars

"
    text += "Possible types:
"
    text += "
".join(results)

    return text

def generate_hashes(text):
    """Generate multiple hash types from text"""
    text_bytes = text.encode('utf-8')

    hashes = {
        'MD5': hashlib.md5(text_bytes).hexdigest(),
        'SHA-1': hashlib.sha1(text_bytes).hexdigest(),
        'SHA-256': hashlib.sha256(text_bytes).hexdigest(),
        'SHA-512': hashlib.sha512(text_bytes).hexdigest(),
        'SHA-224': hashlib.sha224(text_bytes).hexdigest(),
        'SHA-384': hashlib.sha384(text_bytes).hexdigest(),
    }

    result = f"#️⃣ GENERATED HASHES

"
    result += f"Input: `{text[:50]}{'...' if len(text) > 50 else ''}`

"

    for hash_type, hash_value in hashes.items():
        result += f"{hash_type}:
"
        result += f"`{hash_value}`

"

    return result

def base64_convert(text):
    """Base64 encode or decode"""
    text = text.strip()

    # Try to decode first (if it looks like base64)
    try:
        decoded = base64.b64decode(text).decode('utf-8')
        return (
            f"#️⃣ BASE64 DECODED

"
            f"Input: `{text[:50]}{'...' if len(text) > 50 else ''}`

"
            f"Decoded:
"
            f"`{decoded[:200]}{'...' if len(decoded) > 200 else ''}`"
        )
    except:
        pass

    # Encode
    encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    return (
        f"#️⃣ BASE64 ENCODED

"
        f"Input: `{text[:50]}{'...' if len(text) > 50 else ''}`

"
        f"Encoded:
"
        f"`{encoded}`"
    )
