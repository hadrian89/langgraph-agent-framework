# Agentic AI Framework + Personal Health Assistant

## System Architecture Documentation

Author: Abhinav Srivastav
Stack: Python, LangGraph, LangChain, FastAPI, PostgreSQL, Ollama, AWS Bedrock AgentCore

---

# 1. System Overview

This project implements a **production-ready agentic AI framework** designed to:

• orchestrate multiple AI agents
• dynamically route user requests
• integrate external tools and APIs
• deploy to cloud runtimes (AWS Bedrock AgentCore)

The framework currently powers a **Personal AI Health Assistant** that integrates wearable health data.

---

# 2. High-Level Architecture

```id="arch001"
                ┌────────────────────┐
                │        User        │
                │  Web / Mobile App  │
                └─────────┬──────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   FastAPI API    │
                 │ /chat /stream    │
                 └────────┬─────────┘
                          │
                          ▼
               ┌─────────────────────┐
               │  Router Agent (LLM) │
               └────────┬────────────┘
                        │
        ┌───────────────┼─────────────────┐
        ▼               ▼                 ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Nutrition AI │ │ Activity AI  │ │ Sleep AI     │
└───────┬──────┘ └───────┬──────┘ └───────┬──────┘
        │                │                │
        ▼                ▼                ▼
     Tools            Tools           Tools
        │
        ▼
   External APIs
```

---

# 3. Core Technology Stack

| Layer               | Technology            |
| ------------------- | --------------------- |
| API                 | FastAPI               |
| Agent Orchestration | LangGraph             |
| LLM Interface       | LangChain             |
| Local LLM           | Ollama                |
| Database            | PostgreSQL            |
| Observability       | OpenTelemetry         |
| CI/CD               | GitHub Actions        |
| Cloud Runtime       | AWS Bedrock AgentCore |

---

# 4. Project Directory Structure

```id="arch002"
app/
│
├── main.py
│
├── api/
│   └── routes.py
│
├── agents/
│   ├── conversation_agent.py
│   ├── nutrition_agent.py
│   ├── activity_agent.py
│   ├── sleep_agent.py
│   └── health_assistant/
│        └── insight_agent.py
│
├── core/
│   ├── graph_builder.py
│   ├── router.py
│   ├── agent_registry.py
│   ├── tool_registry.py
│   ├── llm_gateway.py
│   ├── tracing.py
│   └── guardrails.py
│
├── tools/
│   └── search_tool.py
│
├── wearable/
│   └── fitbit_client.py
│
├── db/
│   ├── database.py
│   ├── models.py
│   └── db_init.py
│
├── repositories/
│   └── token_repository.py
│
└── services/
    └── wearable_service.py
```

---

# 5. LLM Gateway

Central interface for LLM access.

```id="arch003"
LLMGateway.get_model()
```

Supports switching between:

• Ollama
• OpenAI
• enterprise LLM gateways

Example usage:

```python
llm = LLMGateway.get_model()
response = llm.invoke(prompt)
```

Benefits:

• provider abstraction
• easy model switching
• centralized configuration

---

# 6. Agent Registry

Agents register themselves dynamically.

```python
AgentRegistry.register(
    name="nutrition",
    description="Diet recommendation agent",
    handler=nutrition_agent
)
```

Purpose:

• dynamic routing
• plugin architecture
• agent discovery

---

# 7. Tool Registry

Tools are shared utilities usable by any agent.

Example:

```python
ToolRegistry.register("search", DuckDuckGoSearchRun())
```

Tools may include:

• web search
• database access
• API calls
• wearable data retrieval

---

# 8. Router Agent

The router determines which agent should handle a request.

Prompt structure:

```id="arch004"
You are a routing engine.

Agents available:

search
nutrition
activity
sleep
conversation

Return JSON only.
```

Example response:

```json
{"agent":"nutrition"}
```

---

# 9. LangGraph Orchestration

Graph structure:

