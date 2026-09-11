/**
 * Q5 — API Tests
 * Jest unit tests covering:
 *   1. Valid request with proper JWT → 200 OK
 *   2. Missing token → 401 Unauthorized
 *   3. AppError thrown in handler → correct JSON shape
 *   4. Unexpected error → 500 with safe message
 *
 * Tests run against lib/ modules directly (not Next.js runtime).
 */

import { AppError, UnauthorizedError, ForbiddenError, NotFoundError, RateLimitError } from "../lib/errors";
import { withErrorHandler, ok, fail, ApiResponse } from "../lib/api-wrapper";
import { signToken, verifyToken, extractBearerToken } from "../lib/auth";
import { NextRequest } from "next/server";

// ─── Mock NextRequest helper ──────────────────────────────────────────────────

function makeRequest(
  options: {
    url?: string;
    method?: string;
    headers?: Record<string, string>;
    body?: unknown;
  } = {}
): NextRequest {
  const url = options.url || "http://localhost:3000/api/orders";
  const init: RequestInit = {
    method: options.method || "GET",
    headers: options.headers || {},
  };
  if (options.body) {
    init.body = JSON.stringify(options.body);
    (init.headers as Record<string, string>)["content-type"] = "application/json";
  }
  return new NextRequest(url, init);
}

// ─── Error Classes Tests ──────────────────────────────────────────────────────

describe("AppError & Subclasses", () => {
  it("AppError stores code, statusCode, message, details", () => {
    const err = new AppError("MY_CODE", 422, "something failed", { field: "x" });
    expect(err.code).toBe("MY_CODE");
    expect(err.statusCode).toBe(422);
    expect(err.message).toBe("something failed");
    expect(err.details).toEqual({ field: "x" });
    expect(err instanceof Error).toBe(true);
    expect(err instanceof AppError).toBe(true);
  });

  it("UnauthorizedError has statusCode 401 and code UNAUTHORIZED", () => {
    const err = new UnauthorizedError();
    expect(err.statusCode).toBe(401);
    expect(err.code).toBe("UNAUTHORIZED");
  });

  it("ForbiddenError has statusCode 403", () => {
    const err = new ForbiddenError();
    expect(err.statusCode).toBe(403);
    expect(err.code).toBe("FORBIDDEN");
  });

  it("NotFoundError includes resource name", () => {
    const err = new NotFoundError("Order #42");
    expect(err.statusCode).toBe(404);
    expect(err.message).toContain("Order #42");
  });

  it("RateLimitError has statusCode 429", () => {
    const err = new RateLimitError();
    expect(err.statusCode).toBe(429);
    expect(err.code).toBe("RATE_LIMIT_EXCEEDED");
  });
});

// ─── ApiResponse Helpers Tests ────────────────────────────────────────────────

describe("ApiResponse helpers: ok() and fail()", () => {
  it("ok() returns a NextResponse with success=true and data", async () => {
    const res = ok({ id: 1, name: "test" }, 200);
    const body: ApiResponse<{ id: number; name: string }> = await res.json();

    expect(res.status).toBe(200);
    expect(body.success).toBe(true);
    expect(body.data).toEqual({ id: 1, name: "test" });
    expect(body.meta?.timestamp).toBeDefined();
  });

  it("fail() returns a NextResponse with success=false and error shape", async () => {
    const res = fail("MY_ERROR", "Something went wrong", 422, { field: "name" });
    const body: ApiResponse<null> = await res.json();

    expect(res.status).toBe(422);
    expect(body.success).toBe(false);
    expect(body.error?.code).toBe("MY_ERROR");
    expect(body.error?.message).toBe("Something went wrong");
    expect(body.error?.details).toEqual({ field: "name" });
  });
});

// ─── withErrorHandler Tests ───────────────────────────────────────────────────

describe("withErrorHandler HOF", () => {
  it("passes through successful handler response unchanged", async () => {
    const handler = withErrorHandler(async () => ok({ message: "hello" }, 200));
    const req = makeRequest();
    const res = await handler(req);
    const body = await res.json();

    expect(res.status).toBe(200);
    expect(body.success).toBe(true);
    expect(body.data.message).toBe("hello");
  });

  it("converts AppError to correct status code and error shape", async () => {
    const handler = withErrorHandler(async () => {
      throw new UnauthorizedError("Token expired");
    });
    const req = makeRequest();
    const res = await handler(req);
    const body = await res.json();

    expect(res.status).toBe(401);
    expect(body.success).toBe(false);
    expect(body.error.code).toBe("UNAUTHORIZED");
    expect(body.error.message).toBe("Token expired");
  });

  it("converts ForbiddenError to 403", async () => {
    const handler = withErrorHandler(async () => {
      throw new ForbiddenError("Access denied");
    });
    const res = await handler(makeRequest());
    expect(res.status).toBe(403);
  });

  it("converts unexpected Error to 500 INTERNAL_ERROR without leaking details", async () => {
    const handler = withErrorHandler(async () => {
      throw new Error("Some internal database error with sensitive info");
    });
    const req = makeRequest();
    const res = await handler(req);
    const body = await res.json();

    expect(res.status).toBe(500);
    expect(body.success).toBe(false);
    expect(body.error.code).toBe("INTERNAL_ERROR");
    // Must not expose internal error message
    expect(body.error.message).not.toContain("sensitive info");
    expect(body.error.message).toBe("An unexpected error occurred");
  });
});

// ─── JWT Auth Tests ───────────────────────────────────────────────────────────

describe("JWT Auth: signToken / verifyToken / extractBearerToken", () => {
  it("signs and verifies a token successfully", async () => {
    const payload = { userId: "user-123", role: "admin" as const, email: "aris@example.com" };
    const token = await signToken(payload);
    const decoded = await verifyToken(token);

    expect(decoded.userId).toBe("user-123");
    expect(decoded.role).toBe("admin");
    expect(decoded.email).toBe("aris@example.com");
  });

  it("verifyToken throws on invalid token", async () => {
    await expect(verifyToken("invalid.token.here")).rejects.toThrow();
  });

  it("extractBearerToken strips 'Bearer ' prefix", () => {
    expect(extractBearerToken("Bearer my-token-value")).toBe("my-token-value");
  });

  it("extractBearerToken returns null for null header", () => {
    expect(extractBearerToken(null)).toBeNull();
  });

  it("extractBearerToken returns raw token if no Bearer prefix", () => {
    expect(extractBearerToken("raw-token")).toBe("raw-token");
  });
});

