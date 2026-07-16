# =============================================================================
# Elysium-Bench Docker Image
# Clean, isolated environment for reproducible benchmark runs.
# =============================================================================

FROM python:3.10-slim

LABEL org.elysium.bench.version="0.1.0"
LABEL org.elysium.bench.description="Multi-Agent Self-Improvement Benchmark"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash bench
USER bench
WORKDIR /home/bench

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy benchmark code
COPY --chown=bench:bench . /home/bench/elysium-bench

# Install the package
RUN pip install --no-cache-dir -e /home/bench/elysium-bench

WORKDIR /home/bench/elysium-bench

# Default command
ENTRYPOINT ["elysium-bench"]
CMD ["run", "--help"]
