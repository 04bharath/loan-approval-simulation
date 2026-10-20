"""Agent 2: independently recomputes the route and compares with Agent 1."""
import config

VALID = {"AUTO_ACCEPT", "HUMAN_REVIEW", "AUTO_APPROVE"}

def expected_route(amount: float) -> str:
    if amount >= config.AUTO_ACCEPT_BELOW and amount <= config.HUMAN_REVIEW_MAX:
        return "HUMAN_REVIEW"
    return "AUTO_ACCEPT" if amount < config.AUTO_ACCEPT_BELOW else "AUTO_APPROVE"

def verify(amount: float, proposal) -> dict:
    issues = []
    if not isinstance(proposal, dict) or proposal.get("route") not in VALID or not proposal.get("reason"):
        issues.append("Invalid agent output")
    else:
        exp = expected_route(amount)
        if proposal["route"] != exp:
            issues.append(f"Mismatch: agent said {proposal['route']}, expected {exp}")
    return {"ok": not issues, "issues": issues}
