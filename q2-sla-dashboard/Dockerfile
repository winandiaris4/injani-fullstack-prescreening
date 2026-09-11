FROM node:20-slim

# Install OpenSSL required by Prisma query engine
RUN apt-get update -y && apt-get install -y openssl ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV DATABASE_URL="file:./dev.db"
ENV NEXT_PUBLIC_BASE_URL="http://localhost:3000"

COPY package.json ./
RUN npm install --no-audit

COPY . .

# Generate Prisma client
RUN npx prisma generate

EXPOSE 3000

# Push SQLite schema, seed data, and start Next.js dev server
CMD ["sh", "-c", "npx prisma db push && npm run db:seed && npm run dev"]
