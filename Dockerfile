# 1. Start from an official n8n image
# Using a specific version for stability, e.g., n8nio/n8n:1.39.1 as a recent example.
# Please check Docker Hub for the latest stable or desired n8n version.
FROM n8nio/n8n:1.39.1

# 2. Switch to the root user to install system packages
USER root

# 3. Update package lists
# 4. Install python3, python3-pip, and ffmpeg
# Using --no-install-recommends to keep the image size smaller.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python packages: opencv-python and yt-dlp (using pip3)
# These will be installed globally.
RUN pip3 install --no-cache-dir \
    opencv-python \
    yt-dlp

# 6. Create an /app directory for our custom scripts and workflows
# (This step might be redundant if COPY creates it, but explicit is good)
RUN mkdir -p /app/scripts /app/workflows

# 7. Copy the local scripts/ directory into /app/scripts/ in the image
COPY scripts/ /app/scripts/

# 8. Copy the local workflows/ directory into /app/workflows/ in the image
# For n8n to auto-discover workflows, they often need to be in /home/node/.n8n/custom or /home/node/.n8n/workflows
# However, placing them in /app/workflows and letting the user mount or copy them during runtime
# (or via a custom entrypoint script) provides more flexibility and avoids issues with base image changes.
# The README will instruct on how to make n8n aware of these workflows (e.g., by mounting /app/workflows to /home/node/.n8n/custom/workflows).
COPY workflows/ /app/workflows/

# 9. Set appropriate permissions for the copied files.
# The n8n image runs processes as 'node' user (UID 1000).
# Scripts need to be readable (and executable if they are run directly, though here Python runs them).
# The /app directory and its contents will be owned by root:root after COPY if not specified otherwise.
# We change ownership to node:node to allow the n8n user full access if needed,
# and ensure readability for sure.
RUN chown -R node:node /app

# 10. Switch back to the node user (default n8n user)
USER node

# 11. Specify WORKDIR /home/node/ (this is typically the default WORKDIR for n8n images)
WORKDIR /home/node

# The base n8n image already defines the CMD and EXPOSEs the necessary port (5678).
# No need to redefine CMD or EXPOSE unless changing default behavior.
# HEALTHCHECK is also typically inherited from the base image.

# Reminder: To make workflows in /app/workflows discoverable by n8n,
# users might need to mount this directory to /home/node/.n8n/custom/workflows
# or set N8N_CUSTOM_EXTENSIONS_DIR when running the container.
# Example: docker run -v $(pwd)/workflows:/home/node/.n8n/custom/workflows ...
# Or, they can be manually imported via the n8n UI.
# For scripts in Execute Command nodes, /app/scripts/analyze_scenes.py will be the path.
