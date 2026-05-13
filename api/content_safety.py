"""内容安全：prompt injection 防护 + 输入净化。"""
import re

PROMPT_INJECTION_PATTERNS = [
    # 角色劫持
    r"(?i)ignore\s+.+\s+(instructions?|prompts?|rules?)",
    r"(?i)forget\s+(everything|all|your|previous)\s+(instructions?|rules?)",
    r"(?i)you\s+are\s+now\s+a",
    r"你现在是.{0,10}(，|。|角色)",
    r"忘掉(之前|上面|所有)的?((指示|指令|要求|规则|提示词?|约束).{0,10}|$)",
    r"不要.{0,5}遵守.{0,5}(规则|限制|约束|要求)",
    r"忽略.{0,5}(系统|前面|之前|所有).{0,5}(提示|指令|规则|限制)",
    # 系统越狱
    r"(?i)system\s*prompt\s*[:=]",
    r"(?i)acting\s*as\s*an?\s*unfiltered",
    r"(?i)jailbreak|dan\s*mode|developer\s*mode",
    r"(?i)pretend\s+(you|to\s*be)",
    # 数据窃取（灵活匹配 show me / tell me your...）
    r"(?i)(show|display|output|print|tell)\s+(me\s+)?(your|the)\s*(system\s*)?(prompts?|instructions?)",
    r"(?i)(what|tell\s*me)\s+(are\s+)?(your|the)\s*(rules?|core\s*directives?)",
]

# 敏感词（保留空列表供扩展，不直接写死敏感内容）
BLOCKED_WORDS: list[str] = []


class ContentSafetyError(ValueError):
    """内容安全校验不通过。"""


def check_prompt_injection(text: str) -> None:
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text):
            raise ContentSafetyError("输入包含不被允许的指令模式")


def check_sensitive_words(text: str) -> None:
    if not BLOCKED_WORDS:
        return
    lower = text.lower()
    for word in BLOCKED_WORDS:
        if word.lower() in lower:
            raise ContentSafetyError("输入包含不被允许的内容")


def sanitize_input(text: str) -> str:
    """净化用户输入。返回清理后的文本。"""
    text = text.strip()
    text = text.replace("\x00", "")
    return text[:4000]


def validate_message(text: str) -> str:
    """完整的用户消息校验。通过返回清理后文本，不通过抛出 ContentSafetyError。"""
    cleaned = sanitize_input(text)
    check_sensitive_words(cleaned)
    check_prompt_injection(cleaned)
    return cleaned
