/**
 * Q2 — SLA Analytics Dashboard
 * React Server Component (RSC) — data fetching happens on the server.
 * Uses Tremor components for charts and data visualization.
 */

import { Suspense } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface StepTypeStat {
  name: string;
  avgDurationMinutes: number;
  slaTargetMinutes: number;
  isBreached: boolean;
}

interface BreachedWorkflow {
  id: number;
  title: string;
  department: string;
  status: string;
  createdAt: string;
  totalDurationMinutes: number;
  breachedStepsCount: number;
  totalSteps: number;
}

interface SLAData {
  stepTypeStats: StepTypeStat[];
  breachedWorkflows: BreachedWorkflow[];
  summary: {
    totalWorkflows: number;
    totalSteps: number;
    breachRate: number;
    breachedStepsCount: number;
  };
}

// ─── Server-Side Data Fetching ────────────────────────────────────────────────

async function getSLAData(): Promise<SLAData> {
  // In RSC, we can call our own API route or query DB directly
  // For simplicity in PoC, calling the API route
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";
  const res = await fetch(`${baseUrl}/api/sla`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch SLA data");
  return res.json();
}

// ─── Dashboard Components ─────────────────────────────────────────────────────

function MetricCard({
  title,
  value,
  subtitle,
  color,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: string;
}) {
  return (
    <div
      style={{
        background: "white",
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        padding: "20px 24px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
      }}
    >
      <p style={{ fontSize: 13, color: "#6b7280", margin: 0 }}>{title}</p>
      <p
        style={{
          fontSize: 28,
          fontWeight: 700,
          color: color || "#111827",
          margin: "4px 0",
        }}
      >
        {value}
      </p>
      {subtitle && <p style={{ fontSize: 12, color: "#9ca3af", margin: 0 }}>{subtitle}</p>}
    </div>
  );
}

function BarChartSimple({ data }: { data: StepTypeStat[] }) {
  const maxVal = Math.max(...data.flatMap((d) => [d.avgDurationMinutes, d.slaTargetMinutes]));

  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 600, color: "#374151", marginBottom: 16 }}>
        Avg Duration vs SLA Target (minutes)
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {data.map((item) => (
          <div key={item.name}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: 4,
                fontSize: 13,
                color: "#374151",
              }}
            >
              <span>{item.name}</span>
              <span style={{ color: item.isBreached ? "#ef4444" : "#10b981", fontWeight: 600 }}>
                {item.avgDurationMinutes}min
                {item.isBreached ? " ⚠️ Breached" : " ✅ OK"}
              </span>
            </div>
            <div style={{ position: "relative", height: 8 }}>
              {/* SLA Target Line */}
              <div
                style={{
                  position: "absolute",
                  left: `${(item.slaTargetMinutes / maxVal) * 100}%`,
                  top: -2,
                  width: 2,
                  height: 12,
                  background: "#6b7280",
                  zIndex: 2,
                }}
                title={`SLA Target: ${item.slaTargetMinutes}min`}
              />
              {/* Background track */}
              <div
                style={{
                  background: "#f3f4f6",
                  borderRadius: 4,
                  height: "100%",
                  overflow: "hidden",
                }}
              >
                {/* Actual bar */}
                <div
                  style={{
                    width: `${Math.min((item.avgDurationMinutes / maxVal) * 100, 100)}%`,
                    height: "100%",
                    background: item.isBreached ? "#ef4444" : "#10b981",
                    borderRadius: 4,
                    transition: "width 0.5s ease",
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
      <p style={{ fontSize: 11, color: "#9ca3af", marginTop: 8 }}>
        │ = SLA Target threshold
      </p>
    </div>
  );
}

function BreachedWorkflowsTable({ workflows }: { workflows: BreachedWorkflow[] }) {
  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 600, color: "#374151", marginBottom: 12 }}>
        Top Breached Workflows
      </h3>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
              {["ID", "Title", "Department", "Status", "Breached Steps", "Total Duration"].map(
                (h) => (
                  <th
                    key={h}
                    style={{
                      padding: "8px 12px",
                      textAlign: "left",
                      color: "#6b7280",
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {workflows.map((wf, i) => (
              <tr
                key={wf.id}
                style={{
                  borderBottom: "1px solid #f3f4f6",
                  background: i % 2 === 0 ? "white" : "#fafafa",
                }}
              >
                <td style={{ padding: "10px 12px", color: "#374151" }}>#{wf.id}</td>
                <td
                  style={{
                    padding: "10px 12px",
                    color: "#111827",
                    fontWeight: 500,
                    maxWidth: 200,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {wf.title}
                </td>
                <td style={{ padding: "10px 12px", color: "#374151" }}>{wf.department}</td>
                <td style={{ padding: "10px 12px" }}>
                  <span
                    style={{
                      padding: "2px 8px",
                      borderRadius: 12,
                      fontSize: 11,
                      fontWeight: 600,
                      background:
                        wf.status === "approved"
                          ? "#d1fae5"
                          : wf.status === "rejected"
                          ? "#fee2e2"
                          : "#fef3c7",
                      color:
                        wf.status === "approved"
                          ? "#065f46"
                          : wf.status === "rejected"
                          ? "#991b1b"
                          : "#92400e",
                    }}
                  >
                    {wf.status}
                  </span>
                </td>
                <td style={{ padding: "10px 12px", color: "#ef4444", fontWeight: 600 }}>
                  {wf.breachedStepsCount}/{wf.totalSteps}
                </td>
                <td style={{ padding: "10px 12px", color: "#374151" }}>
                  {wf.totalDurationMinutes}min
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {workflows.length === 0 && (
          <p style={{ textAlign: "center", color: "#6b7280", padding: 24 }}>
            🎉 No SLA breaches found!
          </p>
        )}
      </div>
    </div>
  );
}

// ─── Main Dashboard Page (RSC) ────────────────────────────────────────────────

export default async function DashboardPage() {
  const data = await getSLAData();

  return (
    <div
      style={{
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        background: "#f9fafb",
        minHeight: "100vh",
        padding: 32,
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "#111827", margin: 0 }}>
          📊 SLA Analytics Dashboard
        </h1>
        <p style={{ color: "#6b7280", marginTop: 4, fontSize: 14 }}>
          Injani Systems — Approval Workflow Performance Monitor
        </p>
      </div>

      {/* Summary Metrics */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 16,
          marginBottom: 32,
        }}
      >
        <MetricCard
          title="Total Workflows"
          value={data.summary.totalWorkflows}
          subtitle="All time"
        />
        <MetricCard
          title="Total Steps"
          value={data.summary.totalSteps}
          subtitle="Across all workflows"
        />
        <MetricCard
          title="SLA Breach Rate"
          value={`${data.summary.breachRate}%`}
          subtitle={`${data.summary.breachedStepsCount} steps breached`}
          color={data.summary.breachRate > 20 ? "#ef4444" : "#10b981"}
        />
        <MetricCard
          title="Step Types Monitored"
          value={data.stepTypeStats.length}
          subtitle="With SLA targets"
        />
      </div>

      {/* Charts Row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 24, marginBottom: 24 }}>
        <div
          style={{
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: 8,
            padding: 24,
            boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
          }}
        >
          <Suspense fallback={<p>Loading chart...</p>}>
            <BarChartSimple data={data.stepTypeStats} />
          </Suspense>
        </div>
      </div>

      {/* Breached Workflows Table */}
      <div
        style={{
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: 8,
          padding: 24,
          boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        }}
      >
        <BreachedWorkflowsTable workflows={data.breachedWorkflows} />
      </div>
    </div>
  );
}

