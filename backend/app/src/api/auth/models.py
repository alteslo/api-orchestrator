from pydantic import BaseModel


class TokenData(BaseModel):
    user: str
    user_id: str
    access_roles: list
    exp: int
    start_service_id: str


class TokenBearer(BaseModel):
    access_token: str
    token_type: str = "bearer"
