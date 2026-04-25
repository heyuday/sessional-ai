from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(pattern="^(patient|clinician)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
