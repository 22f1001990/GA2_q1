from fastapi import FastAPI, HTTPException, status, Request
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timezone

app = FastAPI()

PUBLIC_KEY = """MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB"""

EXPECTED_ISS = "https://idp.exam.local"
EXPECTED_AUD = "tds-969pasph.apps.exam.local"

class TokenRequest(BaseModel):
    token: str

@app.post("/verify")
async def verify(req: TokenRequest):
    token = req.token
    print (token)
    try:
        # Decode and verify signature + expiration automatically.
        # We explicitly require RS256 and verify audience + issuer manually below.
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"], options={"verify_aud": False})
    except JWTError:
        # signature invalid, malformed token, or expired (if jwt library raises on exp)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"valid": False})
        # Check issuer
    iss = payload.get("iss")
    if iss != EXPECTED_ISS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"valid": False})
        # Check audience (aud claim may be a string or list)
    aud = payload.get("aud")
    if isinstance(aud, list):
        aud_ok = EXPECTED_AUD in aud
    else:
        aud_ok = (aud == EXPECTED_AUD)
    if not aud_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"valid": False})
        # Check expiry explicitly if the library didn't already enforce it
    exp = payload.get("exp")
    if exp is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"valid": False})
    now_ts = int(datetime.now(tz=timezone.utc).timestamp())
    if exp <= now_ts:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"valid": False})
        # On success, echo required claims. If email or sub missing, return them as None.
    return {"valid": True, "email": payload.get("email"), "sub": payload.get("sub"), "aud": payload.get("aud")}

