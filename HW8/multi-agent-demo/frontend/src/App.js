import React, { useState, useEffect, useRef, useCallback } from "react";

/* ────────────────────────────────────────────────────────────
   AGENT METADATA
   ──────────────────────────────────────────────────────────── */
const AGENTS = [
  { id: "researcher", name: "Researcher", emoji: "", color: "#06b6d4", x: 0 },
  { id: "analyst",    name: "Analyst",    emoji: "", color: "#8b5cf6", x: 1 },
  { id: "writer",     name: "Writer",     emoji: "", color: "#f59e0b", x: 2 },
  { id: "reviewer",   name: "Reviewer",   emoji: "", color: "#10b981", x: 3 },
];

const TOPICS = [
  "agent-tasks", "agent-research", "agent-analysis",
  "agent-writing", "agent-review"
];

/* ────────────────────────────────────────────────────────────
   MAIN APP
   ──────────────────────────────────────────────────────────── */
export default function App() {
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const [agentStates, setAgentStates] = useState({});
  const [outputs, setOutputs] = useState({});
  const [taskTopic, setTaskTopic] = useState("The future of multi-agent AI systems");
  const [activePulse, setActivePulse] = useState(null);
  const [pipelineComplete, setPipelineComplete] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const wsRef = useRef(null);
  const logRef = useRef(null);

  // ── WebSocket ─────────────────────────────────────────
  useEffect(() => {
    let ws;
    let reconnectTimer;

    const connect = () => {
      const wsUrl = window.location.hostname === "localhost"
        ? "ws://localhost:3000/ws"
        : `ws://${window.location.host}/ws`;
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        reconnectTimer = setTimeout(connect, 2000);
      };
      ws.onmessage = (e) => {
        try {
          const evt = JSON.parse(e.data);
          handleEvent(evt);
        } catch {}
      };
    };

    connect();
    return () => {
      clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  // eslint-disable-next-line
  }, []);

  const handleEvent = useCallback((evt) => {
    setEvents((prev) => [...prev.slice(-150), evt]);

    switch (evt.type) {
      case "task_submitted":
        setPipelineComplete(false);
        setOutputs({});
        setAgentStates({});
        break;
      case "agent_start":
        setAgentStates((s) => ({ ...s, [evt.agent]: "starting" }));
        break;
      case "agent_thinking":
        setAgentStates((s) => ({ ...s, [evt.agent]: "thinking" }));
        break;
      case "agent_complete":
        setAgentStates((s) => ({ ...s, [evt.agent]: "done" }));
        setOutputs((o) => ({ ...o, [evt.agent]: evt.content }));
        break;
      case "kafka_message":
        setActivePulse(evt.from_agent);
        setTimeout(() => setActivePulse(null), 800);
        break;
      case "pipeline_complete":
        setPipelineComplete(true);
        break;
      default:
        break;
    }
  }, []);

  // Auto-scroll event log
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [events]);

  // ── Submit Task ───────────────────────────────────────
  const submitTask = async () => {
    setSubmitting(true);
    try {
      const base = window.location.hostname === "localhost"
        ? "http://localhost:3000"
        : "";
      await fetch(`${base}/api/task`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: taskTopic }),
      });
    } catch (err) {
      console.error("Submit error:", err);
    }
    setSubmitting(false);
  };

  return (
    <div style={styles.root}>
      {/* Background grid */}
      <div style={styles.gridBg} />

      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.logo}></div>
          <div>
            <h1 style={styles.title}>Multi-Agent Collaboration</h1>
            <p style={styles.subtitle}>
              OpenAI Agents • Apache Kafka • Real-Time Visualization
            </p>
          </div>
        </div>
        <div style={styles.statusBadge}>
          <span style={{
            ...styles.statusDot,
            background: connected ? "#10b981" : "#ef4444",
            boxShadow: connected
              ? "0 0 8px #10b981"
              : "0 0 8px #ef4444",
          }} />
          {connected ? "CONNECTED" : "RECONNECTING"}
        </div>
      </header>

      {/* Task Input */}
      <section style={styles.inputSection}>
        <div style={styles.inputRow}>
          <input
            style={styles.input}
            value={taskTopic}
            onChange={(e) => setTaskTopic(e.target.value)}
            placeholder="Enter a topic for the agents to collaborate on..."
            onKeyDown={(e) => e.key === "Enter" && submitTask()}
          />
          <button
            style={{
              ...styles.submitBtn,
              opacity: submitting ? 0.6 : 1,
            }}
            onClick={submitTask}
            disabled={submitting}
          >
            {submitting ? "Dispatching..." : "▶ Launch Pipeline"}
          </button>
        </div>
      </section>

      {/* Pipeline Visualization */}
      <section style={styles.pipeline}>
        <h2 style={styles.sectionTitle}>
          <span style={styles.sectionIcon}>◆</span> Agent Pipeline
        </h2>
        <div style={styles.pipelineRow}>
          {AGENTS.map((agent, i) => {
            const state = agentStates[agent.id];
            const isActive = state === "thinking";
            const isDone = state === "done";
            const isPulsing = activePulse === agent.id;

            return (
              <React.Fragment key={agent.id}>
                <div style={{
                  ...styles.agentCard,
                  borderColor: isDone ? agent.color : isActive ? agent.color : "#2a2a3e",
                  boxShadow: isActive
                    ? `0 0 30px ${agent.color}40, 0 0 60px ${agent.color}20`
                    : isDone
                    ? `0 0 20px ${agent.color}30`
                    : "0 4px 20px rgba(0,0,0,0.3)",
                  transform: isActive ? "scale(1.05)" : "scale(1)",
                }}>
                  <div style={{
                    ...styles.agentEmoji,
                    animation: isActive ? "pulse 1.5s ease infinite" : "none",
                  }}>
                    {agent.emoji}
                  </div>
                  <div style={styles.agentName}>{agent.name}</div>
                  <div style={{
                    ...styles.agentStatus,
                    color: isDone ? "#10b981" : isActive ? agent.color : "#666",
                  }}>
                    {isDone ? " Complete" : isActive ? "Thinking..." : state === "starting" ? "Starting..." : "Idle"}
                  </div>
                  {isActive && (
                    <div style={styles.thinkingBar}>
                      <div style={{
                        ...styles.thinkingFill,
                        background: agent.color,
                      }} />
                    </div>
                  )}
                </div>
                {i < AGENTS.length - 1 && (
                  <div style={styles.connector}>
                    <div style={{
                      ...styles.connectorLine,
                      background: isPulsing
                        ? `linear-gradient(90deg, ${agent.color}, ${AGENTS[i+1].color})`
                        : "#2a2a3e",
                      boxShadow: isPulsing ? `0 0 10px ${agent.color}60` : "none",
                    }} />
                    <div style={{
                      ...styles.connectorArrow,
                      borderLeftColor: isPulsing ? AGENTS[i+1].color : "#2a2a3e",
                    }} />
                    <div style={styles.topicLabel}>
                      {TOPICS[i + 1]}
                    </div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
        {pipelineComplete && (
          <div style={styles.completeBanner}>
             Pipeline Complete — All agents have finished collaborating!
          </div>
        )}
      </section>

      {/* Bottom: Outputs + Log */}
      <div style={styles.bottomGrid}>
        {/* Agent Outputs */}
        <section style={styles.outputsSection}>
          <h2 style={styles.sectionTitle}>
            <span style={styles.sectionIcon}>◆</span> Agent Outputs
          </h2>
          <div style={styles.outputsList}>
            {AGENTS.map((agent) => {
              const content = outputs[agent.id];
              if (!content) return null;
              return (
                <div key={agent.id} style={{
                  ...styles.outputCard,
                  borderLeftColor: agent.color,
                }}>
                  <div style={styles.outputHeader}>
                    <span>{agent.emoji}</span>
                    <span style={{ color: agent.color, fontWeight: 600 }}>
                      {agent.name}
                    </span>
                  </div>
                  <div style={styles.outputContent}>
                    {content.split("\n").map((line, i) => (
                      <p key={i} style={{
                        margin: "4px 0",
                        fontWeight: line.startsWith("**") ? 600 : 400,
                        color: line.startsWith("**") ? "#e2e8f0" : "#94a3b8",
                      }}>
                        {line.replace(/\*\*/g, "")}
                      </p>
                    ))}
                  </div>
                </div>
              );
            })}
            {Object.keys(outputs).length === 0 && (
              <div style={styles.emptyState}>
                Submit a task to see agent outputs here
              </div>
            )}
          </div>
        </section>

        {/* Event Log */}
        <section style={styles.logSection}>
          <h2 style={styles.sectionTitle}>
            <span style={styles.sectionIcon}>◆</span> Kafka Event Stream
            <span style={styles.eventCount}>{events.length}</span>
          </h2>
          <div ref={logRef} style={styles.logScroll}>
            {events.map((evt, i) => (
              <EventRow key={i} evt={evt} />
            ))}
            {events.length === 0 && (
              <div style={styles.emptyState}>
                Waiting for events...
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Kafka Topics Bar */}
      <section style={styles.topicsBar}>
        {TOPICS.map((t) => (
          <div key={t} style={styles.topicChip}>
            <span style={styles.topicDot} />
            {t}
          </div>
        ))}
      </section>

      <style>{animationCSS}</style>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   EVENT ROW COMPONENT
   ──────────────────────────────────────────────────────────── */
function EventRow({ evt }) {
  const agent = AGENTS.find((a) => a.id === evt.agent || a.id === evt.from_agent);
  const color = agent?.color || "#64748b";

  const labels = {
    task_submitted: " TASK SUBMITTED",
    agent_start: " AGENT START",
    agent_thinking: " THINKING",
    agent_complete: " COMPLETE",
    kafka_message: " KAFKA MSG",
    pipeline_complete: " PIPELINE DONE",
  };

  return (
    <div style={styles.eventRow}>
      <span style={{ ...styles.eventTime }}>
        {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : ""}
      </span>
      <span style={{
        ...styles.eventLabel,
        color,
        borderColor: color + "40",
      }}>
        {labels[evt.type] || evt.type}
      </span>
      <span style={styles.eventDetail}>
        {evt.agent && <span style={{ color }}>{evt.agent}</span>}
        {evt.topic && <span style={{ color: "#64748b" }}> → {evt.topic}</span>}
        {evt.to_topic && <span style={{ color: "#64748b" }}> → {evt.to_topic}</span>}
        {evt.task_id && <span style={styles.taskIdBadge}>#{evt.task_id}</span>}
      </span>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   ANIMATIONS
   ──────────────────────────────────────────────────────────── */
const animationCSS = `
  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.15); }
  }
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(200%); }
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: #0a0a14;
    font-family: 'DM Sans', -apple-system, sans-serif;
    color: #e2e8f0;
    overflow-x: hidden;
  }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0a0a14; }
  ::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 3px; }
  input:focus, button:focus { outline: none; }
`;

/* ────────────────────────────────────────────────────────────
   STYLES
   ──────────────────────────────────────────────────────────── */
const styles = {
  root: {
    minHeight: "100vh",
    padding: "24px 32px",
    position: "relative",
    maxWidth: 1400,
    margin: "0 auto",
  },
  gridBg: {
    position: "fixed",
    inset: 0,
    backgroundImage: `
      linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
    `,
    backgroundSize: "60px 60px",
    pointerEvents: "none",
    zIndex: 0,
  },

  // Header
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 24,
    position: "relative",
    zIndex: 1,
  },
  headerLeft: { display: "flex", alignItems: "center", gap: 16 },
  logo: {
    fontSize: 32,
    width: 52,
    height: 52,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "linear-gradient(135deg, #06b6d4, #8b5cf6)",
    borderRadius: 14,
  },
  title: {
    margin: 0,
    fontSize: 22,
    fontWeight: 700,
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: "-0.5px",
  },
  subtitle: {
    margin: "2px 0 0",
    fontSize: 13,
    color: "#64748b",
    fontFamily: "'JetBrains Mono', monospace",
  },
  statusBadge: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "8px 16px",
    background: "#12121e",
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "1px",
    fontFamily: "'JetBrains Mono', monospace",
    border: "1px solid #1e1e30",
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
  },

  // Input
  inputSection: {
    marginBottom: 24,
    position: "relative",
    zIndex: 1,
  },
  inputRow: {
    display: "flex",
    gap: 12,
  },
  input: {
    flex: 1,
    padding: "14px 20px",
    background: "#12121e",
    border: "1px solid #2a2a3e",
    borderRadius: 12,
    color: "#e2e8f0",
    fontSize: 15,
    fontFamily: "'DM Sans', sans-serif",
    transition: "border-color 0.2s",
  },
  submitBtn: {
    padding: "14px 28px",
    background: "linear-gradient(135deg, #06b6d4, #8b5cf6)",
    border: "none",
    borderRadius: 12,
    color: "#fff",
    fontSize: 14,
    fontWeight: 600,
    fontFamily: "'JetBrains Mono', monospace",
    cursor: "pointer",
    whiteSpace: "nowrap",
    transition: "transform 0.15s, opacity 0.15s",
  },

  // Pipeline
  pipeline: {
    marginBottom: 24,
    position: "relative",
    zIndex: 1,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "2px",
    color: "#64748b",
    marginBottom: 16,
    fontFamily: "'JetBrains Mono', monospace",
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  sectionIcon: { color: "#8b5cf6", fontSize: 10 },
  pipelineRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 0,
    padding: "20px 0",
  },
  agentCard: {
    width: 160,
    padding: "24px 16px",
    background: "#12121e",
    borderRadius: 16,
    border: "2px solid #2a2a3e",
    textAlign: "center",
    transition: "all 0.4s ease",
    position: "relative",
    overflow: "hidden",
  },
  agentEmoji: { fontSize: 36, marginBottom: 8 },
  agentName: {
    fontSize: 14,
    fontWeight: 600,
    fontFamily: "'JetBrains Mono', monospace",
    marginBottom: 4,
  },
  agentStatus: {
    fontSize: 11,
    fontWeight: 500,
    fontFamily: "'JetBrains Mono', monospace",
  },
  thinkingBar: {
    marginTop: 12,
    height: 3,
    background: "#1e1e30",
    borderRadius: 2,
    overflow: "hidden",
  },
  thinkingFill: {
    width: "40%",
    height: "100%",
    borderRadius: 2,
    animation: "shimmer 1.5s ease infinite",
  },
  connector: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    width: 80,
    position: "relative",
  },
  connectorLine: {
    width: "100%",
    height: 3,
    borderRadius: 2,
    transition: "all 0.3s ease",
  },
  connectorArrow: {
    width: 0,
    height: 0,
    borderTop: "6px solid transparent",
    borderBottom: "6px solid transparent",
    borderLeft: "8px solid #2a2a3e",
    position: "absolute",
    right: -4,
    top: "50%",
    transform: "translateY(-50%)",
    transition: "border-color 0.3s ease",
    marginTop: -8,
  },
  topicLabel: {
    fontSize: 9,
    color: "#475569",
    marginTop: 8,
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: "0.5px",
    textAlign: "center",
  },
  completeBanner: {
    textAlign: "center",
    padding: "12px 20px",
    background: "linear-gradient(135deg, #10b98115, #06b6d415)",
    border: "1px solid #10b98130",
    borderRadius: 12,
    marginTop: 16,
    fontSize: 14,
    fontWeight: 600,
    fontFamily: "'JetBrains Mono', monospace",
    color: "#10b981",
    animation: "fadeIn 0.5s ease",
  },

  // Bottom Grid
  bottomGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 24,
    marginBottom: 24,
    position: "relative",
    zIndex: 1,
  },

  // Outputs
  outputsSection: {},
  outputsList: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
    maxHeight: 420,
    overflowY: "auto",
  },
  outputCard: {
    padding: "16px 20px",
    background: "#12121e",
    borderRadius: 12,
    borderLeft: "3px solid",
    animation: "fadeIn 0.4s ease",
  },
  outputHeader: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 10,
    fontSize: 13,
    fontFamily: "'JetBrains Mono', monospace",
  },
  outputContent: {
    fontSize: 12.5,
    lineHeight: 1.6,
    fontFamily: "'DM Sans', sans-serif",
  },

  // Event Log
  logSection: {},
  eventCount: {
    marginLeft: "auto",
    background: "#1e1e30",
    padding: "2px 10px",
    borderRadius: 10,
    fontSize: 11,
    color: "#8b5cf6",
  },
  logScroll: {
    maxHeight: 420,
    overflowY: "auto",
    background: "#0d0d18",
    borderRadius: 12,
    border: "1px solid #1e1e30",
    padding: 8,
  },
  eventRow: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "6px 10px",
    borderBottom: "1px solid #1a1a2e",
    animation: "fadeIn 0.3s ease",
    fontSize: 12,
    fontFamily: "'JetBrains Mono', monospace",
  },
  eventTime: {
    color: "#475569",
    fontSize: 10,
    minWidth: 70,
    flexShrink: 0,
  },
  eventLabel: {
    fontSize: 10,
    fontWeight: 600,
    padding: "2px 8px",
    borderRadius: 6,
    border: "1px solid",
    whiteSpace: "nowrap",
  },
  eventDetail: {
    color: "#94a3b8",
    fontSize: 11,
    display: "flex",
    gap: 6,
    alignItems: "center",
    flexWrap: "wrap",
  },
  taskIdBadge: {
    background: "#1e1e30",
    padding: "1px 6px",
    borderRadius: 4,
    fontSize: 10,
    color: "#8b5cf6",
  },

  // Topics bar
  topicsBar: {
    display: "flex",
    justifyContent: "center",
    gap: 16,
    padding: "16px 0",
    position: "relative",
    zIndex: 1,
  },
  topicChip: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    padding: "6px 14px",
    background: "#12121e",
    borderRadius: 8,
    fontSize: 11,
    color: "#64748b",
    fontFamily: "'JetBrains Mono', monospace",
    border: "1px solid #1e1e30",
  },
  topicDot: {
    width: 6,
    height: 6,
    borderRadius: "50%",
    background: "#10b981",
    boxShadow: "0 0 6px #10b981",
  },

  // Empty
  emptyState: {
    textAlign: "center",
    padding: 40,
    color: "#475569",
    fontSize: 13,
    fontFamily: "'JetBrains Mono', monospace",
  },
};
