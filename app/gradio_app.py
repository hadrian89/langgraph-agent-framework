import requests
import gradio as gr
import time

API_URL = "http://localhost:8000/chat/stream"

def format_code(text):

    if "def " in text or "import " in text:

        return f"```python\n{text}\n```"

    return text

def stream_agent(message):

    url = f"{API_URL}?query={message}"

    response = requests.get(url, stream=True)

    partial = ""

    for chunk in response.iter_lines():

        if chunk:

            text = chunk.decode()

            if text.startswith("data:"):

                token = text.replace("data:", "").strip()

                partial += token + " "

                yield partial


def respond(message, history):

    start = time.time()

    history.append({"role": "user", "content": message})

    assistant_msg = {"role": "assistant", "content": ""}

    history.append(assistant_msg)

    for partial in stream_agent(message):

        assistant_msg["content"] = format_code(partial)
        yield history, ""
    
    latency = round(time.time() - start, 2)

    assistant_msg["content"] += f"\n\n⏱️ Response time: {latency}s"
    

    yield history, ""


with gr.Blocks(
    theme=gr.themes.Soft(),
    css="""
#chatbot {
    height: 600px;
}
"""
) as demo:

    gr.Markdown("# 🤖 LangGraph Agent Platform")

    chatbot = gr.Chatbot(
        elem_id="chatbot",
    )

    with gr.Row():

        msg = gr.Textbox(
            placeholder="Ask something...",
            scale=8,
            container=False
        )

        send = gr.Button("Send", scale=1)

    clear = gr.Button("Clear Chat")

    msg.submit(
        respond,
        [msg, chatbot],
        [chatbot, msg]
    )

    send.click(
        respond,
        [msg, chatbot],
        [chatbot, msg]
    )

    clear.click(
        lambda: [],
        None,
        chatbot
    )

    gr.Examples(
        examples=[
            "Who is PM of India?",
            "Write a python fibonacci program",
            "Explain LangGraph in simple terms",
            "Latest AI news"
        ],
        inputs=msg
    )

demo.launch()