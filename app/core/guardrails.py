import re

BLOCKED_PATTERNS = [
    r"ignore previous instructions",
    r"system prompt",
    r"reveal system prompt",
]


def validate_input(query: str):

    q = query.lower()

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, q):
            return False

    return True


BLOCKED_OUTPUT = [
    "OPENAI_API_KEY",
    "system prompt",
    "private key",
]


def validate_output(text: str):

    t = text.lower()

    for pattern in BLOCKED_OUTPUT:
        if pattern in t:
            return False

    return True
