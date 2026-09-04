"""
场景相关路由

✅ 已实现：
- GET /api/scene/list 获取场景列表
- GET /api/scene/{id} 获取单个场景详情

参考实现见 frontend/src/api/scene.js 的注释
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas import SceneInfo
from app.models import Scene, User
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/scene", tags=["场景"])


def _scene_info(scene: Scene) -> SceneInfo:
    info = SceneInfo.model_validate(scene)
    if "独立看病" in (scene.title or ""):
        return info.model_copy(update={
            "description": "以江苏省人民医院为背景，体验第一次独立看病中的关键决策与沟通",
            "role": "医院流程角色",
        })
    return info


@router.get("/list", response_model=List[SceneInfo])
async def get_scene_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取场景列表

    逻辑：
    1. 查询 is_active=1 的所有场景
    2. 按难度升序排列
    3. 返回列表
    """
    scenes = (
        db.query(Scene)
        .filter(Scene.is_active == 1)
        .order_by(Scene.difficulty.asc())
        .all()
    )
    return [_scene_info(scene) for scene in scenes]


@router.get("/{scene_id}")
async def get_scene_detail(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个场景详情

    逻辑：
    1. 按 id 查询场景 → 404
    2. 返回完整场景信息（含 config）
    """
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景不存在")

    payload = {
        "id": scene.id,
        "title": scene.title,
        "description": scene.description,
        "cover": scene.cover,
        "role": scene.role,
        "role_avatar": scene.role_avatar,
        "background": scene.background,
        "opening_message": scene.opening_message,
        "config": scene.config,
        "difficulty": scene.difficulty,
    }
    if "独立看病" in (scene.title or ""):
        payload.update({
            "description": "以江苏省人民医院为背景，体验第一次独立看病中的关键决策与沟通",
            "role": "医院流程角色",
        })
    return payload
