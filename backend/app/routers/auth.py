"""
认证相关路由

✅ 已实现：
- POST /api/auth/register 用户注册
- POST /api/auth/login 用户登录
- POST /api/auth/logout 退出登录（无状态，前端清 token 即可）
- GET  /api/auth/me 获取当前登录用户

参考实现见 frontend/src/api/auth.js 的注释
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas import (
    UserRegister as UserRegisterSchema,
    UserLogin,
    LoginResponse,
    UserInfo
)
from app.models import User
from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])

# tokenUrl 用于 Swagger 文档的"Authorize"按钮调用登录接口
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# =====================================================
# ✅ 已实现：POST /api/auth/register
# =====================================================
@router.post("/register", response_model=LoginResponse)
async def register(data: UserRegisterSchema, db: Session = Depends(get_db)):
    """
    用户注册

    逻辑：
    1. 检查用户名是否已存在 → 400
    2. 加密密码（hash_password）
    3. 创建用户记录
    4. 生成 JWT token
    5. 返回 token + user
    """
    # 1. 查重
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 2. 创建用户
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        real_name=data.real_name,
        student_id=data.student_id,
        school=data.school or "南京医科大学",
        email=data.email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3. 生成 token
    token = create_access_token({"user_id": user.id, "username": user.username})

    # 4. 返回
    return LoginResponse(
        token=token,
        user=UserInfo.model_validate(user)
    )


# =====================================================
# ✅ 已实现：POST /api/auth/login
# =====================================================
@router.post("/login", response_model=LoginResponse)
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录

    逻辑：
    1. 根据 username 查询用户
    2. verify_password 验证密码 → 401
    3. 验证成功生成 JWT token
    4. 返回 token + user
    """
    # 1. 查询用户
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. 验证密码
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. 生成 token
    token = create_access_token({"user_id": user.id, "username": user.username})

    # 4. 返回
    return LoginResponse(
        token=token,
        user=UserInfo.model_validate(user)
    )


# =====================================================
# ✅ 已实现：POST /api/auth/logout
# =====================================================
@router.post("/logout")
async def logout():
    """
    退出登录

    说明：
    - JWT 是无状态的，前端清除 token 即可
    - 如需服务端失效，可维护 token 黑名单（暂未实现）
    """
    return {"code": 0, "message": "success", "data": None}


# =====================================================
# ✅ 已实现：依赖注入 - 获取当前登录用户
# =====================================================
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    依赖注入：从 token 解析当前登录用户

    用法：
    @router.get("/xxx")
    async def xxx(current_user: User = Depends(get_current_user)):
        return current_user
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的 token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 中缺少 user_id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


# =====================================================
# ✅ 已实现：GET /api/auth/me
# =====================================================
@router.get("/me", response_model=UserInfo)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息（需要 token）"""
    return current_user
