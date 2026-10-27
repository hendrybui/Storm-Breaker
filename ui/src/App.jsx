import React, { useCallback, useEffect, useMemo, useState } from "react";
import { TABS } from "./tabs.js";
import { get, post } from "./api.js";

/* ---------------- generic renderers (used by the data tabs) -------------- */

function Cell({ value }) {
  if (value === null || value === undefined) return <span className="dim">—</span>;
  if (typeof value === "object") return <span className="mono">{JSON.stringify(value)}</span>;
  const text = String(value);
  return <span title={text}>{text.length > 80 ? text.slice(0, 80) + "…" : text}</span>;
}

function Table({ rows }) {
  const cols = useMemo(
    () => [...new Set(rows.flatMap((r) => Object.keys(r || {})))].slice(0, 8),
    [rows]
  );
  return (
    <div className="scroll">
      <table>
        <thead>
          <tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.slice(0, 100).map((r, i) => (
            <tr key={i}>{cols.map((c) => <td key={c}><Cell value={r?.[c]} /></td>)}</tr>
          ))}
        </tbody>
      </table>
      {rows.length > 100 && <div className="dim pad">showing 100 of {rows.length}</div>}
    </div>
  );
}

function Value({ value }) {
  if (Array.isArray(value)) {
    if (value.length && typeof value[0] === "object") return <Table rows={value} />;
    return (
      <div className="chips">
        {value.length ? value.map((v, i) => <span className="chip" key={i}>{String(v)}</span>)
          : <span className="dim">empty</span>}
      </div>
    );
  }
  if (value && typeof value === "object") return <pre>{JSON.stringify(value, null, 2)}</pre>;
  return <div className="scalar">{String(value)}</div>;
}

function EndpointCard({ path }) {
  const [state, setState] = useState({ loading: true });
  const load = useCallback(() => {
    setState({ loading: true });
    get(path).then(
      (data) => setState({ loading: false, data }),
      (err) => setState({ loading: false, error: String(err.message || err) })
    );
  }, [path]);
  useEffect(load, [load]);

  const entries = state.data && typeof state.data === "object"
    ? Object.entries(state.data).slice(0, 6)
    : [["value", state.data]];

  return (
    <section className="card">
      <header className="card-head">
        <code>{path}</code>
        <button className="ghost" onClick={load}>↻</button>
      </header>
      <div className="card-body">
        {state.loading && <div className="dim">loading…</div>}
        {state.error && <div className="err">{state.error}</div>}
        {state.data !== undefined && entries.map(([k, v]) => (
          <div className="field" key={k}>
            <div className="field-label">{k}</div>
            <Value value={v} />
          </div>
        ))}
      </div>
    </section>
  );
}

/* ------------------------------- live tab -------------------------------- */

