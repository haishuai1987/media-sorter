from datetime import timedelta
from typing import Any, List, Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app import schemas
from app.chain.user import UserChain
from app.core import security
from app.core.config import settings
from app.db.systemconfig_oper import SystemConfigOper
from app.helper.sites import SitesHelper  # noqa
from app.helper.wallpaper import WallpaperHelper
from app.schemas.types import SystemConfigKey

router = APIRouter()


@router.post("/access-token", summary="获取token", response_model=schemas.Token)
def login_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        otp_password: Annotated[str | None, Form()] = None
) -> Any:
    """
    获取认证Token
    """
    success, user_or_message = UserChain().user_authenticate(username=form_data.username,
                                                             password=form_data.password,
                                                             mfa_code=otp_password)

    if not success:
        raise HTTPException(status_code=401, detail=user_or_message)

    # 用户等级
    level = SitesHelper().auth_level
    # 是否显示配置向导
    show_wizard = not SystemConfigOper().get(SystemConfigKey.SetupWizardState) and not settings.ADVANCED_MODE
    return schemas.Token(
        access_token=security.create_access_token(
            userid=user_or_message.id,
            username=user_or_message.name,
            super_user=user_or_message.is_superuser,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            level=level
        ),
        token_type="bearer",
        super_user=user_or_message.is_superuser,
        user_id=user_or_message.id,
        user_name=user_or_message.name,
        avatar=user_or_message.avatar,
        level=level,
        permissions=user_or_message.permissions or {},
        widzard=show_wizard
    )


@router.get("/wallpaper", summary="登录页面电影海报", response_model=schemas.Response)
def wallpaper() -> Any:
    """
    获取登录页面电影海报
    """
    url = WallpaperHelper().get_wallpaper()
    if url:
        return schemas.Response(
            success=True,
            message=url
        )
    return schemas.Response(success=False)


@router.get("/wallpapers", summary="登录页面电影海报列表", response_model=List[str])
def wallpapers() -> Any:
    """
    获取登录页面电影海报
    """
    return WallpaperHelper().get_wallpapers()
