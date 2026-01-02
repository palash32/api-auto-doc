FROM node:20-alpine

WORKDIR /app

# Install dependencies (including devDependencies for build)
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:8000/health || exit 1

# Start server
CMD ["node", "dist/index.js"]
