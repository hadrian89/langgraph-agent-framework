import time

import gradio as gr
import requests

STREAM_API_URL = "http://localhost:8000/chat/stream"
AGENTCORE_API_URL = "http://localhost:8080/invocations"
TRIGGER_TYPE = "agentcore"  # or "agentcore"
UI_SESSION_ID = ""


def format_code(text):

    if "def " in text or "import " in text:

        return f"```python\n{text}\n```"

    return text


def stream_agent(message):

    url = f"{STREAM_API_URL}?query={message}"

    response = requests.get(url, stream=True)

    partial = ""

    for chunk in response.iter_lines():

        if chunk:

            text = chunk.decode()

            if text.startswith("data:"):

                token = text.replace("data:", "").strip()

                partial += token + " "

                yield partial


def trigger_agent(message):
    global UI_SESSION_ID
    payload = {
        "prompt": message,
        "token": "YOUR_JWT_TOKEN_HERE",
        "session_id": UI_SESSION_ID,
    }
    print(f"Sending payload to AgentCore: {payload}")
    response = requests.post(AGENTCORE_API_URL, json=payload)

    if response.status_code == 200:
        print(f"AgentCore response: {response.json()}")

        UI_SESSION_ID = response.json().get("session_id", "")
        return response.json().get("response", "No response field in JSON")
    else:
        return f"Error: {response.status_code} - {response.text}"


def respond(message, history):

    start = time.time()

    history.append({"role": "user", "content": message})

    assistant_msg = {"role": "assistant", "content": ""}

    history.append(assistant_msg)

    if TRIGGER_TYPE == "stream":
        for partial in stream_agent(message):

            assistant_msg["content"] = format_code(partial)

            yield history, ""
    else:

        agresp = trigger_agent(message)
        assistant_msg["content"] = format_code(agresp)
        yield history, ""

    latency = round(time.time() - start, 2)

    assistant_msg["content"] += f"\n\n⏱️ Response time: {latency}s"

    yield history, ""


with gr.Blocks(
    theme=gr.themes.Soft(),
    css="""
#chatbot {
    height: 700px;
}
""",
) as demo:

    gr.Markdown("Agent Framework Demo - Powered by LangGraph and Bedrock AgentCore")

    chatbot = gr.Chatbot(
        elem_id="chatbot",
    )

    with gr.Row():

        msg = gr.Textbox(placeholder="Ask something...", scale=8, container=False)

        send = gr.Button("Send", scale=1)

    clear = gr.Button("Clear Chat")

    msg.submit(respond, [msg, chatbot], [chatbot, msg])

    send.click(respond, [msg, chatbot], [chatbot, msg])

    clear.click(lambda: [], None, chatbot)

    gr.Examples(
        examples=[
            "Who is PM of India?",
            "Write a python fibonacci program",
            "Explain LangGraph in simple terms",
            "Latest AI news",
        ],
        inputs=msg,
    )

demo.launch()
