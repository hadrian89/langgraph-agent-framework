# AI Agent Framework + Health Assistant

## Project Context (LLM Continuation File)

Author: Abhinav Srivastav
Stack: Python, LangGraph, LangChain, FastAPI, PostgreSQL, Ollama, AWS Bedrock AgentCore

---

# 1. Project Purpose

Build a **production-ready multi-agent AI framework** capable of:

* routing requests to specialized agents
* using tools dynamically
* running locally or on cloud
* deploying to AWS Bedrock AgentCore

The framework is currently being extended to build a **Personal AI Health Assistant** that integrates wearable data (Fitbit).

---

# 2. Current Architecture

Core system uses **LangGraph orchestration**.

```
User
 │
 ▼
API (FastAPI)
 │
 ▼
Router Agent (LLM decision)
 │
 ▼
Specialized Agent
 │
 ▼
Tools / External APIs
 │
 ▼
LLM Response
```

---

# 3. Core Framework Components

## LLM Gateway

Centralized abstraction layer to switch models.

Supported:

* Ollama (local development)
* OpenAI (future production)

Location:

```
app/core/llm_gateway.py
```

Purpose:

* model switching
* unified configuration
* provider independence

---

## Agent Registry

Agents register dynamically.

Example:

```
AgentRegistry.register(
    name="nutrition",
    description="Provides diet recommendations",
    handler=nutrition_agent
)
```

Purpose:

* dynamic discovery
* routing support
* plugin architecture

---

## Tool Registry

Reusable tools shared across agents.

Example:

```
ToolRegistry.register("search", DuckDuckGoSearchRun())
```

Purpose:

* tool reuse
* centralized tool management

---

## Router Agent

Router decides which agent handles a query.

Prompt structure:

```
You are a routing engine.

Agents:
search
coding
nutrition
sleep
activity

Return JSON only.

Example:
{"agent": "nutrition"}
```

Router output determines graph path.

---

# 4. LangGraph Orchestration

Graph structure:

```
START
 │
 ▼
Router
 │
 ▼
Agent Node
 │
 ▼
Tool Node
 │
 ▼
END
```

Graph builder located at:

```
app/core/graph_builder.py
```

---

# 5. Observability

OpenTelemetry tracing added.

Tracks:

* router decisions
* agent execution
* tool calls

Supports integration with:

* Langfuse
* Jaeger
* AWS monitoring

---

# 6. Guardrails

Input/output validation implemented.

```
validate_input()
validate_output()
```

Purpose:

* block unsafe prompts
* prevent sensitive output
* enforce policy

---

# 7. Streaming Support

Streaming endpoint implemented:

```
/chat/stream
```

Allows real-time token streaming to UI.

---

# 8. Testing UI

Gradio UI built for testing.

Capabilities:

* interactive chat
* code formatting
* streaming display

---

# 9. CI/CD

GitHub Actions pipeline created.

Includes:

* black
* isort
* flake8
* pylint
* secret detection

Deployment automation:

```
GitHub → CodeBuild → AgentCore
```

---

# 10. Deployment Target

AWS Bedrock AgentCore runtime.

Deployment flow:

```
Local code
 → Docker build
 → ECR push
 → CodeBuild
 → AgentCore runtime
```

AgentCore entrypoint:

```
BedrockAgentCoreApp()
```

---

# 11. Authentication

System uses:

```
AWS Cognito + JWT
```

Purpose:

* secure agent invocation
* user identity
* session management

---

# 12. Session Memory

LangGraph conversation memory uses:

```
thread_id = session_id
```

Example:

```
config = {"configurable": {"thread_id": session_id}}
```

Allows multi-turn conversation memory.

---

# 13. Health Assistant Extension

Framework now powering a **Personal AI Health Assistant**.

Goal:

AI that monitors lifestyle and provides personalized health guidance.

---

# 14. Health Assistant Agents

### Conversation Agent

General health Q&A.

### Nutrition Agent

Diet advice.

Factors considered:

* religion
* geography
* medical conditions

### Sleep Agent

Sleep pattern analysis.

### Activity Agent

Exercise and movement analysis.

### Health Insight Agent

Detects patterns from wearable data.

Examples:

```
sleep deficit
sedentary lifestyle
overtraining
```

---

# 15. Wearable Integration

Current integration:

Fitbit API.

OAuth PKCE flow implemented.

Flow:

```
User login
 → Fitbit OAuth
 → callback
 → exchange code for token
 → store tokens
```

Tokens stored in database.

---

# 16. Database

PostgreSQL used.

Tables:

```
users
sessions
wearable_tokens
health_metrics
```

Example table:

```
wearable_tokens
---------------
user_id
provider
access_token
refresh_token
```

---

# 17. User Identity

Primary user identifier:

```
Fitbit encodedId
```

Example:

```
BXZPNX
```

Extracted from:

```
/1/user/-/profile.json
```

---

# 18. Session Flow

```
User login
 → Fitbit OAuth
 → get user profile
 → create session
```

Session table:

```
sessions
--------
session_id
user_id
created_at
```

API flow:

```
User request
 → session_id
 → resolve user_id
 → invoke LangGraph
```

State passed to agents:

```
{
  messages,
  user_id
}
```

---

# 19. Health Insight Engine

Agents analyze wearable metrics to detect trends.

Examples:

```
low sleep for multiple days
reduced activity
elevated heart rate
```

Agent generates recommendations.

Example:

```
Sleep dropped below 6 hours for 3 days.
Consider sleeping earlier tonight.
```

---

# 20. Planned Future Features

### Proactive Health Alerts

AI sends notifications based on trends.

---

### Personalized Diet Planning

Factors:

```
religion
geography
medical conditions
```

Example:

```
Vegetarian diabetic → low glycemic vegetarian meals
```

---

### Additional Wearable Integrations

Planned:

```
Apple Health
Garmin
Google Fit
```

---

### Long-Term Health Memory

AI learns user behavior over time.

Tracks:

```
sleep trends
activity levels
diet habits
```

---

# 21. Current Development Status

Completed:

✔ Agent framework
✔ Dynamic routing
✔ Tool system
✔ Observability
✔ Guardrails
✔ Streaming
✔ CI/CD pipeline
✔ AgentCore deployment
✔ Fitbit OAuth integration
✔ PostgreSQL persistence

---

# 22. Next Development Tasks

Next priorities:

1. Fitbit data ingestion pipeline
2. Automated wearable data sync
3. Health trend detection algorithms
4. Notification system
5. Mobile UI integration

---

# End of Context
