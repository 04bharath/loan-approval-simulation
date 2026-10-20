import { useState, useEffect } from "react";
const API = "http://localhost:8000";
const LABELS = { AUTO_ACCEPTED: "Automatic acceptance", PENDING_HUMAN_REVIEW: "Pending human approval",
  AUTO_APPROVAL_PATH: "Automatic approval path", APPROVED: "Approved by reviewer", REJECTED: "Rejected", MONITORING_ERROR: "Monitoring error" };
const Badge = ({ s }) => <span className={`badge ${s}`}>{LABELS[s] || s}</span>;
async function call(path, opts) {
  const r = await fetch(API + path, opts);
  const d = await r.json();
  if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : "Invalid input");
  return d;
}

export default function App() {
  const [form, setForm] = useState({ name: "", reference: "", amount: "", purpose: "" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [key, setKey] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [pending, setPending] = useState([]);
  const [msg, setMsg] = useState("");

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  async function submit(e) {
    e.preventDefault(); setLoading(true); setError("");
    try {
      setResult(await call("/applications", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, amount: Number(form.amount) }) }));
    } catch (err) { setError(err.message); }
    setLoading(false);
  }
  async function refresh() { if (result) setResult(await call(`/applications/${result.id}`)); }
  useEffect(() => { // auto-refresh while pending
    if (result?.status !== "PENDING_HUMAN_REVIEW") return;
    const t = setInterval(refresh, 5000); return () => clearInterval(t);
  }, [result]);
  async function loadPending() {
    try { setPending(await call("/review/pending", { headers: { "X-Reviewer-Key": key } })); setMsg(""); }
    catch (err) { setMsg(err.message); }
  }
  async function decide(id, decision) {
    let reason = "";
    if (decision === "reject") { reason = prompt("Reason for rejection (required):") || ""; if (!reason) return; }
    try {
      await call(`/review/${id}`, { method: "POST", headers: { "Content-Type": "application/json", "X-Reviewer-Key": key },
        body: JSON.stringify({ reviewer, decision, reason }) });
      loadPending();
    } catch (err) { setMsg(err.message); }
  }

  return (<main>
    <h1>Loan Approval System <small>Simulation only: no money is disbursed</small></h1>
    <div className="grid">
      <section className="card">
        <h2>Apply</h2>
        <form onSubmit={submit}>
          <input placeholder="Applicant name" value={form.name} onChange={set("name")} required />
          <input placeholder="Application reference" value={form.reference} onChange={set("reference")} required />
          <input type="number" step="0.01" placeholder="Amount (₹)" value={form.amount} onChange={set("amount")} required />
          <input placeholder="Purpose (optional)" value={form.purpose} onChange={set("purpose")} />
          <button disabled={loading}>{loading ? "Submitting…" : "Submit"}</button>
        </form>
        {error && <p className="err">{error}</p>}
        {result && <div className="result">
          <Badge s={result.status} />
          <p><b>ID:</b> {result.id}</p><p><b>Amount:</b> ₹{result.amount}</p>
          <p><b>Reason:</b> {result.reason}</p>
          <p><b>Next:</b> {result.status === "PENDING_HUMAN_REVIEW" ? "Waiting for a reviewer (auto-refreshes)." : "No further action. Simulation: no funds issued."}</p>
          <button className="ghost" onClick={refresh}>Refresh status</button>
        </div>}
      </section>
      <section className="card">
        <h2>Reviewer dashboard</h2>
        <input type="password" placeholder="Reviewer key" value={key} onChange={(e) => setKey(e.target.value)} />
        <input placeholder="Your reviewer name" value={reviewer} onChange={(e) => setReviewer(e.target.value)} />
        <button onClick={loadPending}>Load pending</button>
        {msg && <p className="err">{msg}</p>}
        {pending.map((p) => <div key={p.id} className="item">
          <b>{p.name}</b> · ₹{p.amount} · ref {p.reference}<br /><small>{p.purpose}</small>
          <div className="row"><button onClick={() => decide(p.id, "approve")}>Approve</button>
            <button className="danger" onClick={() => decide(p.id, "reject")}>Reject</button></div>
        </div>)}
      </section>
    </div>
  </main>);
}
