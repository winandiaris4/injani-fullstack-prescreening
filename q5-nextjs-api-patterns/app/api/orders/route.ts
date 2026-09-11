/**
 * Q5 — Orders API Route
 * Protected endpoint demonstrating:
 *   - JWT authentication (Bearer token)
 *   - RBAC (role-based access control)
 *   - withErrorHandler HOF wrapping
 *   - Typed ApiResponse<T> responses
 */

import { NextRequest } from "next/server";
import { withErrorHandler, ok } from "@/lib/api-wrapper";
import { UnauthorizedError, ForbiddenError, NotFoundError } from "@/lib/errors";
import { verifyToken, extractBearerToken } from "@/lib/auth";

// ─── Fake Order Type & Data ───────────────────────────────────────────────────

interface Order {
  id: number;
  customerId: string;
  items: Array<{ name: string; quantity: number; amount: number }>;
  totalAmount: number;
  status: "pending" | "processing" | "completed" | "cancelled";
  createdAt: string;
}

const MOCK_ORDERS: Order[] = [
  {
    id: 1,
    customerId: "cust-001",
    items: [{ name: "Cement (50kg bag)", quantity: 10, amount: 850000 }],
    totalAmount: 8_500_000,
    status: "completed",
    createdAt: "2026-09-01T10:00:00Z",
  },
  {
    id: 2,
    customerId: "cust-002",
    items: [
      { name: "Red Brick", quantity: 500, amount: 1_250_000 },
      { name: "Sand (per m³)", quantity: 2, amount: 400_000 },
    ],
    totalAmount: 1_650_000,
    status: "pending",
    createdAt: "2026-09-10T14:30:00Z",
  },
];

// ─── GET /api/orders ───────────────────────────────────────────────────────────

export const GET = withErrorHandler<Order[]>(async (req: NextRequest) => {
  // ── Layer 1: Authentication ────────────────────────────────────────────────
  const authHeader = req.headers.get("authorization");
  const token = extractBearerToken(authHeader);

  if (!token) {
    throw new UnauthorizedError("Missing or invalid Authorization header");
  }

  let user;
  try {
    user = await verifyToken(token);
  } catch {
    throw new UnauthorizedError("Token is invalid or expired");
  }

  // ── Layer 2: Authorization (RBAC) ─────────────────────────────────────────
  const allowedRoles = ["admin", "manager"] as const;
  if (!allowedRoles.includes(user.role)) {
    throw new ForbiddenError(
      `Role '${user.role}' does not have permission to view orders`
    );
  }

  // ── Layer 3: Business Logic ────────────────────────────────────────────────
  const { searchParams } = new URL(req.url);
  const statusFilter = searchParams.get("status");

  const orders = statusFilter
    ? MOCK_ORDERS.filter((o) => o.status === statusFilter)
    : MOCK_ORDERS;

  return ok(orders, 200, { requestId: `req-${Date.now()}` });
});

// ─── GET /api/orders/[id] — demonstrating NotFoundError ──────────────────────
// (In a real app this would be a separate route file: app/api/orders/[id]/route.ts)

export const POST = withErrorHandler<{ message: string }>(async (req: NextRequest) => {
  const authHeader = req.headers.get("authorization");
  const token = extractBearerToken(authHeader);

  if (!token) throw new UnauthorizedError();

  try {
    await verifyToken(token);
  } catch {
    throw new UnauthorizedError("Token is invalid or expired");
  }

  const body = await req.json();
  const orderId = body?.id as number | undefined;

  if (orderId && !MOCK_ORDERS.find((o) => o.id === orderId)) {
    throw new NotFoundError(`Order #${orderId}`);
  }

  return ok({ message: "Order processed successfully" }, 201);
});

