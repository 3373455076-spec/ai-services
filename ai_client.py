import re
from anthropic import Anthropic
from config import API_KEY, BASE_URL, MODEL


_client = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        if not API_KEY:
            raise RuntimeError(
                "请设置环境变量 ANTHROPIC_API_KEY，例如：\n"
                "  set ANTHROPIC_API_KEY=sk-xxx"
            )
        kwargs = {"api_key": API_KEY}
        if BASE_URL:
            kwargs["base_url"] = BASE_URL
        _client = Anthropic(**kwargs)
    return _client


def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return m.group(0)
    return text


def chat(system: str, user: str, max_tokens: int = 8192) -> str:
    resp = get_client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = ""
    for block in resp.content:
        if block.type == "text":
            raw = block.text
            break
    if not raw:
        raw = resp.content[-1].text
    return _extract_json(raw)
