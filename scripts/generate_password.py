#!/usr/bin/env python3
"""
Generate a cryptographically secure random password for Kyoka Lavalink V4.
"""
import secrets
import string

def generate_secure_password(length: int = 36) -> str:
    alphabet = string.ascii_letters + string.digits + "-_.~"
    # Ensure at least one uppercase, lowercase, and digit
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)):
            return password

if __name__ == "__main__":
    password = generate_secure_password()
    print("=" * 64)
    print(" KYOKA LAVALINK V4 - SECURE PASSWORD GENERATOR")
    print("=" * 64)
    print(f"\nGenerated Password:\n{password}\n")
    print("=" * 64)
    print("How to use this password:")
    print("1. In Render Dashboard (kyoka-lavalink service):")
    print("   Environment -> Add Environment Variable:")
    print("   LAVALINK_SERVER_PASSWORD = " + password)
    print("\n2. In Kyoka Discord Bot (.env file or Render Environment):")
    print("   LAVALINK_PASSWORD = " + password)
    print("=" * 64)

