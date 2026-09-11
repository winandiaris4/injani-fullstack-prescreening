/**
 * Q5 — API Wrapper & Response Types
 *
 * Provides:
 *   1. ApiResponse<T> — standardized JSON response envelope
 *   2. withErrorHandler — Higher-Order Function (HOF) that wraps route handlers
 *      with consistent error handling so each route handler doesn't need
 *      individual try/catch blocks.
 */

import { NextRequest, NextResponse } from "next/server";
import { AppError } from "./errors";

// ─── Standardized Response Envelope ──────────────────────────────────────────

export interface ApiResponse<T = null> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
  meta?: {
    timestamp: string;
    requestId?: string;
  };
}

// ─── Success Response Helper ──────────────────────────────────────────────────

export function ok<T>(
  data: T,
  status = 200,
  meta?: ApiResponse["meta"]
): NextResponse<ApiResponse<T>> {
  return NextResponse.json(
    {
      success: true,
      data,
      meta: {
        timestamp: new Date().toISOString(),
        ...meta,
      },
    },
    { status }
  );
}

// ─── Error Response Helper ────────────────────────────────────────────────────

export function fail(
  code: string,
  message: string,
  status: number,
  details?: unknown
): NextResponse<ApiResponse<null>> {
  return NextResponse.json(
    {
      success: false,
      error: { code, message, details },
      meta: { timestamp: new Date().toISOString() },
    },
    { status }
  );
}

// ─── withErrorHandler HOF ─────────────────────────────────────────────────────

type RouteHandler<T = unknown> = (
  req: NextRequest,
  context?: { params: Record<string, string> }
) => Promise<NextResponse<ApiResponse<T>>>;

/**
 * Higher-Order Function that wraps any route handler with:
 * - AppError → mapped to its statusCode + code + message
 * - Unexpected errors → 500 INTERNAL_ERROR (safe message, no leak)
 *
 * Usage:
 *   export const GET = withErrorHandler(async (req) => {
 *     // your handler logic
 *   });
 */
export function withErrorHandler<T>(handler: RouteHandler<T>): RouteHandler<T | null> {
  return async (
    req: NextRequest,
    context?: { params: Record<string, string> }
  ): Promise<NextResponse<ApiResponse<T | null>>> => {
    try {
      return await handler(req, context);
    } catch (error) {
      if (error instanceof AppError) {
        return fail(error.code, error.message, error.statusCode, error.details);
      }

      // Log unexpected errors server-side (don't expose internals to client)
      console.error("[withErrorHandler] Unexpected error:", error);
      return fail("INTERNAL_ERROR", "An unexpected error occurred", 500);
    }
  };
}

