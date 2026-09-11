/**
 * Q2 — SLA Dashboard Seed Script
 * Generates realistic dummy data for the SLA analytics dashboard.
 *
 * Usage:
 *   DATABASE_URL="file:./dev.db" npx prisma db push
 *   DATABASE_URL="file:./dev.db" npm run db:seed
 */

import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

// ─── Helper ───────────────────────────────────────────────────────────────────

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomDate(daysAgo: number): Date {
  const now = new Date();
  const past = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);
  return new Date(past.getTime() + Math.random() * (now.getTime() - past.getTime()));
}

function addMinutes(date: Date, minutes: number): Date {
  return new Date(date.getTime() + minutes * 60 * 1000);
}

// ─── Seed Data Definitions ────────────────────────────────────────────────────

const DEPARTMENTS = ["Finance", "Legal", "Operations", "Procurement", "HR"];

const STEP_TYPES = [
  { name: "Finance Approval", slaTargetMinutes: 120 },     // 2 hours
  { name: "Legal Review", slaTargetMinutes: 480 },          // 8 hours
  { name: "Manager Sign-off", slaTargetMinutes: 60 },       // 1 hour
  { name: "Procurement Check", slaTargetMinutes: 240 },     // 4 hours
  { name: "HR Clearance", slaTargetMinutes: 180 },          // 3 hours
  { name: "Director Approval", slaTargetMinutes: 720 },     // 12 hours
];

const USERS_PER_DEPT = 3;  // 5 depts × 3 users = 15 users
const TOTAL_WORKFLOWS = 80;

// ─── Main Seed Function ───────────────────────────────────────────────────────

async function main() {
  console.log("🌱 Starting seed...");

  // Clean up existing data
  await prisma.workflowStep.deleteMany();
  await prisma.workflow.deleteMany();
  await prisma.stepType.deleteMany();
  await prisma.user.deleteMany();
  await prisma.department.deleteMany();

  // 1. Create departments
  const departments = await Promise.all(
    DEPARTMENTS.map((name) => prisma.department.create({ data: { name } }))
  );
  console.log(`  ✅ Created ${departments.length} departments`);

  // 2. Create step types
  const stepTypes = await Promise.all(
    STEP_TYPES.map((st) => prisma.stepType.create({ data: st }))
  );
  console.log(`  ✅ Created ${stepTypes.length} step types`);

  // 3. Create users (3 per department)
  const users = await Promise.all(
    departments.flatMap((dept, deptIdx) =>
      Array.from({ length: USERS_PER_DEPT }, (_, i) =>
        prisma.user.create({
          data: {
            name: `User ${deptIdx * USERS_PER_DEPT + i + 1} (${dept.name})`,
            departmentId: dept.id,
          },
        })
      )
    )
  );
  console.log(`  ✅ Created ${users.length} users`);

  // 4. Create workflows with steps
  let totalSteps = 0;
  for (let w = 0; w < TOTAL_WORKFLOWS; w++) {
    const dept = departments[randomInt(0, departments.length - 1)];
    const workflowCreatedAt = randomDate(90); // within last 90 days

    const workflow = await prisma.workflow.create({
      data: {
        title: `Workflow #${w + 1} - ${dept.name} Request`,
        departmentId: dept.id,
        status: ["in_progress", "approved", "rejected"][randomInt(0, 2)],
        createdAt: workflowCreatedAt,
      },
    });

    // Each workflow has 2–4 steps
    const numSteps = randomInt(2, 4);
    let stepStartTime = workflowCreatedAt;

    for (let s = 0; s < numSteps; s++) {
      const stepType = stepTypes[randomInt(0, stepTypes.length - 1)];
      const deptUsers = users.filter((u) => u.departmentId === dept.id);
      const assignee = deptUsers[randomInt(0, deptUsers.length - 1)];

      const assignedAt = stepStartTime;

      // 30% chance of SLA breach (duration > slaTargetMinutes)
      const isBreach = Math.random() < 0.30;
      const multiplier = isBreach ? randomInt(110, 250) / 100 : randomInt(30, 95) / 100;
      const durationMinutes = Math.round(stepType.slaTargetMinutes * multiplier);

      // 15% chance step is still pending (completedAt = null)
      const isPending = s === numSteps - 1 && Math.random() < 0.15;
      const completedAt = isPending ? null : addMinutes(assignedAt, durationMinutes);

      await prisma.workflowStep.create({
        data: {
          workflowId: workflow.id,
          stepTypeId: stepType.id,
          assigneeId: assignee.id,
          assignedAt,
          completedAt,
        },
      });

      totalSteps++;
      if (completedAt) stepStartTime = completedAt;
    }
  }

  console.log(`  ✅ Created ${TOTAL_WORKFLOWS} workflows with ${totalSteps} steps`);
  console.log("🎉 Seed complete!");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

