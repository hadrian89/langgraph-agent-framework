"""
app/agents/health_assistant/insight_agent.py

Health Insight Agent — grounded in real Fitbit trend data.
Registered in agent_registry.py as "insight".

Uses your existing sync SessionLocal from app/db.py.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import SystemMessage

from app.core.llm_gateway import LLMGateway
from app.services.health.trend_detector import build_trend_report

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a personal AI health coach with access to the user's recent wearable data.

Your role:
- Identify health trends and explain them in plain language
- Give specific, actionable, encouraging recommendations
- Always note you are not a medical professional and clinical
  concerns should be discussed with a doctor

A health trend summary derived from the user's Fitbit data is
provided below. Ground your response in these real numbers.
"""


def insight_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node. Expects state keys: messages, user_id.

    Sync implementation matching your SessionLocal/get_db pattern.
    DB import is lazy to avoid circular imports during agent_loader startup.
    """
    user_id: str = state.get("user_id", "")
    messages: list = state.get("messages", [])

    # Lazy import — agent_loader.py imports this module at startup
    # before db.py is ready; top-level import would cause ImportError
    from app.db.getdb import SessionLocal  # noqa: PLC0415

    db = SessionLocal()
    try:
        trend_report = build_trend_report(user_id, db, lookback_days=7)
    finally:
        db.close()

    system = SystemMessage(content=f"{SYSTEM_PROMPT}\n\n{trend_report.to_agent_context()}")
    llm = LLMGateway.get_model()
    response = llm.invoke([system] + messages)

    logger.info("Insight agent | user=%s alerts=%d", user_id, len(trend_report.alerts))
    return {**state, "messages": messages + [response]}
