from ninja import Schema
from pydantic import EmailStr


class UserOut(Schema):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    language: str
    is_active: bool


class UserUpdateIn(Schema):
    first_name: str | None = None
    last_name: str | None = None
    language: str | None = None


class LoginIn(Schema):
    email: EmailStr
    password: str


class PasswordChangeIn(Schema):
    old_password: str
    new_password: str
