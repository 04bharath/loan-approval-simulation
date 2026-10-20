# Loan Approval System (Two Agents + Human Review): SIMULATION

**This is a simulation. It does not connect to any bank, move money, or issue funds.** "Approved/accepted" only means a workflow outcome.

## Rules (backend/config.py)
- ₹0 < amount < ₹1,000 → reject
- ₹1,000–₹10,000 (inclusive) → pending human review
- > ₹10,000 → automatic approval path
- Invalid/missing/negative amounts → rejected with 422

## Agents
- `agents/approval_agent.py`: proposes a route + reason.
- `agents/monitoring_agent.py`: recomputes the route independently; on mismatch/invalid output the status becomes MONITORING_ERROR and auto-approval is blocked.

## Run backend
    cd backend
    python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    export REVIEWER_API_KEY=change-me                  # default: reviewer-demo-key
    uvicorn main:app --reload                          # http://localhost:8000/docs

## Run frontend
    cd frontend
    npm install
    npm run dev                                        # http://localhost:5173

## Tests
    cd backend && pytest

## Auth
Reviewer routes need header `X-Reviewer-Key`. Applicants have no key; a reviewer can't review an application under their own name. Replays get 409.
