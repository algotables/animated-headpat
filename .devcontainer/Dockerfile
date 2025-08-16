FROM mcr.microsoft.com/devcontainers/python:3.11

# Install ffmpeg for video encoding with VP9 and alpha support.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the codespace. When a codespace
# launches it will mount the repository at /workspaces/headpat_app.
WORKDIR /workspaces/headpat_app