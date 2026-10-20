"""Agent 1: proposes a route. SIMULATION ONLY - never moves money."""
import config

def decide(amount: float) -> dict:
    if amount < config.AUTO_ACCEPT_BELOW:
        return {"route": "AUTO_ACCEPT", "reason": f"Amount below {config.AUTO_ACCEPT_BELOW}: automatic acceptance path."}
    if amount <= config.HUMAN_REVIEW_MAX:
        return {"route": "HUMAN_REVIEW", "reason": "Medium amount: human review required."}
    return {"route": "AUTO_APPROVE", "reason": f"Amount above {config.HUMAN_REVIEW_MAX}: automatic approval path."}
