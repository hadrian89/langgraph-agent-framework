# LangGraph Agent Platform

A modular AI agent platform built with:

- FastAPI
- LangGraph
- LangChain
- Ollama / OpenAI
- OpenTelemetry
- uv dependency manager

## Features

- Multi-agent orchestration
- Dynamic agent registry
- Tool registry
- LLM-based routing
- Streaming responses
- OpenTelemetry tracing
- Ollama / OpenAI switching

---

## Architecture
User -> FastAPI API -> LangGraph Orchestrator -> Router -> Agent Registry -> Agents -> Tools

---

## Installation

### Install uv
```
curl -LsSf https://astral.sh/uv/install.sh
```

### Install dependencies
```
uv sync
```
---

## Run the server

```
uv run uvicorn app.main:app --reload
```

Server will run at:
```
http://localhost:8000
```

---

## API Endpoints

### Chat
POST /chat
Example:
```
curl "http://localhost:8000/chat?query=who%20is%20PM%20of%20India
```
POST /chat/stream
Example:
```
curl -N "http://localhost:8000/chat/stream?query=who%20is%20PM%20of%20India
```
---

## Supported LLMs

| Provider | Supported |
|--------|-----------|
| OpenAI | ✅ |
| Ollama | ✅ |

Switch via `.env`:
```
LLM_PROVIDER=ollama
```

---

## Observability

The platform supports OpenTelemetry tracing.

Example trace structure:
agent_request
=> router
=> search_agent
=> tool_execution
=> response_generation

---

## Adding New Agents

Create a new file in: app/agents/

Register the agent: AgentRegistry.register("weather", weather_agent)

The system automatically adds it to the graph.

---

## License

MIT

# authentication
# deployment EKS/Agentcore
# guardrails 
# Source - https://stackoverflow.com/a/7173011
# Posted by Sean Patrick Floyd, modified by community. See post 'Timeline' for change history
# Retrieved 2026-03-07, License - CC BY-SA 4.0

curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"prompt":"who is PM of India"}' \
  https://bedrock-agentcore.eu-west-2.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aeu-west-2%3A317112499880%3Aruntime%2Fagentaiframework-XtFV52GIZk/invocations?qualifier=DEFAULT

    http://localhost:8080/invocations