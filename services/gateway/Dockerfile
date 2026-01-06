FROM node:20-alpine

WORKDIR /app

# Install dependencies (including devDependencies for build)
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Railway provides PORT env variable - don't hardcode
ENV PORT=8000

# Start server (Railway will set PORT dynamically)
CMD ["node", "dist/index.js"]
