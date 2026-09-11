# Q5 — Next.js API Patterns: Auth, Rate Limiting & Error Handling

PoC untuk menjawab **Question 5** dari pre-screening INJANI SYSTEMS.

## Overview

Demonstrasi pola API Next.js 14 yang production-ready:
- JWT Authentication via `jose` (Edge-compatible)
- Typed error hierarchy dengan `AppError` class
- `withErrorHandler` HOF — eliminasi boilerplate try/catch di setiap route
- `ApiResponse<T>` — standardized response envelope
- 20+ Jest unit tests

## Cara Menjalankan

### 1. Install dependencies
```bash
npm install
```

### 2. Jalankan tests
```bash
npm test
```

### 3. Jalankan server
```bash
npm run dev
# Buka: http://localhost:3001 (untuk menghindari clash dengan Q2)
```

### 4. Test endpoint

```bash
# Generate token (via signToken in lib/auth.ts)
# Atau gunakan token test ini (valid untuk dev):

# ✅ Request dengan token valid
curl -X GET http://localhost:3001/api/orders \
  -H "Authorization: Bearer <your-jwt-token>"

# ❌ Request tanpa token → 401
curl -X GET http://localhost:3001/api/orders
```

## Pola Error Handling

### Custom Error Hierarchy
```typescript
AppError (base)
├── UnauthorizedError  → 401 UNAUTHORIZED
├── ForbiddenError     → 403 FORBIDDEN
├── NotFoundError      → 404 NOT_FOUND
├── ValidationError    → 422 VALIDATION_ERROR
└── RateLimitError     → 429 RATE_LIMIT_EXCEEDED
```

### withErrorHandler HOF
```typescript
// Setiap route handler bersih dari boilerplate try/catch:
export const GET = withErrorHandler(async (req) => {
  const user = await authenticate(req);  // throws UnauthorizedError jika gagal
  if (!hasPermission(user)) throw new ForbiddenError();
  return ok(await getOrders());
});
```

### Standardized Response Envelope
```json
// Success
{ "success": true, "data": [...], "meta": { "timestamp": "..." } }

// Error
{ "success": false, "error": { "code": "UNAUTHORIZED", "message": "..." } }
```

## JWT Authentication Strategy

| Layer | Lokasi | Tugas |
|---|---|---|
| **Layer 1** | `middleware.ts` (Edge) | Fast rejection — cek keberadaan token |
| **Layer 2** | Route Handler | Verify token + cek role/permission (RBAC) |

## Tech Stack

- **Next.js 14** — App Router, Edge Middleware
- **jose** — JWT sign/verify (Node.js + Edge compatible)
- **TypeScript** — Strict typed error hierarchy
- **Jest + ts-jest** — Unit testing

