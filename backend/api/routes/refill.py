import time
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.services.refill_parser import parse_pipeline
from backend.schemas.refill import RefillPipeline
import backend.api.deps as deps

router = APIRouter()

# Cache parsed pipeline at startup
_pipeline_cache: RefillPipeline | None = None


def get_pipeline() -> RefillPipeline:
    global _pipeline_cache
    if _pipeline_cache is None:
        _pipeline_cache = parse_pipeline()
    return _pipeline_cache


@router.get("/refill/pipeline")
async def get_refill_pipeline():
    pipeline = get_pipeline()
    # Transform backend schema → frontend-compatible format
    return {
        "markets": [
            {
                "name": market.name,
                "flag": market.flag,
                "currency": market.currency,
                "methods": [
                    {
                        "name": method.label,
                        "currency": market.currency,
                        "buy_service": method.buy_service,
                        "lightning_wallet": method.lightning_wallet,
                        "pipeline": method.pipeline_steps,
                        "total_time": f"{method.total_time_min}–{method.total_time_max} min",
                        "fees": method.fee_notes,
                        "kyc": method.kyc_required,
                        "risk": method.risk,
                        "status": "unconfirmed" if method.status == "partial" else method.status,
                        "evidence_url": method.evidence_urls[0] if method.evidence_urls else None,
                        "notes": " | ".join(filter(None, [method.gaps, method.workaround])) or None,
                    }
                    for method in market.methods
                ],
            }
            for market in pipeline.markets
        ],
        "last_updated": pipeline.source_file,
    }


class ScanRequest(BaseModel):
    market: Optional[str] = None


@router.post("/refill/scan")
async def trigger_refill_scan(req: ScanRequest):
    agent = deps.get_intelligence()
    if agent is None:
        return {
            "analysis": "Intelligence agent not available (API key not configured). Check CEREBRAS_API_KEY in .env",
            "scanned_at": time.time(),
        }
    scope = f"for {req.market}" if req.market else "for all markets"
    question = (
        f"Run a refill pipeline check {scope}. "
        "For each payment method, confirm the current best route to buy BTC and send it "
        "via Lightning to a Noones wallet. Flag any routes that need verification. "
        "Be concise and actionable."
    )
    try:
        answer = agent.ask(question)
        return {"analysis": answer, "scanned_at": time.time()}
    except Exception as e:
        return {"analysis": f"Agent error: {e}", "scanned_at": time.time()}
