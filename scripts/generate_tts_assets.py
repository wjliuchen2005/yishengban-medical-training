#!/usr/bin/env python3
"""Generate the small, repeatable MiMo TTS asset set without embedding secrets."""
from __future__ import annotations

import base64
import json
import os
import ssl
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "backend" / ".env"
OUT_DIR = ROOT / "frontend" / "public" / "audio" / "tts"

ASSETS = {
    "guide-intro.wav": ("冰糖", "亲切明亮、自然微笑，普通话清晰。", "我是“易”生伴，有什么需要帮助的吗？请选择你想要训练的场景。"),
    "guide-home.wav": ("冰糖", "亲切明亮、自然微笑，普通话清晰。", "欢迎来到训练场景，请选择你想要训练的场景。"),
    "guide-history.wav": ("冰糖", "亲切温暖，略有鼓励感。", "温故而知新，欢迎来到历史记录。"),
    "guide-profile.wav": ("冰糖", "亲切简洁，普通话清晰。", "在这里你可以修改个人信息。"),
    "guide-result.wav": ("冰糖", "温暖、鼓励、自然。", "训练完成了，我们一起看看本次复盘。"),
    "psych-opening.wav": ("茉莉", "温柔真诚、陪伴感强，语速稍慢，有自然停顿。", "嗨，我是易心。今天感觉怎么样？不管是开心的、烦心的还是心里堵着说不出口的，都可以慢慢告诉我，我会认真听。"),
}


def load_env() -> dict[str, str]:
    values = dict(os.environ)
    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return values


def synthesize(api_key: str, base_url: str, model: str, voice: str, style: str, text: str) -> bytes:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": style}, {"role": "assistant", "content": text}],
        "audio": {"format": "wav", "voice": voice},
    }, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    ca_file = "/etc/ssl/cert.pem" if Path("/etc/ssl/cert.pem").exists() else None
    ssl_context = ssl.create_default_context(cafile=ca_file)
    with urlopen(request, timeout=60, context=ssl_context) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return base64.b64decode(payload["choices"][0]["message"]["audio"]["data"], validate=True)


def main() -> None:
    env = load_env()
    api_key = env.get("MIMO_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("MIMO_API_KEY is missing from backend/.env or environment")
    base_url = env.get("MIMO_TTS_BASE_URL", "https://api.xiaomimimo.com/v1")
    model = env.get("MIMO_TTS_MODEL", "mimo-v2.5-tts")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, (voice, style, text) in ASSETS.items():
        target = OUT_DIR / filename
        target.write_bytes(synthesize(api_key, base_url, model, voice, style, text))
        print(f"generated {target.relative_to(ROOT)} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
