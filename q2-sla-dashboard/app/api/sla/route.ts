/**
 * Q2 — SLA Dashboard API Route
 * Fetches aggregated SLA analytics data from the database.
 * Used by the dashboard page as a server-side data source.
 */

import { NextResponse } from "next/server";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export async function GET() {
  try {
    // ── 1. Average Duration per Step Type vs SLA Target ──────────────────────
    const stepTypes = await prisma.stepType.findMany({
      include: {
        workflowSteps: {
          where: { completedAt: { not: null } },
          select: { assignedAt: true, completedAt: true },
        },
      },
    });

    const stepTypeStats = stepTypes.map((st) => {
      const completedSteps = st.workflowSteps.filter((s) => s.completedAt);
      const avgDuration =
        completedSteps.length > 0
          ? completedSteps.reduce((sum, s) => {
              const duration =
                (new Date(s.completedAt!).getTime() - new Date(s.assignedAt).getTime()) /
                60000;
              return sum + duration;
            }, 0) / completedSteps.length
          : 0;

      return {
        name: st.name,
        avgDurationMinutes: Math.round(avgDuration),
        slaTargetMinutes: st.slaTargetMinutes,
        isBreached: avgDuration > st.slaTargetMinutes,
      };
    });

    // ── 2. Top 10 Breached Workflows ──────────────────────────────────────────
    const workflows = await prisma.workflow.findMany({
      include: {
        department: { select: { name: true } },
        steps: {
          include: {
            stepType: { select: { name: true, slaTargetMinutes: true } },
            assignee: { select: { name: true } },
          },
        },
      },
      orderBy: { createdAt: "desc" },
    });

    const breachedWorkflows = workflows
      .map((wf) => {
        const breachedSteps = wf.steps.filter((step) => {
          if (!step.completedAt) return false;
          const duration =
            (new Date(step.completedAt).getTime() - new Date(step.assignedAt).getTime()) /
            60000;
          return duration > step.stepType.slaTargetMinutes;
        });

        const totalDurationMinutes = wf.steps.reduce((sum, step) => {
          if (!step.completedAt) return sum;
          return (
            sum +
            (new Date(step.completedAt).getTime() - new Date(step.assignedAt).getTime()) /
              60000
          );
        }, 0);

        return {
          id: wf.id,
          title: wf.title,
          department: wf.department.name,
          status: wf.status,
          createdAt: wf.createdAt,
          totalDurationMinutes: Math.round(totalDurationMinutes),
          breachedStepsCount: breachedSteps.length,
          totalSteps: wf.steps.length,
        };
      })
      .filter((wf) => wf.breachedStepsCount > 0)
      .sort((a, b) => b.breachedStepsCount - a.breachedStepsCount)
      .slice(0, 10);

    // ── 3. Summary Metrics ─────────────────────────────────────────────────────
    const totalSteps = await prisma.workflowStep.count();
    const breachedStepsCount = (
      await prisma.workflowStep.findMany({
        where: { completedAt: { not: null } },
        include: { stepType: { select: { slaTargetMinutes: true } } },
      })
    ).filter((step) => {
      const duration =
        (new Date(step.completedAt!).getTime() - new Date(step.assignedAt).getTime()) /
        60000;
      return duration > step.stepType.slaTargetMinutes;
    }).length;

    return NextResponse.json({
      stepTypeStats,
      breachedWorkflows,
      summary: {
        totalWorkflows: workflows.length,
        totalSteps,
        breachRate:
          totalSteps > 0 ? Math.round((breachedStepsCount / totalSteps) * 100) : 0,
        breachedStepsCount,
      },
    });
  } catch (error) {
    console.error("[SLA API] Error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

