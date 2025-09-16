import nacl.signing


def verify_signature(pk_hex: str, sig_hex: str, ts: str, body: bytes) -> bool:
    try:
        nacl.signing.VerifyKey(bytes.fromhex(pk_hex)).verify(ts.encode() + body, bytes.fromhex(sig_hex))
        return True
    except Exception:
        return False


