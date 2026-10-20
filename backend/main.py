import hmac, sqlite3
from typing import Literal
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
import config, db, workflow

app = FastAPI(title="Simulated Loan Approval (no real money moves)")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
db.init_db()

class ApplicationIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    reference: str = Field(min_length=1, max_length=50)
    amount: float = Field(gt=0, le=1_000_000_000, allow_inf_nan=False)
    purpose: str = Field(default="", max_length=200)

class ReviewIn(BaseModel):
    reviewer: str = Field(min_length=1, max_length=100)
    decision: Literal["approve", "reject"]
    reason: str = Field(default="", max_length=300)

    @model_validator(mode="after")
    def need_reason(self):
        if self.decision == "reject" and not self.reason.strip():
            raise ValueError("Reason is required for rejection")
        return self

def fetch(app_id):
    with db.conn() as c:
        row = c.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Application not found")
        hist = [dict(h) for h in c.execute("SELECT status,reason,at FROM history WHERE app_id=? ORDER BY id", (app_id,))]
    return {**dict(row), "history": hist}

def require_reviewer(key):
    if not key:
        raise HTTPException(401, "Reviewer key required")
    if not hmac.compare_digest(key, config.REVIEWER_API_KEY):
        raise HTTPException(403, "Not an authorized reviewer")

@app.get("/health")
def health(): return {"status": "ok", "simulation": True}

@app.post("/applications", status_code=201)
def create(a: ApplicationIn):
    try:
        app_id = workflow.submit(a.name.strip(), a.reference.strip(), a.amount, a.purpose)
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Duplicate application reference")
    return fetch(app_id)

@app.get("/applications/{app_id}")
def get_one(app_id: str): return fetch(app_id)

@app.get("/review/pending")
def pending(x_reviewer_key: str | None = Header(default=None)):
    require_reviewer(x_reviewer_key)
    with db.conn() as c:
        rows = c.execute("SELECT * FROM applications WHERE status='PENDING_HUMAN_REVIEW' ORDER BY created_at").fetchall()
    return [dict(r) for r in rows]

@app.post("/review/{app_id}")
def review(app_id: str, r: ReviewIn, x_reviewer_key: str | None = Header(default=None)):
    require_reviewer(x_reviewer_key)
    cur = fetch(app_id)
    if r.reviewer.strip().lower() == cur["name"].strip().lower():
        raise HTTPException(403, "Applicants cannot review their own application")
    with db.conn() as c:
        status = "APPROVED" if r.decision == "approve" else "REJECTED"
        reason = r.reason.strip() or "Approved by reviewer (simulation)"
        # atomic guard: only a still-pending row can change -> blocks replays
        res = c.execute("UPDATE applications SET status=?, reason=?, reviewer=?, updated_at=? WHERE id=? AND status='PENDING_HUMAN_REVIEW'",
                        (status, reason, r.reviewer.strip(), workflow.now(), app_id))
        if res.rowcount == 0:
            raise HTTPException(409, "Application is not pending review")
        c.execute("INSERT INTO history(app_id,status,reason,at) VALUES(?,?,?,?)", (app_id, status, f"{r.reviewer}: {reason}", workflow.now()))
    return fetch(app_id)
