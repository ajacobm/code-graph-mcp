# Development Dockerfile for CodeNav React Frontend
FROM node:22-slim AS development

WORKDIR /app

# Install dependencies first for better layer caching
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

# Expose development server port
EXPOSE 5173

# Run development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
