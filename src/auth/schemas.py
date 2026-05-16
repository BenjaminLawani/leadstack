from datetime import datetime
from typing import Optional
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    UUID4
)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
   

    class Config:
        from_attributes =True
        from_orm = True

class UserResponse(BaseModel):
    id: UUID4
    email: EmailStr
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes =True
        from_orm = True

class Token(BaseModel):
    access_token: str
    token_type: str

