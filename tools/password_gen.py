"""
TARRIFIC HOST BOT - Password Generator
Generate secure passwords with entropy analysis
"""
import secrets
import string
import math

def generate_password(length=16, use_upper=True, use_lower=True, use_numbers=True, use_symbols=True):
    """Generate secure password"""

    # Build character set
    chars = ""
    if use_upper:
        chars += string.ascii_uppercase
    if use_lower:
        chars += string.ascii_lowercase
    if use_numbers:
        chars += string.digits
    if use_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

    if not chars:
        return "❌ No character types selected!"

    # Generate password
    password = ''.join(secrets.choice(chars) for _ in range(length))

    # Calculate entropy
    charset_size = len(chars)
    entropy_bits = length * math.log2(charset_size)

    # Strength rating
    if entropy_bits >= 128:
        strength = "💪 Excellent"
        crack_time = "centuries"
    elif entropy_bits >= 80:
        strength = "🟢 Strong"
        crack_time = "decades"
    elif entropy_bits >= 60:
        strength = "🟡 Good"
        crack_time = "years"
    elif entropy_bits >= 40:
        strength = "🟠 Fair"
        crack_time = "months"
    else:
        strength = "🔴 Weak"
        crack_time = "days"

    # Build result
    result = f"🔑 GENERATED PASSWORD

"
    result += f"`{password}`

"

    result += f"Length: {length} characters
"
    result += f"Charset: {charset_size} characters
"
    result += f"Entropy: {entropy_bits:.1f} bits
"
    result += f"Strength: {strength}
"
    result += f"Est. crack time: {crack_time}

"

    result += "Character types used:
"
    if use_upper:
        result += "  ✓ Uppercase (A-Z)
"
    if use_lower:
        result += "  ✓ Lowercase (a-z)
"
    if use_numbers:
        result += "  ✓ Numbers (0-9)
"
    if use_symbols:
        result += "  ✓ Symbols (!@#$...)
"

    result += "
⚠️ Store this password securely!
"
    result += "Use a password manager if possible."

    return result
