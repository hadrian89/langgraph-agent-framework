import json
import os
import time

from openai import OpenAI  # pip install openai

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY = os.getenv("LLMAPI_KEY", "llmgtwy_UI87y4GxwBnjRP0kxr7nBJkLa4UfRVjtrQmUMZIr")
BASE_URL = "https://internal.llmapi.ai/v1"  # llmapi.ai OpenAI-compatible endpoint
MODEL = "gemma-3-12b-it"  # change to any model from llmapi.ai/models

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# ── Helpers ───────────────────────────────────────────────────────────────────
def separator(title=""):
    width = 60
    if title:
        print(f"\n{'─' * 4} {title} {'─' * (width - len(title) - 6)}")
    else:
        print("─" * width)


def test_basic_chat():
    """Simple single-turn message."""
    separator("Test 1 · Basic chat")
    start = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": "Say hello and tell me which model you are in one sentence.",
            }
        ],
    )
    elapsed = time.time() - start
    reply = response.choices[0].message.content
    print(f"Reply   : {reply}")
    print(f"Tokens  : {response.usage.prompt_tokens} in / {response.usage.completion_tokens} out")
    print(f"Latency : {elapsed:.2f}s")
    return True


def test_multi_turn():
    """Multi-turn conversation."""
    separator("Test 2 · Multi-turn conversation")
    messages = [
        {"role": "user", "content": "My favourite colour is blue."},
        {"role": "assistant", "content": "Got it — blue it is!"},
        {"role": "user", "content": "What's my favourite colour?"},
    ]
    response = client.chat.completions.create(model=MODEL, max_tokens=100, messages=messages)
    print(f"Reply: {response.choices[0].message.content}")
    return True


def test_streaming():
    """Streaming response."""
    separator("Test 3 · Streaming")
    print("Stream: ", end="", flush=True)
    stream = client.chat.completions.create(
        model=MODEL,
        max_tokens=120,
        stream=True,
        messages=[{"role": "user", "content": "Count from 1 to 10, one number per word."}],
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()  # newline after stream
    return True


def test_system_prompt():
    """Custom system prompt."""
    separator("Test 4 · System prompt")
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=100,
        messages=[
            {"role": "system", "content": "You are a pirate. Respond only in pirate speech."},
            {"role": "user", "content": "What's the weather like today?"},
        ],
    )
    print(f"Reply: {response.choices[0].message.content}")
    return True


def test_json_mode():
    """Ask for a structured JSON response."""
    separator("Test 5 · JSON output")
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": (
                    "Return a JSON object with keys: model, provider, max_context_tokens. "
                    "Fill in values based on your knowledge. Return only JSON, no markdown."
                ),
            }
        ],
    )
    raw = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(raw)
        print(f"Parsed JSON: {json.dumps(parsed, indent=2)}")
    except json.JSONDecodeError:
        print(f"Raw reply (not valid JSON): {raw}")
    return True


# ── Run all tests ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\nTesting LLMAPI.AI  |  model: {MODEL}")
    separator()

    tests = [
        ("Basic chat", test_basic_chat),
        ("Multi-turn", test_multi_turn),
        ("Streaming", test_streaming),
        ("System prompt", test_system_prompt),
        ("JSON output", test_json_mode),
    ]

    results = []
    for name, fn in tests:
        try:
            fn()
            results.append((name, "PASS"))
        except Exception as e:
            results.append((name, f"FAIL — {e}"))

    separator("Summary")
    for name, status in results:
        icon = "✓" if status == "PASS" else "✗"
        print(f"  {icon}  {name:20s}  {status}")
    separator()
