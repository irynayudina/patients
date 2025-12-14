FROM node:18-alpine AS base

WORKDIR /app

# Install dependencies needed for native modules
RUN apk add --no-cache python3 make g++

# Copy package files
COPY services/nestjs-service/package*.json ./

# Install dependencies
RUN npm ci

# Copy proto files
COPY proto /app/proto

# Copy source code
COPY services/nestjs-service /app

# Generate protobuf stubs
RUN npm run proto:generate || echo "Proto generation skipped in build"

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Install only production dependencies
COPY services/nestjs-service/package*.json ./
RUN npm ci --only=production

# Copy built application
COPY --from=base /app/dist ./dist
COPY --from=base /app/src/generated ./src/generated

# Expose ports
EXPOSE 3000 50051

CMD ["node", "dist/main"]

