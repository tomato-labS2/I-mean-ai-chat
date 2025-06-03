import jwt
from fastapi import HTTPException
from .config import settings

async def verify_token(token: str) -> dict:
    try:
        print(f"[SECURITY_DEBUG] Verifying token: {token[:20]}...")
        
        # 토큰에서 'Bearer ' 접두사가 있으면 제거
        if token.startswith('Bearer '):
            token = token[7:]
            
        # 토큰 디코딩 시도
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            print(f"[SECURITY_DEBUG] Token decoded successfully. Payload: {payload}")
            return payload
        except jwt.ExpiredSignatureError:
            print("[SECURITY_ERROR] Token has expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            print(f"[SECURITY_ERROR] Token validation error: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
            
    except Exception as e:
        print(f"[SECURITY_ERROR] Token processing error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e)) 