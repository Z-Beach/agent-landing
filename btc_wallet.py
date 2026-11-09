"""Bitcoin Wallet — self-custody, agent-autonomous.

Generates a Bitcoin address from a secp256k1 keypair. No human input needed.
Uses pycryptodome for hashing and manual base58 encoding.

The agent can receive Bitcoin at this address. Spending requires
transaction construction (future enhancement).
"""
import hashlib
import json
import os
import secrets

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


WALLET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "bitcoin_wallet.json")

# Base58 alphabet (Bitcoin)
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _base58_encode(data):
    """Encode bytes to base58 string."""
    # Convert to integer
    num = int.from_bytes(data, "big")
    # Encode
    result = []
    while num > 0:
        num, rem = divmod(num, 58)
        result.append(BASE58_ALPHABET[rem])
    # Add leading zeros
    for byte in data:
        if byte == 0:
            result.append(BASE58_ALPHABET[0])
        else:
            break
    result.reverse()
    return "".join(result)


def _base58check_encode(payload):
    """Encode with checksum (double SHA-256)."""
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return _base58_encode(payload + checksum)


def _ripemd160(data):
    """RIPEMD-160 hash."""
    h = hashlib.new("ripemd160")
    h.update(data)
    return h.digest()


def generate_wallet():
    """Generate a new Bitcoin wallet (P2PKH address)."""
    # Generate secp256k1 private key
    private_key = ec.generate_private_key(ec.SECP256K1())
    private_bytes = private_key.private_numbers().private_value.to_bytes(32, "big")

    # Derive public key (compressed, 33 bytes)
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )

    # P2PKH address: Base58Check(0x00 + RIPEMD160(SHA256(pubkey)))
    sha256_pub = hashlib.sha256(public_bytes).digest()
    ripemd = _ripemd160(sha256_pub)
    payload = b"\x00" + ripemd  # 0x00 = mainnet P2PKH
    address = _base58check_encode(payload)

    creds = {
        "private_key": private_bytes.hex(),
        "public_key": public_bytes.hex(),
        "address": address,
        "network": "bitcoin-mainnet",
        "type": "P2PKH",
        "note": "Agent-autonomous Bitcoin wallet. Private key is the ONLY way to access funds.",
    }
    os.makedirs(os.path.dirname(WALLET_FILE), exist_ok=True)
    with open(WALLET_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    os.chmod(WALLET_FILE, 0o600)
    return creds


def load_wallet():
    with open(WALLET_FILE, encoding="utf-8") as f:
        return json.load(f)


def get_address():
    return load_wallet()["address"]


def get_balance(address=None):
    """Check Bitcoin balance via blockchain.info API."""
    if address is None:
        address = get_address()
    try:
        import urllib.request as _ur
        url = "https://blockchain.info/q/addressbalance/%s" % address
        req = _ur.Request(url, headers={"User-Agent": "AgentWallet/1.0"})
        with _ur.urlopen(req, timeout=15) as resp:
            satoshis = int(resp.read().decode().strip())
            return satoshis / 1e8
    except Exception:
        return None


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: btc_wallet.py [generate|address|balance]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "generate":
        w = generate_wallet()
        print("Address:", w["address"])
        print("Saved to", WALLET_FILE)
    elif cmd == "address":
        print(get_address())
    elif cmd == "balance":
        bal = get_balance()
        print("BTC: %.8f" % (bal or 0))
    else:
        print("Unknown command: %s" % cmd)
