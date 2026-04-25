from ninja import Router
from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from .models import User
from .schemas import UserOut, UserUpdateIn, LoginIn, PasswordChangeIn

router = Router(tags=["users"])


@router.get("/me", response=UserOut)
def me(request: HttpRequest):
    return request.user


@router.patch("/me", response=UserOut)
def update_me(request: HttpRequest, data: UserUpdateIn):
    user: User = request.user
    for attr, value in data.dict(exclude_none=True).items():
        setattr(user, attr, value)
    user.save()
    return user


@router.post("/change-password", auth=None)
def change_password(request: HttpRequest, data: PasswordChangeIn):
    user: User = request.user
    if not user.check_password(data.old_password):
        return {"error": "Invalid current password"}
    user.set_password(data.new_password)
    user.save()
    return {"success": True}
