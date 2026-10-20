import json, uuid
from datetime import datetime, timezone
import db
from agents import approval_agent, monitoring_agent

def now(): return datetime.now(timezone.utc).isoformat()

def set_status(c, app_id, status, reason, **extra):
    sets = "status=?, reason=?, updated_at=?" + "".join(f", {k}=?" for k in extra)
    c.execute(f"UPDATE applications SET {sets} WHERE id=?", (status, reason, now(), *extra.values(), app_id))
    c.execute("INSERT INTO history(app_id,status,reason,at) VALUES(?,?,?,?)", (app_id, status, reason, now()))

def submit(name, reference, amount, purpose):
    app_id = str(uuid.uuid4())
    with db.conn() as c:
        c.execute("INSERT INTO applications(id,name,reference,amount,purpose,status,reason,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                  (app_id, name, reference, amount, purpose, "SUBMITTED", "Received", now(), now()))
        c.execute("INSERT INTO history(app_id,status,reason,at) VALUES(?,?,?,?)", (app_id, "SUBMITTED", "Received", now()))
        proposal = approval_agent.decide(amount)                   # Agent 1
        check = monitoring_agent.verify(amount, proposal)          # Agent 2
        agent_json = json.dumps({"approval": proposal, "monitoring": check})
        if not check["ok"]:
            set_status(c, app_id, "MONITORING_ERROR", "; ".join(check["issues"]) + ". Automatic approval blocked.", agent_result=agent_json)
        else:
            status = {"AUTO_ACCEPT": "AUTO_ACCEPTED", "HUMAN_REVIEW": "PENDING_HUMAN_REVIEW", "AUTO_APPROVE": "AUTO_APPROVAL_PATH"}[proposal["route"]]
            set_status(c, app_id, status, proposal["reason"], agent_result=agent_json)
    return app_id
