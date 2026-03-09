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
# Pre commit hooks
```
pre-commit run --all-files
```

# To run with agentcore
```
agentcore dev
```
## To test with agentcore
curl command
```
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"prompt":"who is PM of India"}' \
  http://localhost:8080/invocations
```
curl with memory
```
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"prompt":"how many times he become PM?","session_id": "a8089a3f-6e2d-4088-8ebb-cade809d1dfe"}' \
  http://localhost:8081/invocations
```
---
with Agentcore invoke command
```
agentcore invoke '{"prompt": "who is PM of India?"}' \
  --bearer-token "$TOKEN" \
  --session-id "demo_session_$(uuidgen | tr -d '-')"          
```
with session
```
agentcore invoke '{"prompt": "how many times he became a PM?"}' \                     
  --bearer-token "$TOKEN" \                                   
  --session-id "demo_session_D9F757C9E7C5414D897EDF273BA6DA0C"
```

## License

MIT
<!-- https://bedrock-agentcore.eu-west-2.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aeu-west-2%3A317112499880%3Aruntime%2Fagentaiframework-XtFV52GIZk/invocations?qualifier=DEFAULT -->

<!-- agent with identity setup
# 1. Create Cognito pools
agentcore identity setup-cognito

# 2. Load environment variables
export $(grep -v '^#' .agentcore_identity_user.env | xargs)

# 3. Configure agent with JWT auth
agentcore configure \
  -e app/agentcore.py \
  --name myagentwithidentity \
  --authorizer-config '{
    "customJWTAuthorizer": {
      "discoveryUrl": "'$RUNTIME_DISCOVERY_URL'",
      "allowedClients": ["'$RUNTIME_CLIENT_ID'"]
    }
  }' \
  --disable-memory

# 4. Create credential provider
agentcore identity create-credential-provider \
  --name MyServiceProvider \
  --type cognito \
  --client-id $IDENTITY_CLIENT_ID \
  --client-secret $IDENTITY_CLIENT_SECRET \
  --discovery-url $IDENTITY_DISCOVERY_URL \
  --cognito-pool-id $IDENTITY_POOL_ID

# 5. Create workload identity
agentcore identity create-workload-identity \
  --name my-agent-workload
# 6. Deploy agent
agentcore deploy

# 7. Get bearer token for Runtime auth
TOKEN=$(agentcore identity get-cognito-inbound-token)

# 8. Invoke with JWT authentication
agentcore invoke '{"prompt": "who is PM of India?"}' \
  --bearer-token "$TOKEN" \
  --session-id "demo_session_$(uuidgen | tr -d '-')" 
  
  
agentcore invoke '{"prompt": "how many times he became a PM?"}' \
  --bearer-token "$TOKEN" \
  --session-id "demo_session_D9F757C9E7C5414D897EDF273BA6DA0C"

-->

<!-- To generate a token use below

export $(grep -v '^#' .agentcore_identity_user.env | xargs)

TOKEN=$(agentcore identity get-cognito-inbound-token)

agentcore deploy \
          --env OPENAI_API_KEY=<OPENAI_API_KEY> \
          --env LLM_PROVIDER=openai \
          --env OPENAI_MODEL=gpt-4o-mini \
          --env OLLAMA_MODEL=llama3.2
-->
