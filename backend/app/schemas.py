"""
Pydantic 数据模型

对应请求体和响应体。
email 字段：避免依赖 email-validator，用 str + 简单正则验证
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
import re
from pydantic import BaseModel, Field, field_validator


# =====================================================
# 通用响应
# =====================================================
class ResponseBase(BaseModel):
    """基础响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None


# =====================================================
# 自定义字段验证器（不依赖 email-validator）
# =====================================================
def _validate_email_format(value: Optional[str]) -> Optional[str]:
    """邮箱格式校验：基础正则，够日常使用"""
    if value is None or value == "":
        return None
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, value):
        raise ValueError(f"邮箱格式不正确: {value}")
    return value


# =====================================================
# 用户相关
# =====================================================
class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=20)
    real_name: Optional[str] = None
    student_id: Optional[str] = None
    school: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    @field_validator("email")
    @classmethod
    def _check_email(cls, v):
        return _validate_email_format(v)


class UserRegister(UserBase):
    """注册请求"""
    password: str = Field(..., min_length=6, max_length=20)


class UserLogin(BaseModel):
    """登录请求"""
    username: str
    password: str


class UserInfo(UserBase):
    """用户信息响应"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    user: UserInfo


class UpdateProfile(BaseModel):
    """更新用户信息（不含密码）"""
    real_name: Optional[str] = None
    student_id: Optional[str] = None
    school: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    @field_validator("email")
    @classmethod
    def _check_email(cls, v):
        return _validate_email_format(v)


class ChangePassword(BaseModel):
    """修改密码"""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=20)


# =====================================================
# 场景相关
# =====================================================
class SceneInfo(BaseModel):
    """场景信息"""
    id: int
    title: str
    description: Optional[str] = None
    cover: Optional[str] = None
    role: Optional[str] = None
    role_avatar: Optional[str] = None
    background: Optional[str] = None
    opening_message: Optional[str] = None
    difficulty: int = 1

    class Config:
        from_attributes = True


# =====================================================
# 对话相关
# =====================================================
class StartChatRequest(BaseModel):
    """开始对话请求"""
    scene_id: int
    gender: Literal["male", "female", "unspecified"] = "unspecified"


class StartChatResponse(BaseModel):
    """开始对话响应"""
    session_id: int
    opening_message: str
    opening_role: Literal["system"] = "system"
    opening_meta: Dict[str, Any] = Field(default_factory=dict)
    scene_info: SceneInfo


class ChatMessage(BaseModel):
    """对话消息"""
    id: int
    role: str  # user/ai/coach
    content: str
    timestamp: int
    coach_tip: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    session_id: int
    message: str = Field(..., min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def _strip_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("消息不能为空")
        return value


class SendMessageResponse(BaseModel):
    """发送消息响应"""
    message_id: int
    role: str
    content: str
    timestamp: int
    coach_tip: Optional[Dict[str, Any]] = None
    stage_info: Optional[Dict[str, Any]] = None
    ui_action: Optional[Dict[str, Any]] = None


class MedicalRecordRequest(BaseModel):
    """OSCE 学生独立书写的病历记录。"""
    session_id: int
    content: str = Field(..., min_length=20, max_length=12000)

    @field_validator("content")
    @classmethod
    def _strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("病历记录不能为空")
        return value


# =====================================================
# 评分相关
# =====================================================
class DimensionScores(BaseModel):
    """三维度评分"""
    accuracy: int  # 医学准确性
    warmth: int    # 沟通温度
    decision: int  # 决策合理性


class ResultResponse(BaseModel):
    """评分结果响应"""
    session_id: int
    total_score: int
    dimensions: DimensionScores
    messages: List[Dict[str, Any]]  # 对话回放（带标注）
    decision_tree: Optional[Dict[str, Any]] = None  # 决策树数据
    share_url: Optional[str] = None
