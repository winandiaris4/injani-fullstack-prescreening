/**
 * Q5 — JWT Auth Helper
 * Verifies JWT tokens using the `jose` library (works in Node.js + Edge runtime).
 */

import { jwtVerify, SignJWT } from "jose";

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || "injani-dev-secret-change-in-production"
);

export interface JWTPayload {
  userId: string;
  role: "admin" | "manager" | "viewer";
  email: string;
}

/**
 * Verify a JWT token and return the decoded payload.
 * Throws an error if the token is invalid or expired.
 */
export async function verifyToken(token: string): Promise<JWTPayload> {
  const { payload } = await jwtVerify(token, JWT_SECRET);
  return payload as unknown as JWTPayload;
}

/**
 * Sign a new JWT (for testing and development only).
 * In production, tokens are issued by the auth service.
 */
export async function signToken(payload: JWTPayload, expiresIn = "1h"): Promise<string> {
  return new SignJWT(payload as Record<string, unknown>)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(expiresIn)
    .sign(JWT_SECRET);
}

/**
 * Extract bearer token from Authorization header.
 * Supports both "Bearer <token>" and raw token formats.
 */
export function extractBearerToken(authHeader: string | null): string | null {
  if (!authHeader) return null;
  if (authHeader.startsWith("Bearer ")) return authHeader.slice(7);
  return authHeader;
}

