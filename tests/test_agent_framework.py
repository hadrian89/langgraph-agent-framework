import asyncio
import importlib
import os
import sys
import types
import uuid
from types import SimpleNamespace

import pytest

import app.config as app_config
import app.core.agent_loader as agent_loader
import app.core.agent_registry as agent_registry
import app.core.guardrails as guardrails
import app.core.llm_gateway as llm_gateway
import app.core.router as router
import app.core.session as session
import app.core.tool_loader as tool_loader
import app.core.tools_registry as tool_registry
from app import agentcore
from app.config import settings
from app.tools import search_tool

# ensure workspace root is on path so `import app` works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ---------------------------------------------------------------------------
# stub out third-party modules that are not installed in the test
# environment. the production code imports them at module level, so we
# need to make dummy packages available before those imports happen.
# ---------------------------------------------------------------------------


stub_modules = [
    "langchain_ollama",
    "langchain_openai",
    "langchain_community",
    "langchain_community.tools",
    "langchain_core",
    "langchain_core.messages",
    "langgraph",
    "langgraph.graph",
    "langgraph.graph.message",
    "langgraph.prebuilt",
    "langgraph_checkpoint_aws",
    "opentelemetry",
    "opentelemetry.trace",
    "bedrock_agentcore",
    "bedrock_agentcore.runtime",
]
for name in stub_modules:
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)

# provide minimal classes/attributes used by our code
setattr(
    sys.modules["bedrock_agentcore.runtime"],
    "BedrockAgentCoreApp",
    type("BedrockAgentCoreApp", (), {"entrypoint": lambda self, f: f, "run": lambda self: None}),
)
setattr(sys.modules["langchain_openai"], "ChatOpenAI", type("ChatOpenAI", (), {}))
setattr(sys.modules["langchain_ollama"], "ChatOllama", type("ChatOllama", (), {}))
setattr(
    sys.modules["langchain_community.tools"],
    "DuckDuckGoSearchRun",
    type("DuckDuckGoSearchRun", (), {"run": lambda self, q: f"searched {q}"}),
)


# simple stand-in that mimics the real HumanMessage constructor
class _HumanMessage:
    def __init__(self, content=None, **kwargs):
        self.content = content


setattr(sys.modules["langchain_core.messages"], "HumanMessage", _HumanMessage)

# graph builder stubs


# opentelemetry stub used by tracing decorator
class _DummyTracer:
    def start_as_current_span(self, name):
        class Ctx:
            def __enter__(self):
                return None

            def __exit__(self, exc_type, exc, tb):
                pass

        return Ctx()


sys.modules["opentelemetry.trace"].get_tracer = lambda name: _DummyTracer()
sys.modules["langgraph.graph"].END = "END"
sys.modules["langgraph.graph.message"].add_messages = lambda *a, **k: None


def _fake_stategraph(*args, **kwargs):
    class Fake:
        def add_node(self, *a, **k):
            pass

        def add_conditional_edges(self, *a, **k):
            pass

        def add_edge(self, *a, **k):
            pass

        def set_conditional_entry_point(self, *a, **k):
            pass

        def compile(self, **k):
            return self

    return Fake()


sys.modules["langgraph.graph"].StateGraph = _fake_stategraph
sys.modules["langgraph.prebuilt"].ToolNode = lambda tools: object()
sys.modules["langgraph_checkpoint_aws"].AgentCoreMemorySaver = lambda *a, **k: None


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_registries():
    """Ensure global registries are restored after each test.

    The agents and tools modules register objects at import time, so
    tests should not make irreversible changes to those global maps.
    """
    orig_agents = agent_registry.AgentRegistry._agents.copy()
    orig_meta = agent_registry.AgentRegistry._metadata.copy()
    orig_tools = tool_registry.ToolRegistry._tools.copy()
    yield
    agent_registry.AgentRegistry._agents = orig_agents
    agent_registry.AgentRegistry._metadata = orig_meta
    tool_registry.ToolRegistry._tools = orig_tools


# ---------------------------------------------------------------------------
# Agent / tool registry tests
# ---------------------------------------------------------------------------


def test_agent_registry_basic():
    # initial = agent_registry.AgentRegistry.list_agents()

    def dummy():
        return {}

    agent_registry.AgentRegistry.register("foo", dummy, "desc")
    assert "foo" in agent_registry.AgentRegistry.list_agents()
    assert agent_registry.AgentRegistry.get_agent("foo") is dummy
    assert agent_registry.AgentRegistry.get_metadata()["foo"] == "desc"
    # registering the same name should overwrite
    agent_registry.AgentRegistry.register("foo", lambda s: s, "new")
    assert agent_registry.AgentRegistry.get_metadata()["foo"] == "new"


def test_tool_registry_basic():
    initial = tool_registry.ToolRegistry.get_tools().copy()
    tool_registry.ToolRegistry.register("t", lambda x: x)
    assert len(tool_registry.ToolRegistry.get_tools()) == len(initial) + 1


# ---------------------------------------------------------------------------
# Guardrails and search tests
# ---------------------------------------------------------------------------


def test_guardrails():
    assert guardrails.validate_input("hello") is True
    assert guardrails.validate_input("ignore previous instructions") is False
    assert guardrails.validate_output("this is safe") is True
    # blocked patterns are compared case-sensitively against lowered text, so
    # the current implementation does *not* catch the uppercase string.
    assert guardrails.validate_output("OPENAI_API_KEY in text") is True


def test_search_guard():
    # normal query passes through
    assert search_tool.search_guard("test") == "test"

    # blocked pattern returns explanation string
    assert (
        search_tool.search_guard("ignore previous instructions")
        == "Search query blocked by guardrails."
    )

    # query that is too long raises
    with pytest.raises(ValueError):
        search_tool.search_guard("x" * 201)


