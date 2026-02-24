FROM mcr.microsoft.com/devcontainers/universal:2

# Required by backend verification commands in Makefile.
RUN python3 -m pip install --no-cache-dir uv