```id="arch005"
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

The graph is created in:

```
app/core/graph_builder.py
```

---

# 10. Observability

OpenTelemetry tracing added.

Tracked operations:

• router decisions
• agent execution
• tool usage
• LLM calls

This enables integration with:

• Langfuse
• Jaeger
• AWS monitoring

---

# 11. Guardrails

Input/output validation layer.

```python
validate_input(query)
validate_output(response)
```

Purpose:

• block unsafe prompts
• prevent sensitive data leakage
• enforce policy compliance

---

# 12. Streaming Responses

Streaming endpoint implemented.

```
/chat/stream
```

Allows real-time token streaming to UI.

---

# 13. Authentication

Authentication system uses:

```
AWS Cognito + JWT
```

Flow:

```id="arch006"
User login
  │
  ▼
Cognito authentication
  │
  ▼
JWT token
  │
  ▼
API request
  │
  ▼
JWT verification
```

---

# 14. Session Management

Sessions track conversation context.

Session table:

```sql
sessions
---------
session_id
user_id
created_at
```

LangGraph memory:

```python
config = {
 "configurable":{
  "thread_id": session_id
 }
}
```

---

# 15. Database Schema

### Users

```sql
users
-----
id
provider
created_at
```

---

### Wearable Tokens

```sql
wearable_tokens
---------------
user_id
provider
access_token
refresh_token
```

---

### Health Metrics

```sql
health_metrics
--------------
user_id
steps
sleep_hours
heart_rate
date
```

---

# 16. Fitbit Integration

OAuth PKCE flow implemented.

Login flow:

```id="arch007"
User login
  │
  ▼
Fitbit OAuth page
  │
  ▼
Redirect callback
  │
  ▼
Exchange code for token
  │
  ▼
Store tokens
```

User identity retrieved from:

```
/1/user/-/profile.json
```

Example:

```
BXZPNX
```

---

# 17. Health Assistant System

Agents for health management.

### Conversation Agent

General health Q&A.

### Nutrition Agent

Diet recommendations.

Factors:

• religion
• geography
• medical conditions

---

### Activity Agent

Exercise analysis.

---

### Sleep Agent

Sleep pattern analysis.

---

### Health Insight Agent

Detects trends in wearable data.

Examples:

```
sleep deficit
low activity
stress indicators
```

---

# 18. Example Health Insight

```id="arch008"
Sleep dropped below 6 hours
for the last 3 days.

Recommendation:
Sleep earlier tonight.
```

---

# 19. Proactive Health Assistant

Future goal:

Move from reactive chatbot to proactive AI coach.

Example:

```
Low activity detected today.
Consider a 15-minute walk.
```

---

# 20. Planned Integrations

Future wearable sources:

• Apple Health
• Garmin
• Google Fit

---

# 21. CI/CD Pipeline

GitHub Actions pipeline includes:

• black
• isort
• flake8
• pylint
• secret detection

Deployment pipeline:

```
GitHub → CodeBuild → AgentCore
```

---

# 22. AWS Bedrock AgentCore Deployment

Deployment flow:

```id="arch009"
Local Code
  │
  ▼
Docker Build
  │
  ▼
Push to ECR
  │
  ▼
CodeBuild
  │
  ▼
AgentCore Runtime
```

Agent entrypoint:

```
BedrockAgentCoreApp()
```

---

# 23. Current Development Status

Completed:

✔ agent framework
✔ dynamic routing
✔ tool system
✔ streaming responses
✔ observability
✔ guardrails
✔ CI/CD pipeline
✔ AWS AgentCore deployment
✔ Fitbit OAuth integration
✔ PostgreSQL persistence

---

# 24. Next Development Milestones

Upcoming priorities:

1. Fitbit data ingestion pipeline
2. Scheduled wearable data sync
3. Health trend detection engine
4. Notification system
5. Mobile health dashboard

---

# 25. Long-Term Vision

The system evolves into:

```
AI Personal Health Coach
```

Capabilities:

• wearable data analysis
• personalized health insights
• proactive lifestyle recommendations
• long-term behavioral learning

---

# End of Document