function LiveTab() {
  const [events, setEvents] = useState([]);
  const [snapshot, setSnapshot] = useState({ listeners: [], beacons: [], subscribers: 0 });
  const [status, setStatus] = useState("connecting");

  const refresh = useCallback(() => {
    get("/api/live").then(setSnapshot, () => {});
  }, []);

  useEffect(() => {
    refresh();
    const es = new EventSource("/api/events");
    const onEvent = (msg) => {
      const ev = JSON.parse(msg.data);
      setEvents((prev) => [ev, ...prev].slice(0, 60));
      refresh();
    };
    ["beacon", "listener", "strike"].forEach((k) => es.addEventListener(k, onEvent));
    es.onopen = () => setStatus("live");
    es.onerror = () => setStatus("reconnecting");
    const timer = setInterval(refresh, 10000);
    return () => { es.close(); clearInterval(timer); };
  }, [refresh]);

  const describe = (e) =>
    e.kind === "beacon" ? `${e.uid} beacon (${e.expected_ms}ms)`
      : e.kind === "listener" ? `${e.peer}:${e.peer_port} → ${e.host}:${e.port}`
        : e.kind === "strike" ? `${e.payload_type} → ${e.target} callback=${e.callback_ok ? "VERIFIED" : "NO"}`
          : JSON.stringify(e);

  return (
    <div className="grid2">
      <section className="card">
        <header className="card-head">
          <span>Live event stream</span>
          <span className="dim small">subscribers: {snapshot.subscribers} · <b>{status}</b></span>
        </header>
        <div className="card-body scroll tall">
          {events.length === 0 && <div className="dim">waiting for events…</div>}
          {events.map((e, i) => (
            <div className="evrow" key={i}>
              <span className={"kind " + e.kind}>{e.kind}</span>
              <span className="flex1">{describe(e)}</span>
              <span className="dim">{(e.at || "").slice(11, 19)}</span>
            </div>
          ))}
        </div>
      </section>
      <div className="stack">
        <section className="card">
          <header className="card-head"><span>Listeners</span></header>
          <div className="card-body">
            {snapshot.listeners.length === 0 && <div className="dim">no listeners</div>}
            {snapshot.listeners.map((l) => (
              <div className="mono small" key={l.name}>
                {l.name} :{l.port} <b className="ok">{l.connections} conn</b>
              </div>
            ))}
          </div>
        </section>
        <section className="card">
          <header className="card-head"><span>Observed beacons</span></header>
          <div className="card-body">
            {snapshot.beacons.length === 0 && <div className="dim">no beacons observed</div>}
            {snapshot.beacons.map((b) => (
              <div className="mono small" key={b.uid}>
                {b.uid} <b className="ok">{b.count} beacons</b>
                {b.interval_ms ? <span className="dim"> ~{b.interval_ms}ms</span> : null}
                {b.missed ? <span className="err"> {b.missed} missed</span> : null}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

/* ------------------------------ strike panel ----------------------------- */

function StrikeBar() {
  const [out, setOut] = useState(null);
  const [busy, setBusy] = useState(false);
  const run = () => {
    setBusy(true);
    post("/api/strike/reverse", { payload_type: "python_reverse" })
      .then((r) => setOut(r), (e) => setOut({ error: String(e) }))
      .finally(() => setBusy(false));
  };
  return (
    <div className="strikebar">
      <button className="primary" onClick={run} disabled={busy}>
        {busy ? "firing…" : "⚡ Fire python_reverse"}
      </button>
      {out && (
        <span className="small mono">
          {out.error ? <span className="err">{out.error}</span>
            : <span className={out.ok ? "ok" : "err"}>{out.summary}</span>}
        </span>
      )}
    </div>
  );
}

/* --------------------------------- shell --------------------------------- */

export default function App() {
  const [active, setActive] = useState("live");
  const [query, setQuery] = useState("");
  const tab = TABS.find((t) => t.id === active) || TABS[0];

  const shown = query
    ? TABS.filter((t) => t.label.toLowerCase().includes(query.toLowerCase()))
    : TABS;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <b>Storm-Breaker</b>
          <span className="dim small">V2 · {TABS.length} tabs</span>
        </div>
        <input
          className="search" placeholder="filter tabs…" value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="nav scroll">
          {shown.map((t) => (
            <button
              key={t.id}
              className={"navitem" + (t.id === active ? " active" : "")}
              onClick={() => setActive(t.id)}
            >
              <span className="ic">{t.icon}</span>{t.label}
              {t.custom === "live" && <span className="dot" />}
            </button>
          ))}
        </div>
        <a className="legacy" href="/panel">← legacy panel</a>
      </aside>

      <main className="content">
        <header className="topbar">
          <h1>{tab.icon} {tab.label}</h1>
          <StrikeBar />
        </header>
        <div className="panes">
          {tab.custom === "live" ? <LiveTab /> : (
            tab.endpoints.length
              ? <div className="stack">{tab.endpoints.map((p) => <EndpointCard key={p} path={p} />)}</div>
              : <div className="card"><div className="card-body dim">
                  This tab is generated by the frozen module UI (no JSON endpoint yet).
                </div></div>
          )}
        </div>
      </main>
    </div>
  );
}
