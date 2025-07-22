# Stage 1: Build stage for dependencies
# Use a specific Python version to ensure consistency
FROM python:3.10-slim AS builder

# Install curl, gnupg for adding repositories, and build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gnupg build-essential && \
    rm -rf /var/lib/apt/lists/*

# Add NodeSource repository for Node.js 18.x (a stable LTS version)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -

# Install Node.js and npm from the newly added repository
RUN apt-get install -y --no-install-recommends nodejs

WORKDIR /app

# Copy dependency definition files, which are now expected to be in the build context root
COPY package.json package-lock.json* ./
# Use npm ci for a clean, reproducible install from the lock file
RUN npm ci

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser dependencies
RUN playwright install --with-deps chromium

# ---

# Stage 2: Final runtime stage
FROM python:3.10-slim

# Install Node.js runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/app/.local/bin:${PATH}"

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app

WORKDIR /home/app

# Copy installed Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy installed Node.js dependencies from the builder stage
COPY --from=builder /app/node_modules ./node_modules

# Copy the entire application source code from the build context
COPY . .

# Change ownership of the application directory
RUN chown -R app:app /home/app

# Switch to the non-root user
USER app

# Expose the application port
EXPOSE 8000

# Run migrations and start the application as Python modules
CMD ["sh", "-c", "python3 -m alembic upgrade head && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]