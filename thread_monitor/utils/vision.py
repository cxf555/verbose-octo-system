"""
多模型视觉识别模块 — 支持 Kimi (月之暗面) / 豆包 (火山方舟)。

默认使用 Kimi kimi-k2.6 视觉模型。

使用方式:
    from thread_monitor.utils.vision import recognize_image

    result = recognize_image("screenshot.png", prompt="这张图里有什么？")
    print(result)

API Key 优先级: 参数传入 > 环境变量
"""

import base64
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List

PROVIDERS = {
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "kimi-k2.6",
        "env_key": "KIMI_API_KEY",
        "default_key": None,
    },
    "doubao": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-seed-2-0-lite-260215",
        "env_key": "ARK_API_KEY",
        "default_key": None,
    },
}

DEFAULT_PROVIDER = "kimi"

MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
}


def _resolve_config(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
):
    p = provider or DEFAULT_PROVIDER
    if p not in PROVIDERS:
        raise ValueError(f"未知提供者: {p}，可选: {list(PROVIDERS.keys())}")
    cfg = PROVIDERS[p]
    key = api_key or os.environ.get(cfg["env_key"])
    if not key:
        raise ValueError(
            f"未找到 {p} 的 API Key。请设置环境变量 {cfg['env_key']} 或通过 api_key 参数传入。"
        )
    m = model or cfg["default_model"]
    return cfg["base_url"], m, key


def _image_to_data_url(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    ext = path.suffix.lower()
    mime = MIME_MAP.get(ext, "application/octet-stream")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def recognize_image(
    image_path: str,
    prompt: str = "请详细描述这张图片的内容。",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: Optional[float] = None,
) -> str:
    """调用视觉模型识别单张图片。"""
    base_url, model_name, key = _resolve_config(provider, api_key, model)
    data_url = _image_to_data_url(image_path)

    payload = {
        "model": model_name,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }
    if temperature is not None:
        payload["temperature"] = temperature

    return _call_api(base_url, key, payload)


def recognize_images(
    image_paths: List[str],
    prompt: str = "请描述这些图片的内容和它们之间的关联。",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: Optional[float] = None,
) -> str:
    """调用视觉模型识别多张图片。"""
    base_url, model_name, key = _resolve_config(provider, api_key, model)

    content = []
    for path in image_paths:
        data_url = _image_to_data_url(path)
        content.append({"type": "image_url", "image_url": {"url": data_url}})
    content.append({"type": "text", "text": prompt})

    payload = {
        "model": model_name,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if temperature is not None:
        payload["temperature"] = temperature

    return _call_api(base_url, key, payload)


def _call_api(base_url: str, key: str, payload: dict) -> str:
    url = f"{base_url}/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API 调用失败 (HTTP {e.code}): {body}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"无法连接 API: {e.reason}") from None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m thread_monitor.utils.vision <图片路径> [提示词]")
        print("示例: python -m thread_monitor.utils.vision screenshot.png '图片里有什么？'")
        sys.exit(1)

    img = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "请详细描述这张图片的内容。"
    print(f"正在识别: {img}")
    print(f"提示词: {prompt}")
    print("-" * 50)
    try:
        result = recognize_image(img, prompt=prompt)
        print(result)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
