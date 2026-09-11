/**
 * Q5 — Next.js Edge Middleware
 *
 * Implements:
 *   1. JWT Verification at the Edge (Fast Rejection before hitting serverless compute)
 *   2. Rate Limiting Simulation (Sliding window rate limit check)
 */

import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || "injani-dev-secret-change-in-production"
);

// Simulated in-memory sliding window rate limiter for Edge/PoC
const rateLimitMap = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT_WINDOW_MS = 60 * 1000; // 1 minute
const MAX_REQUESTS_PER_WINDOW = 60; // 60 req/min

function checkRateLimit(identifier: string): { success: boolean; remaining: number } {
  const now = Date.now();
  const record = rateLimitMap.get(identifier);

  if (!record || now > record.resetTime) {
    rateLimitMap.set(identifier, { count: 1, resetTime: now + RATE_LIMIT_WINDOW_MS });
    return { success: true, remaining: MAX_REQUESTS_PER_WINDOW - 1 };
  }

  if (record.count >= MAX_REQUESTS_PER_WINDOW) {
    return { success: false, remaining: 0 };
  }

  record.count += 1;
  return { success: true, remaining: MAX_REQUESTS_PER_WINDOW - record.count };
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Only protect /api/* routes (excluding health/public if any)
  if (!pathname.startsWith("/api/")) {
    return NextResponse.next();
  }

  // ── 1. Rate Limiting Check ──────────────────────────────────────────────────
  const ip = req.ip || req.headers.get("x-forwarded-for") || "anonymous";
  const { success: rateLimitOk, remaining } = checkRateLimit(ip);

  if (!rateLimitOk) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "RATE_LIMIT_EXCEEDED",
          message: "Too many requests. Please try again later.",
        },
      },
      {
        status: 429,
        headers: {
          "Retry-After": "60",
          "X-RateLimit-Limit": String(MAX_REQUESTS_PER_WINDOW),
          "X-RateLimit-Remaining": "0",
        },
      }
    );
  }

  // ── 2. Edge JWT Verification (Fast Rejection) ───────────────────────────────
  const authHeader = req.headers.get("authorization");
  const token = authHeader?.startsWith("Bearer ")
    ? authHeader.slice(7)
    : req.cookies.get("token")?.value;

  if (!token) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "UNAUTHORIZED",
          message: "Authentication token is missing.",
        },
      },
      { status: 401 }
    );
  }

  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);

    // Forward verified user information in custom request headers to downstream route handlers
    const requestHeaders = new Headers(req.headers);
    requestHeaders.set("x-user-id", String(payload.userId || ""));
    requestHeaders.set("x-user-role", String(payload.role || ""));

    const response = NextResponse.next({
      request: { headers: requestHeaders },
    });
    response.headers.set("X-RateLimit-Remaining", String(remaining));
    return response;
  } catch {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "UNAUTHORIZED",
          message: "Invalid or expired authentication token.",
        },
      },
      { status: 401 }
    );
  }
}

export const config = {
  matcher: ["/api/:path*"],
};