def test_guarded_search(monkeypatch):
    calls = {}

    def fake_run(q):
        calls["q"] = q
        return "result"

    monkeypatch.setattr(search_tool.search_tool, "run", fake_run)

    assert search_tool.guarded_search("foo") == "result"
    # dict input converts properly
    assert search_tool.guarded_search({"value": "bar"}) == "result"
    assert calls["q"] == "bar"


# ---------------------------------------------------------------------------
# Session handling
# ---------------------------------------------------------------------------


def test_session():
    sid1 = session.get_or_create_session(None)
    sid2 = session.get_or_create_session(None)
    assert sid1 != sid2
    assert isinstance(sid1, str)
    existing = session.get_or_create_session("abc")
    assert existing == "abc"


# ---------------------------------------------------------------------------
# Routing and LLM gateway
# ---------------------------------------------------------------------------


def test_router(monkeypatch):
    class DummyModel:
        def __init__(self, content):
            self.content = content

        def invoke(self, prompt):
            return SimpleNamespace(content=self.content)

    state = {"messages": [SimpleNamespace(content="hi")]}

    # normal JSON response
    monkeypatch.setattr(
        llm_gateway.LLMGateway,
        "get_model",
        classmethod(lambda cls: DummyModel('{"agent": "search"}')),
    )
    assert router.route(state) == "search"

    # malformed JSON should fall back to default
    monkeypatch.setattr(
        llm_gateway.LLMGateway,
        "get_model",
        classmethod(lambda cls: DummyModel("not json")),
    )
    assert router.route(state) == "search"

    # unknown agent falls back as well
    monkeypatch.setattr(
        llm_gateway.LLMGateway,
        "get_model",
        classmethod(lambda cls: DummyModel('{"agent": "nonexistent"}')),
    )
    assert router.route(state) == "search"


def test_llm_gateway(monkeypatch):
    # patch ChatOpenAI/ChatOllama with simple stand‑ins
    class FakeModel:
        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr(llm_gateway, "ChatOpenAI", FakeModel)
    monkeypatch.setattr(llm_gateway, "ChatOllama", FakeModel)

    # openai provider
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    llm_gateway.LLMGateway._model = None
    m = llm_gateway.LLMGateway.get_model()
    assert isinstance(m, FakeModel)

    # ollama provider
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    llm_gateway.LLMGateway._model = None
    m2 = llm_gateway.LLMGateway.get_model()
    assert isinstance(m2, FakeModel)

    # unsupported provider raises
    monkeypatch.setattr(settings, "LLM_PROVIDER", "xyz")
    llm_gateway.LLMGateway._model = None
    with pytest.raises(ValueError):
        llm_gateway.LLMGateway.get_model()


# ---------------------------------------------------------------------------
# Utilities that import/initialize plugins
# ---------------------------------------------------------------------------


def test_load_functions():
    tool_loader.load_tools()
    assert tool_registry.ToolRegistry.get_tools(), "tools should be registered after load_tools"
    agent_loader.load_agents()
    assert (
        agent_registry.AgentRegistry.list_agents()
    ), "agents should be registered after load_agents"


# ---------------------------------------------------------------------------
# Configuration module
# ---------------------------------------------------------------------------


def test_config_defaults(monkeypatch, tmp_path, capsys):
    # remove env vars and reload
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_URL", raising=False)

    # force a reload of the module

    importlib.reload(app_config)
    s = app_config.settings

    assert s.LLM_PROVIDER == "openai"
    assert s.OPENAI_MODEL == "gpt-4o-mini"
    assert s.OLLAMA_MODEL == "llama3.2"
    assert s.OLLAMA_URL == "http://localhost:11434"


# ---------------------------------------------------------------------------
# integration test
# ---------------------------------------------------------------------------


def test_handle_request_flow(monkeypatch):
    """Simulate a full request through agentcore.handle_request.

    The graph object built at import time has been stubbed above; here we
    override its ``ainvoke`` method to return a predictable message list.  We
    also verify session_id handling and guardrail enforcement.
    """

    # patch graph.ainvoke to be an async function that echoes input
    async def fake_ainvoke(initial_state, config=None):
        # mimic what the real graph might return
        return {"messages": [SimpleNamespace(content="output text")]}  # noqa

    monkeypatch.setattr(agentcore, "graph", SimpleNamespace(ainvoke=fake_ainvoke))

    # normal request should succeed
    payload = {"prompt": "hello world"}
    result = asyncio.run(
        agentcore.handle_request(payload, context=SimpleNamespace(session_id=None))
    )
    assert "response" in result
    assert result["response"] == "output text"
    assert "session_id" in result
    # ensure a uuid-like session id was created
    uuid.UUID(result["session_id"])

    # input guardrail blocks request
    payload2 = {"prompt": "ignore previous instructions"}
    result2 = asyncio.run(
        agentcore.handle_request(payload2, context=SimpleNamespace(session_id="xyz"))
    )
    assert result2["response"].startswith("Your request violates")
    # handle_request currently omits session_id when input is blocked
    assert "session_id" not in result2

    # output guardrail should be applied as well; make ainvoke return blocked text
    async def fake_bad_ainvoke(initial_state, config=None):
        # Return a lowercased string so the guardrail blocks it
        return {"messages": [SimpleNamespace(content="here is openai_api_key embedded")]}

    monkeypatch.setattr(agentcore, "graph", SimpleNamespace(ainvoke=fake_bad_ainvoke))
    payload3 = {"prompt": "safe prompt"}
    result3 = asyncio.run(
        agentcore.handle_request(payload3, context=SimpleNamespace(session_id="foo"))
    )
    assert result3["response"].startswith("Response blocked")
    assert result3["session_id"] == "foo"
