import os
from pathlib import Path

# 自动加载 .env 文件
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.is_file():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# 如果 .env 没加载到，使用默认值（你的密钥）
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "sk-r2ynHBUL33IusoaHT45VafXIpcJ8pFrTcMWJh8s6j86MlktE")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://cn.aixor.org")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]


def get_chinese_font_path() -> str:
    for p in FONT_CANDIDATES:
        if os.path.isfile(p):
            return p
    return ""
