import time
import os
from fastapi import APIRouter
from pydantic import BaseModel
import backend.api.deps as deps

router = APIRouter()


class AskRequest(BaseModel):
    question: str


@router.post("/intelligence/ask")
async def ask_intelligence(req: AskRequest):
    agent = deps.get_intelligence()
    if agent is None:
        return {
            "answer": "Intelligence agent not configured. Set CEREBRAS_API_KEY in .env",
            "duration_ms": 0,
        }
    t0 = time.time()
    try:
        answer = agent.ask(req.question)
        return {"answer": answer, "duration_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {"answer": f"Error: {e}", "duration_ms": 0}


@router.post("/intelligence/research")
async def research(req: AskRequest):
    """Use Anthropic API (Claude) for deep web research queries."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"answer": "ANTHROPIC_API_KEY not set in .env", "duration_ms": 0}
    t0 = time.time()
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": req.question}],
            system=(
                "You are a Bitcoin P2P trading research assistant for CryptoDistro 2.0. "
                "The operator buys BTC on Binance and sells at a premium in emerging markets "
                "(Nigeria, Argentina, Venezuela, Kenya, Sweden) via Noones. "
                "Answer concisely with specific, actionable insights."
            ),
        )
        answer = msg.content[0].text
        return {"answer": answer, "duration_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {"answer": f"Anthropic API error: {e}", "duration_ms": 0}
