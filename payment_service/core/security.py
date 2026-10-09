import os
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY = os.environ["API_KEY"]


async def verify_api_key(api_key: str | None = Depends(api_key_header)) -> None:
    if api_key is None or api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid X-API-Key header value")
