import os
from fastapi import Request
from helpers.functions.discord_verify import verify_signature

async def extract_verified_body(request: Request) -> bytes | None:
    sig = request.headers.get("X-Signature-Ed25519")
    ts = request.headers.get("X-Signature-Timestamp")
    body = await request.body()
    pk = os.environ.get("DISCORD_PUBLIC_KEY")
    if not (sig and ts and pk and verify_signature(pk, sig, ts, body)):
        return None
    return body


