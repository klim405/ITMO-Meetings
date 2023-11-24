from pydantic import BaseModel, PositiveInt


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: PositiveInt
