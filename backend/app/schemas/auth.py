from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: str
    email: str


class UserInfo(BaseModel):
    id: str
    email: str
    created_at: str
