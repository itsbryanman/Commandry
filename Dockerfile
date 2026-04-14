FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV COMMANDRY_DATA=/data/commandry
ENV COMMANDRY_DB=/data/commandry/commandry.db
ENV COMMANDRY_ADMIN_PASS=commandry

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    sqlite3 curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22.x (Vite 8+ requires Node >= 20.19)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy Commandry
COPY . /opt/commandry
WORKDIR /opt/commandry

# Python dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r commandry-api/requirements.txt

# Frontend build
RUN cd commandry-theme && npm ci && npm run build

# Make startup script executable
RUN chmod +x bin/commandry-start

# Data volume
VOLUME /data

# Expose main port
EXPOSE 10000

ENTRYPOINT ["/opt/commandry/bin/commandry-start"]
