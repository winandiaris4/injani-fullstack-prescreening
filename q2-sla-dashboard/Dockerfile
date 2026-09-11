FROM node:22-alpine

WORKDIR /app

ENV NODE_ENV=development
ENV DATABASE_URL="file:./dev.db"
ENV NEXT_PUBLIC_BASE_URL="http://localhost:3000"

COPY package.json ./
RUN npm install

COPY . .

# Generate Prisma client
RUN npx prisma generate

EXPOSE 3000

# Push SQLite schema, seed data, and start Next.js dev server
CMD ["sh", "-c", "npx prisma db push && npm run db:seed && npm run dev"]

