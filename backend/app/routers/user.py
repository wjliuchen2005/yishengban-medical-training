"""
用户相关路由

✅ 已实现：
- GET  /api/user/profile 获取当前用户信息
- PUT  /api/user/profile 修改用户信息（不含密码）
- PUT  /api/user/password 修改密码（需要原密码验证）
- POST /api/user/avatar 上传头像

参考实现见 frontend/src/api/user.js 的注释
"""
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.schemas import UpdateProfile, ChangePassword, UserInfo
from app.models import User
from app.database import get_db
from app.auth import verify_password, hash_password
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["用户"])

# 头像保存目录（main.py 会把该目录挂载为静态路由 /static/avatars）
AVATAR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static", "avatars")

# 允许的头像扩展名
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


# =====================================================
# ✅ 已实现：GET /api/user/profile
# =====================================================
@router.get("/profile", response_model=UserInfo)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


# =====================================================
# ✅ 已实现：PUT /api/user/profile
# =====================================================
@router.put("/profile", response_model=UserInfo)
async def update_profile(
    data: UpdateProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改用户信息

    逻辑：
    1. 只更新请求中出现的字段（exclude_unset）
    2. 提交事务
    3. 返回更新后的 user
    """
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


# =====================================================
# ✅ 已实现：PUT /api/user/password
# =====================================================
@router.put("/password")
async def change_password(
    data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码（需要原密码验证）

    逻辑：
    1. verify_password 验证原密码 → 400
    2. hash_password 加密新密码
    3. 更新 user.password_hash
    4. 提交事务
    """
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )

    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"success": True}


# =====================================================
# ✅ 已实现：POST /api/user/avatar
# =====================================================
@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传头像

    逻辑：
    1. 校验文件扩展名
    2. 保存到 backend/static/avatars/
    3. 更新 user.avatar_url
    4. 返回头像 URL
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式：{ext or '未知'}（支持 jpg/png/gif/webp）"
        )

    os.makedirs(AVATAR_DIR, exist_ok=True)
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(AVATAR_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    current_user.avatar_url = f"/static/avatars/{filename}"
    db.commit()

    return {"avatar_url": current_user.avatar_url}
