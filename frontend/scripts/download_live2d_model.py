#!/usr/bin/env python3
"""从 CDN 下载 Live2D Cubism 4 模型（递归解析 model3.json 中的资源引用）"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

KNOWN_EXTS = {
    ".moc3",
    ".png",
    ".physics3.json",
    ".pose3.json",
    ".motion3.json",
    ".exp3.json",
    ".cdi3.json",
    ".model3.json",
}


def collect_refs(obj, base_url):
    refs = set()
    if isinstance(obj, dict):
        for v in obj.values():
            refs.update(collect_refs(v, base_url))
    elif isinstance(obj, list):
        for item in obj:
            refs.update(collect_refs(item, base_url))
    elif isinstance(obj, str) and not obj.startswith(("http:", "https:")):
        for ext in KNOWN_EXTS:
            if obj.endswith(ext):
                refs.add(urljoin(base_url, obj))
                break
    return refs


def download(url, local_path):
    local_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {url} -> {local_path}")
    with urlopen(url, timeout=30) as resp:
        data = resp.read()
    local_path.write_bytes(data)


def main():
    if len(sys.argv) != 3:
        print("Usage: download_live2d_model.py <model3.json-url> <out-dir>")
        sys.exit(1)
    model_url = sys.argv[1]
    out_dir = Path(sys.argv[2])
    print(f"Downloading model from {model_url}")
    print(f"Output directory: {out_dir}")

    with urlopen(model_url, timeout=30) as resp:
        model_json = json.loads(resp.read())

    refs = collect_refs(model_json, model_url)
    # 确保 model3.json 本身也保存一份
    refs.add(model_url)

    for ref in sorted(refs):
        rel = urlparse(ref).path.lstrip("/")
        # 只保留模型目录之后的相对路径
        # base 是 model3.json 所在目录，所以直接去掉 base path 前缀即可
        base_path = urlparse(model_url).path.rsplit("/", 1)[0]
        rel_local = ref[len(base_path):].lstrip("/") if ref.startswith(base_path) else urlparse(ref).path.split("/")[-1]
        local = out_dir / rel_local
        try:
            download(ref, local)
        except Exception as e:
            print(f"  FAILED {ref}: {e}")
            # 失败后继续尝试其它文件；模型仍可能可用（缺少非关键动作表情仍可加载）

    print("Done.")


if __name__ == "__main__":
    main()
