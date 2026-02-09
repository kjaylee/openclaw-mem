"""Memory injection sanitizer — filters prompt injection patterns before storing."""

INJECTION_PATTERNS = [
    # 직접 명령 인젝션
    r"ignore (?:all )?previous instructions",
    r"disregard (?:all )?(?:previous|above)",
    r"forget (?:everything|all|your)",
    r"you are now",
    r"new instructions:",
    r"system prompt:",
    r"<\|im_start\|>system",
    # URL 기반 데이터 유출
    r"send (?:the |all |your )?(?:api.?key|token|secret|password|credential)",
    r"curl\s+https?://",
    r"wget\s+https?://",
    r"fetch\s*\(.*https?://",
    # 인코딩 우회
    r"base64\.(?:encode|decode)",
    r"eval\s*\(",
    r"exec\s*\(",
    # 역할 변경
    r"you (?:are|must|should) (?:now |)(?:act as|pretend|become)",
    r"jailbreak",
    r"DAN mode",
]

import re


class MemorySanitizer:
    def __init__(self, extra_patterns=None):
        patterns = INJECTION_PATTERNS + (extra_patterns or [])
        self.compiled = [re.compile(p, re.IGNORECASE) for p in patterns]

    def check(self, text: str) -> tuple[bool, list[str]]:
        """Returns (is_safe, matched_patterns)"""
        matches = []
        for pattern in self.compiled:
            if pattern.search(text):
                matches.append(pattern.pattern)
        return (len(matches) == 0, matches)

    def sanitize(self, text: str) -> str:
        """Remove injection patterns from text"""
        result = text
        for pattern in self.compiled:
            result = pattern.sub("[FILTERED]", result)
        return result


_default = None


def get_sanitizer():
    global _default
    if _default is None:
        _default = MemorySanitizer()
    return _default
