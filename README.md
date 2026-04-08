# LangGraph Agent Platform

A modular, production-ready multi-agent framework built with LangGraph and FastAPI.

Drop a file into `/agents` or `/tools` and the framework wires it in automatically — no manual graph editing required.

---

## Architecture

```
User Request
    │
    ▼
FastAPI  (/chat or /chat/stream)
    │  validates input (guardrails)
    │  resolves / creates session_id
    ▼
LangGraph StateGraph
    │
    ├─► router node  ──── LLM reads agent descriptions, picks best agent
    │       │                sets { active_agent: "search" } in state
    │       ▼
    ├─► agent node   ──── binds only its declared tools, calls LLM
    │       │
    │       ├── tool_calls? ──► tools node  ──► back to same agent
    │       │
    │       └── done ──────────────────────────► END
    │
    ▼
Response  (validates output, echoes session_id)
```

**Key design principles:**
- **Plugin architecture** — agents and tools are auto-discovered at startup via `pkgutil`
- **LLM-powered routing** — no hardcoded if/else; the router reasons from agent descriptions
- **Tool scoping** — each agent declares only the tools it needs; the LLM cannot call tools outside that set
- **Session memory** — in-process `MemorySaver` for FastAPI; `AgentCoreMemorySaver` for AWS Bedrock (same graph, different checkpointer)
- **Correct tool routing** — after tool execution, state tracks `active_agent` so results return to the exact agent that made the call
- **Observability** — every node is wrapped with an OpenTelemetry span
- **Guardrails** — input and output are validated before and after every request

---

## Quick Start

**Prerequisites:** Python ≥ 3.12, [uv](https://github.com/astral-sh/uv)

```bash
# 1. Clone and install
git clone https://github.com/hadrian89/langgraph-agent-framework.git
cd langgraph-agent-framework
uv sync

# 2. Configure
cp .env.example .env
# Edit .env — set OPENAI_API_KEY  (or switch to Ollama, see below)

# 3. Run
uv run uvicorn app.main:app --reload
```

Server starts at `http://localhost:8000`.

```bash
# New conversation
curl -X POST "http://localhost:8000/chat?query=What+is+the+capital+of+France"
# => { "response": "Paris...", "session_id": "3f4a..." }

# Continue the same conversation (pass session_id back)
curl -X POST "http://localhost:8000/chat?query=What+is+its+population&session_id=3f4a..."

# Stream a response (SSE)
curl "http://localhost:8000/chat/stream?query=Write+a+quicksort+in+Python"
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` or `ollama` |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `OLLAMA_MODEL` | `llama3.2` | Ollama model name |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `OTEL_ENDPOINT` | `http://localhost:4317` | OpenTelemetry collector endpoint |

**Run with local Ollama (no API key needed):**
```bash
LLM_PROVIDER=ollama uv run uvicorn app.main:app --reload
```

---

## API Reference

### `POST /chat`
Synchronous — waits up to 30 seconds for a complete response.

| Parameter | Type | Description |
|---|---|---|
| `query` | string | The user message |
| `session_id` | string (optional) | Resume an existing conversation |

```json
{ "response": "Paris is the capital of France.", "session_id": "3f4a1b2c-..." }
```

### `GET /chat/stream`
Server-Sent Events stream. Same parameters as `/chat`.
Session ID is returned in the `X-Session-Id` response header.

### `GET /health`
Returns `{ "status": "ok" }`.

---

## Adding a New Agent

1. Create `app/agents/my_agent.py`
2. Define the agent function and register it — that's it.

```python
# app/agents/my_agent.py
from app.core.agent_registry import AgentRegistry
from app.core.llm_gateway import LLMGateway
from app.core.tools_registry import ToolRegistry
from app.core.tracing import trace_node

_TOOLS = ["search"]  # declare only the tools this agent needs


@trace_node("my_agent")
def my_agent(state: dict) -> dict:
    llm = LLMGateway.get_model()
    tools = ToolRegistry.get_tools_by_names(_TOOLS)
    response = llm.bind_tools(tools).invoke(state["messages"])
    return {"messages": [response]}


AgentRegistry.register(
    name="my_agent",
    agent_fn=my_agent,
    description="One clear sentence describing what requests this agent handles",
    tools=_TOOLS,
)
```

The framework auto-discovers the file at startup — no other changes required.

---

## Adding a New Tool

1. Create `app/tools/my_tool.py`
2. Write a plain Python callable with a docstring and register it.

```python
# app/tools/my_tool.py
import requests
from app.core.tools_registry import ToolRegistry


def fetch_exchange_rate(currency_pair: str) -> str:
    """
    Fetch the current exchange rate for a currency pair such as USD/EUR.
    Returns a one-line string with the current rate.
    """
    # ... your implementation ...
    return "1 USD = 0.92 EUR"


ToolRegistry.register("exchange_rate", fetch_exchange_rate)
```

Then declare it in any agent that needs it: `tools=["exchange_rate"]`.

---

## Built-in Agents

| Agent | Description | Tools |
|---|---|---|
| `search` | Answers factual and real-time questions via web search | `search` (DuckDuckGo) |
| `weather` | Current weather conditions for any location | `weather` (wttr.in — no API key) |
| `coding` | Writes, explains, and debugs code in any language | none |

---

## Observability

Every agent and the router emits an OpenTelemetry span via the `@trace_node` decorator.

```
agent_request
  └── router
  └── search_agent
        └── tool_execution (guarded_search)
        └── response_generation
```

Spans are exported to:
- **Console** — visible immediately in your terminal during development
- **OTLP** — sent to `OTEL_ENDPOINT` for Jaeger, Grafana Tempo, or any OpenTelemetry-compatible backend

---

## Deployment

### FastAPI (local / any cloud)
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Uses in-process `MemorySaver` — memory is retained for the lifetime of the server process.

### AWS Bedrock AgentCore (serverless, persistent memory)
```bash
# Deploy
agentcore deploy \
  --env OPENAI_API_KEY=$OPENAI_API_KEY \
  --env LLM_PROVIDER=openai \
  --env OPENAI_MODEL=gpt-4o-mini

# Invoke
agentcore invoke '{"prompt": "Who is the PM of India?"}'

# Continue a session
agentcore invoke '{"prompt": "When did he take office?", "session_id": "abc-123"}'
```
Uses `AgentCoreMemorySaver` — conversation memory persists across invocations and server restarts.

**Invoke via curl:**
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Who is the PM of India?"}'
```

---

## Running Tests

```bash
uv run pytest tests/ -v
```

Test coverage: guardrails, agent registry, tool registry, LLM router (mocked LLM — no API key needed), graph construction, and session memory persistence.

---

## Development

```bash
# Install with dev dependencies
uv sync --group dev

# Set up pre-commit hooks (black, isort, flake8, pylint)
pre-commit install

# Run linting manually
pre-commit run --all-files
```

---

## Tech Stack

| Layer | Library |
|---|---|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM abstraction | [LangChain](https://github.com/langchain-ai/langchain) |
| API server | [FastAPI](https://fastapi.tiangolo.com) + [uvicorn](https://www.uvicorn.org) |
| LLM providers | OpenAI, Ollama |
| Observability | [OpenTelemetry](https://opentelemetry.io) |
| Serverless deploy | [AWS Bedrock AgentCore](https://aws.amazon.com/bedrock) |
| Dependency management | [uv](https://github.com/astral-sh/uv) |

---

## License

MIT
