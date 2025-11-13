# ============================================================================
# Multi-Stage Dockerfile for FinRisk AI Analyst API
#
# Builds production-ready container with:
# - C++ InvestTool engine (compiled from source)
# - Python finrisk_ai application
# - FastAPI server
#
# Build: docker build -t finrisk-ai:latest .
# Run:   docker run -p 8000:8000 -e GEMINI_API_KEY=$GEMINI_API_KEY finrisk-ai:latest
# ============================================================================

# ============================================================================
# Stage 1: C++ Builder
# ============================================================================
FROM python:3.11-slim AS cpp-builder

# Install C++ build dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy C++ source files
COPY *.h *.cpp CMakeLists.txt ./
COPY external/ ./external/

# Build C++ module
RUN mkdir -p build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    echo "✓ C++ module built successfully"

# ============================================================================
# Stage 2: Python Application
# ============================================================================
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Create app user (security best practice - don't run as root)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy C++ compiled module from builder stage
COPY --from=cpp-builder /build/build/investool_engine.*.so /app/build/

# Copy Python application
COPY finrisk_ai/ /app/finrisk_ai/
COPY test_*.py /app/

# Install Python dependencies
# Copy requirements first for better Docker layer caching
COPY finrisk_ai/requirements.txt /app/finrisk_ai/
RUN pip install --no-cache-dir -r finrisk_ai/requirements.txt && \
    pip install --no-cache-dir \
        fastapi \
        uvicorn[standard] \
        pydantic \
        requests \
    && rm -rf /root/.cache/pip

# Set environment variables
ENV PYTHONPATH=/app:$PYTHONPATH \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Default command: Run FastAPI server
CMD ["uvicorn", "finrisk_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================================
# Usage Examples:
#
# Build:
#   docker build -t finrisk-ai:latest .
#
# Run (development):
#   docker run -p 8000:8000 -e GEMINI_API_KEY=$GEMINI_API_KEY finrisk-ai:latest
#
# Run (production with environment file):
#   docker run -p 8000:8000 --env-file .env.production finrisk-ai:latest
#
# Run with custom port:
#   docker run -p 9000:9000 -e PORT=9000 -e GEMINI_API_KEY=$GEMINI_API_KEY finrisk-ai:latest
#
# Test health:
#   docker run -p 8000:8000 -e GEMINI_API_KEY=$GEMINI_API_KEY finrisk-ai:latest &
#   sleep 10
#   curl http://localhost:8000/health
# ============================================================================
