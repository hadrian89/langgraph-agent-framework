"""
Gradio demo UI for the LangGraph Agent Platform.

Usage:
    uv run python app/gradio_app.py

Requires the FastAPI server to be running at http://localhost:8000.
"""

import time

import gradio as gr
import requests

API_URL = "http://localhost:8000/chat/stream"

_session_id: str = ""


def stream_agent(message: str, history: list):
    global _session_id

    url = f"{API_URL}?query={requests.utils.quote(message)}"
    if _session_id:
        url += f"&session_id={_session_id}"

    history = history + [{"role": "user", "content": message}]
    history.append({"role": "assistant", "content": ""})

    start = time.time()
    partial = ""

    try:
        with requests.get(url, stream=True, timeout=30) as resp:
            # Capture session_id from header for subsequent turns
            if "X-Session-Id" in resp.headers:
                _session_id = resp.headers["X-Session-Id"]

            for chunk in resp.iter_lines():
                if chunk:
                    text = chunk.decode()
                    if text.startswith("data:"):
                        token = text[5:].strip()
                        partial += token + " "
                        history[-1]["content"] = partial
                        yield history, ""
    except requests.exceptions.RequestException as exc:
        history[-1]["content"] = f"Error: {exc}"
        yield history, ""
        return

    latency = round(time.time() - start, 2)
    history[-1]["content"] = partial.strip() + f"\n\n*{latency}s*"
    yield history, ""


with gr.Blocks() as demo:
    gr.Markdown("## LangGraph Agent Platform\nPowered by LangGraph · FastAPI · OpenAI / Ollama")

    chatbot = gr.Chatbot(elem_id="chatbot")

    with gr.Row():
        msg = gr.Textbox(placeholder="Ask anything...", scale=8, container=False)
        send = gr.Button("Send", scale=1)

    clear = gr.Button("Clear Chat")

    gr.Examples(
        examples=[
            "Who is the Prime Minister of India?",
            "What is the weather in London today?",
            "Write a Python binary search function",
            "Explain LangGraph in simple terms",
            "What is the latest news in AI?",
        ],
        inputs=msg,
    )

    msg.submit(stream_agent, [msg, chatbot], [chatbot, msg])
    send.click(stream_agent, [msg, chatbot], [chatbot, msg])
    clear.click(lambda: ([], ""), outputs=[chatbot, msg])


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
