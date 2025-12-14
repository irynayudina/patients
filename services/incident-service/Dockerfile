FROM node:18-alpine AS base

WORKDIR /app

# Install dependencies needed for native modules
RUN apk add --no-cache python3 make g++

# Copy package files
COPY services/incident-service/package*.json ./

# Install dependencies
RUN npm ci

# Copy Prisma schema
COPY services/incident-service/prisma ./prisma

# Generate Prisma Client
RUN npx prisma generate

# Copy source code
COPY services/incident-service ./

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Install only production dependencies
COPY services/incident-service/package*.json ./
RUN npm ci --only=production

# Copy Prisma files
COPY services/incident-service/prisma ./prisma
RUN npx prisma generate

# Copy built application
COPY --from=base /app/dist ./dist

# Expose port
EXPOSE 3003

# Run migrations and start
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/main"]

