FROM python:3.12-slim

# Install git and other dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Set workspace as working directory
WORKDIR /github/workspace

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN echo "Working directory: $GITHUB_WORKSPACE"
RUN ls -la /github/workspace

ENTRYPOINT ["/entrypoint.sh"]
