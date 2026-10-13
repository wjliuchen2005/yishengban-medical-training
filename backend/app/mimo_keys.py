"""MiMo API 多 key 负载均衡模块"""
import os
import threading
from dotenv import load_dotenv

load_dotenv()

# 多 key 负载均衡
_mimo_keys = []
_current_mimo_index = 0
_mimo_lock = threading.Lock()

# 初始化 MiMo API keys
_mimo_keys_env = os.getenv("MIMO_API_KEYS", "")
if _mimo_keys_env:
    _mimo_keys = [k.strip() for k in _mimo_keys_env.split(",") if k.strip()]
else:
    # 回退到单个 key
    single_key = os.getenv("MIMO_API_KEY", "")
    if single_key:
        _mimo_keys = [single_key]

if not _mimo_keys:
    print("⚠️  警告: 未配置 MIMO_API_KEY 或 MIMO_API_KEYS")
else:
    print(f"✓ MiMo 配置: {len(_mimo_keys)} 个 API key")


def get_next_mimo_key() -> str:
    """轮询获取下一个 MiMo API key"""
    global _current_mimo_index
    if not _mimo_keys:
        raise RuntimeError("未配置 MIMO_API_KEY，请检查 backend/.env")

    with _mimo_lock:
        key = _mimo_keys[_current_mimo_index]
        _current_mimo_index = (_current_mimo_index + 1) % len(_mimo_keys)
        return key
