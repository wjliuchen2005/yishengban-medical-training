"""
大模型调用模块

已接入：智谱 GLM、DeepSeek（均为 OpenAI 兼容接口，按 base_url 自动区分）

配置方式（backend/.env）：
- LLM_API_KEY / DEEPSEEK_API_KEY  API 密钥（智谱密钥形如 id.secret）
- LLM_API_KEYS  多个密钥（逗号分隔），用于负载均衡，例如：key1,key2,key3
- LLM_BASE_URL   智谱 https://open.bigmodel.cn/api/paas/v4 / DeepSeek https://api.deepseek.com
- LLM_MODEL      智谱 glm-5.3-flash / DeepSeek deepseek-v4-pro
- LLM_REASONING_EFFORT  评分等复杂任务是否开深度思考，默认 high
- LLM_CHAT_REASONING_EFFORT  对话的推理力度，默认 low（关思考保证响应速度）
"""
import os
import json
import threading
from openai import OpenAI
from dotenv import load_dotenv
from app.voice import VOICE_GUIDANCE

load_dotenv()

BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("LLM_MODEL", "deepseek-v4-pro")
PROVIDER = "zhipu" if "bigmodel.cn" in BASE_URL else "deepseek"
REASONING_EFFORT = os.getenv("LLM_REASONING_EFFORT", "high")
CHAT_REASONING_EFFORT = os.getenv("LLM_CHAT_REASONING_EFFORT", "low")

# 多 key 负载均衡支持
_api_keys = []
_current_key_index = 0
_key_lock = threading.Lock()

# 初始化 API keys
_keys_env = os.getenv("LLM_API_KEYS", "")
if _keys_env:
    _api_keys = [k.strip() for k in _keys_env.split(",") if k.strip()]
else:
    # 回退到单个 key
    single_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
    if single_key:
        _api_keys = [single_key]

if not _api_keys:
    print("⚠️  警告: 未配置 LLM_API_KEY 或 LLM_API_KEYS")

print(f"✓ LLM 配置: {len(_api_keys)} 个 API key, 模型: {MODEL}, 提供商: {PROVIDER}")

# 客户端池（每个 key 一个客户端）
_clients = {}
_clients_lock = threading.Lock()


def _get_next_key() -> str:
    """轮询获取下一个 API key"""
    global _current_key_index
    if not _api_keys:
        raise RuntimeError("未配置 LLM_API_KEY，请检查 backend/.env")

    with _key_lock:
        key = _api_keys[_current_key_index]
        _current_key_index = (_current_key_index + 1) % len(_api_keys)
        return key


def _get_client() -> OpenAI:
    """获取下一个可用的客户端（轮询方式）"""
    api_key = _get_next_key()

    with _clients_lock:
        if api_key not in _clients:
            _clients[api_key] = OpenAI(api_key=api_key, base_url=BASE_URL)
        return _clients[api_key]


def _thinking_kwargs(reasoning_effort: str | None) -> dict:
    """按服务商拼思考参数：对话（low）用低思考力度提速，评分等复杂任务用 high。"""
    effort = reasoning_effort or REASONING_EFFORT
    if PROVIDER == "zhipu":
        # GLM-5.x 始终思考，力度只接受 low/high/max
        level = "low" if effort in ("low", "off") else "high"
        return {"reasoning_effort": level}
    return {
        "reasoning_effort": effort,
        "extra_body": {"thinking": {"type": "enabled"}},
    }


def _complete(
    system_prompt: str,
    messages: list,
    json_mode: bool = False,
    reasoning_effort: str | None = None,
    timeout_seconds: float | None = None,
    max_retries: int | None = None,
) -> str:
    """底层调用：拼系统提示词 + 对话历史，返回文本"""
    client = _get_client()

    request_options = {}
    if timeout_seconds is not None:
        request_options["timeout"] = timeout_seconds
    if max_retries is not None:
        request_options["max_retries"] = max_retries
    request_client = client.with_options(**request_options) if request_options else client

    full_messages = [{"role": "system", "content": system_prompt + VOICE_GUIDANCE}]
    full_messages.extend(messages)

    kwargs = _thinking_kwargs(reasoning_effort)
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = request_client.chat.completions.create(
        model=MODEL,
        messages=full_messages,
        stream=False,
        **kwargs,
    )
    return response.choices[0].message.content


def generate_reply(system_prompt: str, messages: list) -> str:
    """
    角色扮演对话（患者智能体）

    用低推理力度换取响应速度（前端有超时限制）。

    :param system_prompt: 系统提示词（见 app/ai/prompts.py）
    :param messages: 对话历史 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    :return: AI 回复文本
    """
    return _complete(system_prompt, messages, reasoning_effort=CHAT_REASONING_EFFORT)


def call_llm_json(
    messages: list,
    system_prompt: str,
    reasoning_effort: str | None = None,
    timeout_seconds: float | None = None,
    max_retries: int | None = None,
) -> dict:
    """
    要求返回 JSON 的调用（教练智能体、评分智能体）

    :param messages: 对话历史
    :param system_prompt: 系统提示词（需包含 JSON 格式要求）
    :param reasoning_effort: 推理力度；教练等实时场景传 CHAT_REASONING_EFFORT 提速，评分默认 high
    :param timeout_seconds: 本次请求的超时秒数；不传则使用 SDK 默认值
    :param max_retries: 本次请求的自动重试次数；不传则使用 SDK 默认值
    :return: 解析后的 dict；解析失败时抛出 ValueError
    """
    content = _complete(
        system_prompt,
        messages,
        json_mode=True,
        reasoning_effort=reasoning_effort,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )

    # 兼容模型偶尔在 JSON 外面包一层 ```json ``` 的情况
    text = content.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"大模型返回的不是合法 JSON: {content[:200]}") from e
