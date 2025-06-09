import json

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from httpx import AsyncClient, Response
from jose import jwt
from datetime import datetime, timedelta

from app.src.api.auth.models import TokenBearer, TokenData
from app.configs.settings import get_settings
from app.src.core.constants.constants import MAIN_SERVICE_VERIFY_ACCESS_TOKEN_URL

oauth2_scheme = HTTPBearer(bearerFormat='JWT', auto_error=False)
config = get_settings()


def create_access_token(token_data: TokenData) -> TokenBearer:
    """
    Создает bearer токен

    Args:
        token_data (TokenData): Содержимое токена.

    Returns:
        TokenBearer: .
    """

    token = jwt.encode(
        token_data.model_dump(), config.BACKEND_SECRET_KEY, algorithm=config.ALGORITHM
    )
    return TokenBearer(access_token=token)


async def verify_access_token(token: str) -> dict:
    """
    Проверяет JWT токен credentials через main сервис

    Args:
        token (str): Содержимое токена.

    Returns:
        dict: Содержимое JWT токен после проверки.
    """
    async with AsyncClient() as client:
        service_key = config.BACKEND_SECRET_KEY
        url = MAIN_SERVICE_VERIFY_ACCESS_TOKEN_URL
        headers = {'Token': service_key}
        data = {'access_token': token, 'token_type': 'bearer'}

        response: Response = await client.post(url=url, json=data, headers=headers)

        if response.status_code == status.HTTP_200_OK:
            return json.loads(response.content.decode('utf-8'))
        else:
            detail = json.loads(response.content.decode('utf-8')).get('detail')
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


async def access_token(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> dict | None:
    """
    Валидация JWT token

    Args:
        token (HTTPAuthorizationCredentials): JWT токен.

    Returns:
        dict: Содержимое JWT токен после проверки либо None.
    """

    if not token:
        return None
    token_data = await verify_access_token(token.credentials)
    return token_data


async def api_token(token: str | None = Depends(APIKeyHeader(name='Token', auto_error=False))) -> str | None:
    """
    Валидация API токена

    Args:
        token (str): API токен.

    Returns:
        str: Токен после проверки либо None.
    """
    if not token:
        return None
    elif token != config.BACKEND_SECRET_KEY:
        return None
    return token


async def check_auth(api_token=Depends(api_token), token_data=Depends(access_token)) -> TokenData:
    """
    Двойная аутентификация API | JWT токена

    Returns:
        TokenData: Токен.
    """
    if not (token_data or api_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Sign in for access')
    if token_data:
        return config.BACKEND_SECRET_KEY
    return api_token
