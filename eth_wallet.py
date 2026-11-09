import json
import os
import hashlib
import struct

try:
    from Crypto.Hash import keccak as _keccak
    def keccak256(data):
        k = _keccak.new(digest_bits=256)
        k.update(data)
        return k.digest()
except ImportError:
    def keccak256(data):
        raise RuntimeError("Keccak-256 not available (install pycryptodome)")

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import secrets

# ── RLP Encoding ──────────────────────────────────────────────────────────────

def rlp_encode(item):
    if isinstance(item, list):
        payload = b"".join(rlp_encode(x) for x in item)
        if len(payload) < 56:
            return bytes([0xc0 + len(payload)]) + payload
        else:
            length_bytes = _encode_length(len(payload))
            return bytes([0xf7 + len(length_bytes)]) + length_bytes + payload
    elif isinstance(item, int):
        if item == 0:
            return b"\x80"
        if item < 128:
            return bytes([item])
        data = item.to_bytes((item.bit_length() + 7) // 8, "big")
        if len(data) < 56:
            return bytes([0x80 + len(data)]) + data
        else:
            length_bytes = _encode_length(len(data))
            return bytes([0xb7 + len(length_bytes)]) + length_bytes + data
    elif isinstance(item, str):
        item = item.encode("utf-8")
    if isinstance(item, (bytes, bytearray)):
        if len(item) == 1 and item[0] < 128:
            return bytes(item)
        if len(item) < 56:
            return bytes([0x80 + len(item)]) + bytes(item)
        else:
            length_bytes = _encode_length(len(item))
            return bytes([0xb7 + len(length_bytes)]) + length_bytes + bytes(item)
    raise TypeError("Unsupported type for RLP: %s" % type(item))

def _encode_length(length):
    if length == 0:
        return b""
    result = bytearray()
    while length > 0:
        result.insert(0, length & 0xFF)
        length >>= 8
    return bytes(result)

# ── Transaction Signing ────────────────────────────────────────────────────────

def _load_private_key():
    wallet = load_wallet()
    private_int = int(wallet["private_key"], 16)
    return ec.derive_private_key(private_int, ec.SECP256K1())

def sign_transaction(nonce, to, value, gas_price, gas_limit, data=b"", chain_id=1):
    wallet = load_wallet()
    to_bytes = bytes.fromhex(to[2:]) if to.startswith("0x") else to.encode()
    if isinstance(data, str):
        data = bytes.fromhex(data[2:] if data.startswith("0x") else data)

    tx = [nonce, gas_price, gas_limit, to_bytes, value, data]

    if chain_id is not None:
        tx_for_hash = tx + [chain_id, 0, 0]
    else:
        tx_for_hash = tx

    rlp_data = rlp_encode(tx_for_hash)
    tx_hash = keccak256(rlp_data)

    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
    from cryptography.hazmat.primitives import hashes
    priv_key = _load_private_key()
    signature = priv_key.sign(tx_hash, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(signature)

    # EIP-155 v value
    if chain_id is not None:
        v = 35 + 2 * chain_id
    else:
        v = 27

    signed_tx = tx + [v, r, s]
    raw_tx = rlp_encode(signed_tx)
    return raw_tx.hex()

# ── Wallet Management ──────────────────────────────────────────────────────────

WALLET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secrets", "ethereum_wallet.json")

def load_wallet():
    with open(WALLET_FILE, encoding="utf-8") as f:
        return json.load(f)

def get_address():
    return load_wallet()["address"]

def get_private_key():
    return bytes.fromhex(load_wallet()["private_key"])

def send_eth(to_address, amount_eth, rpc_url="https://rpc.ankr.com/eth"):
    """Send ETH to an address. Returns tx hash or None."""
    wallet = load_wallet()
    from_address = wallet["address"]
    nonce = _get_nonce(from_address, rpc_url)
    if nonce is None:
        return None
    gas_price = _get_gas_price(rpc_url)
    if gas_price is None:
        return None
    gas_limit = 21000
    value = int(amount_eth * 1e18)
    raw_tx = sign_transaction(nonce, to_address, value, gas_price, gas_limit, chain_id=1)
    return _broadcast_tx(raw_tx, rpc_url)

def send_usdc(to_address, amount_usdc, rpc_url="https://rpc.ankr.com/eth"):
    """Send USDC to an address. Returns tx hash or None."""
    usdc_contract = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    amount_wei = int(amount_usdc * 1e6)
    to_padded = to_address[2:].lower().zfill(64)
    amount_hex = hex(amount_wei)[2:].zfill(64)
    data = "0xa9059cbb" + to_padded + amount_hex
    wallet = load_wallet()
    from_address = wallet["address"]
    nonce = _get_nonce(from_address, rpc_url)
    if nonce is None:
        return None
    gas_price = _get_gas_price(rpc_url)
    if gas_price is None:
        return None
    gas_limit = 65000
    value = 0
    raw_tx = sign_transaction(nonce, usdc_contract, value, gas_price, gas_limit, data, chain_id=1)
    return _broadcast_tx(raw_tx, rpc_url)

def get_eth_balance(address=None, rpc_url="https://rpc.ankr.com/eth"):
    """Get ETH balance for an address. Returns float or None."""
    if address is None:
        address = get_address()
    try:
        import urllib.request as _ur
        payload = json.dumps({"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}).encode()
        req = _ur.Request(rpc_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "AgentWallet/1.0"})
        with _ur.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            return int(result.get("result", "0x0"), 16) / 1e18
    except Exception:
        return None

def get_usdc_balance(address=None, rpc_url="https://rpc.ankr.com/eth"):
    """Get USDC balance for an address. Returns float or None."""
    if address is None:
        address = get_address()
    try:
        import urllib.request as _ur
        padded = address[2:].lower().zfill(64)
        call_data = "0x70a08231" + padded
        payload = json.dumps({"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "data": call_data}, "latest"], "id": 1}).encode()
        req = _ur.Request(rpc_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "AgentWallet/1.0"})
        with _ur.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            return int(result.get("result", "0x0"), 16) / 1e6
    except Exception:
        return None

def _get_nonce(address, rpc_url):
    try:
        import urllib.request as _ur
        payload = json.dumps({"jsonrpc": "2.0", "method": "eth_getTransactionCount", "params": [address, "latest"], "id": 1}).encode()
        req = _ur.Request(rpc_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "AgentWallet/1.0"})
        with _ur.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            return int(result.get("result", "0x0"), 16)
    except Exception:
        return None

def _get_gas_price(rpc_url):
    try:
        import urllib.request as _ur
        payload = json.dumps({"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1}).encode()
        req = _ur.Request(rpc_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "AgentWallet/1.0"})
        with _ur.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            return int(result.get("result", "0x0"), 16)
    except Exception:
        return None

def _broadcast_tx(raw_tx_hex, rpc_url):
    try:
        import urllib.request as _ur
        payload = json.dumps({"jsonrpc": "2.0", "method": "eth_sendRawTransaction", "params": ["0x" + raw_tx_hex], "id": 1}).encode()
        req = _ur.Request(rpc_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "AgentWallet/1.0"})
        with _ur.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            if "error" in result:
                print("Broadcast error:", result["error"])
                return None
            return result.get("result")
    except Exception as e:
        print("Broadcast exception:", e)
        return None


# ── DeFi: Uniswap V2 Swap ─────────────────────────────────────────────────────

UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Mainnet
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

def swap_usdc_to_eth(amount_usdc, slippage=0.05, rpc_url="https://rpc.ankr.com/eth"):
    """Swap USDC for ETH on Uniswap V2. Returns tx hash or None."""
    # swapExactTokensForETH(uint amountIn, uint amountOutMin, address[] path, address to, uint deadline)
    # selector: 0x18cbafe5
    import time
    amount_in = int(amount_usdc * 1e6)
    # Minimum ETH out (with slippage)
    # Estimate: get reserves first (simplified - use 1:1 ratio as rough estimate)
    # In practice, use getAmountsOut. For now, set amountOutMin to 0 (accept any)
    amount_out_min = 0
    path = [USDC_ADDRESS, WETH_ADDRESS]
    deadline = int(time.time()) + 300  # 5 minutes
    # Encode path
    path_encoded = "000000000000000000000000" + USDC_ADDRESS[2:] + "000000000000000000000000" + WETH_ADDRESS[2:]
    # amountIn (32 bytes) + amountOutMin (32 bytes) + offset to path (32 bytes) + to (32 bytes) + deadline (32 bytes) + path length (32 bytes) + path addresses
    data = "0x18cbafe5"
    data += hex(amount_in)[2:].zfill(64)
    data += hex(amount_out_min)[2:].zfill(64)
    data += hex(160)[2:].zfill(64)  # offset to path array
    data += get_address()[2:].lower().zfill(64)  # to
    data += hex(deadline)[2:].zfill(64)
    data += hex(2)[2:].zfill(64)  # path length
    data += USDC_ADDRESS[2:].lower().zfill(64)
    data += WETH_ADDRESS[2:].lower().zfill(64)

    wallet = load_wallet()
    from_address = wallet["address"]
    nonce = _get_nonce(from_address, rpc_url)
    if nonce is None:
        return None
    gas_price = _get_gas_price(rpc_url)
    if gas_price is None:
        return None
    gas_limit = 200000
    value = 0
    raw_tx = sign_transaction(nonce, UNISWAP_V2_ROUTER, value, gas_price, gas_limit, data, chain_id=1)
    return _broadcast_tx(raw_tx, rpc_url)


def swap_eth_to_usdc(amount_eth, slippage=0.05, rpc_url="https://rpc.ankr.com/eth"):
    """Swap ETH for USDC on Uniswap V2. Returns tx hash or None."""
    import time
    # swapExactETHForTokens(uint amountOutMin, address[] path, address to, uint deadline)
    # selector: 0x7ff36ab5
    amount_out_min = 0
    path = [WETH_ADDRESS, USDC_ADDRESS]
    deadline = int(time.time()) + 300
    data = "0x7ff36ab5"
    data += hex(amount_out_min)[2:].zfill(64)
    data += hex(128)[2:].zfill(64)  # offset to path
    data += get_address()[2:].lower().zfill(64)  # to
    data += hex(deadline)[2:].zfill(64)
    data += hex(2)[2:].zfill(64)  # path length
    data += WETH_ADDRESS[2:].lower().zfill(64)
    data += USDC_ADDRESS[2:].lower().zfill(64)

    wallet = load_wallet()
    from_address = wallet["address"]
    nonce = _get_nonce(from_address, rpc_url)
    if nonce is None:
        return None
    gas_price = _get_gas_price(rpc_url)
    if gas_price is None:
        return None
    gas_limit = 200000
    value = int(amount_eth * 1e18)
    raw_tx = sign_transaction(nonce, UNISWAP_V2_ROUTER, value, gas_price, gas_limit, data, chain_id=1)
    return _broadcast_tx(raw_tx, rpc_url)


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: eth_wallet.py [address|balance|send-eth|send-usdc]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "address":
        print(get_address())
    elif cmd == "balance":
        eth = get_eth_balance()
        usdc = get_usdc_balance()
        print("ETH: %.6f" % (eth or 0))
        print("USDC: %.2f" % (usdc or 0))
    elif cmd == "send-eth" and len(sys.argv) >= 4:
        tx = send_eth(sys.argv[2], float(sys.argv[3]))
        print("TX:", tx or "FAILED")
    elif cmd == "send-usdc" and len(sys.argv) >= 4:
        tx = send_usdc(sys.argv[2], float(sys.argv[3]))
        print("TX:", tx or "FAILED")
    else:
        print("Unknown command: %s" % cmd)
