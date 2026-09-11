/**
 * Q5 — Custom Error Classes
 * Typed error hierarchy for consistent API error handling.
 */

export class AppError extends Error {
  constructor(
    public readonly code: string,
    public readonly statusCode: number,
    message: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = "AppError";
    // Restore prototype chain (required when extending built-in Error in TS)
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

// ─── Convenience subclasses for common HTTP errors ────────────────────────────

export class UnauthorizedError extends AppError {
  constructor(message = "Authentication required", details?: unknown) {
    super("UNAUTHORIZED", 401, message, details);
    this.name = "UnauthorizedError";
  }
}

export class ForbiddenError extends AppError {
  constructor(message = "Insufficient permissions", details?: unknown) {
    super("FORBIDDEN", 403, message, details);
    this.name = "ForbiddenError";
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, details?: unknown) {
    super("NOT_FOUND", 404, `${resource} not found`, details);
    this.name = "NotFoundError";
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details?: unknown) {
    super("VALIDATION_ERROR", 422, message, details);
    this.name = "ValidationError";
  }
}

export class RateLimitError extends AppError {
  constructor(message = "Too many requests — please try again later", details?: unknown) {
    super("RATE_LIMIT_EXCEEDED", 429, message, details);
    this.name = "RateLimitError";
  }
}

