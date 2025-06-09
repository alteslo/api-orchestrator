from datetime import datetime, timedelta

from app.src.api.auth.models import TokenData
from app.src.api.auth.service import create_access_token
from app.configs.settings import get_settings
from fastapi import APIRouter

router = APIRouter()
config = get_settings()


@router.get("/get_acces_token", tags=["auth"])
async def get_acces_token():
    """Возвращает acces token"""

    expires = int((datetime.utcnow() + timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRE_MINUTES))).timestamp())
    tokendata = TokenData(
        user="admin", user_id="12345", access_roles=[], exp=expires, start_service_id=""
    )
    access_token = create_access_token(tokendata)
    return access_token
