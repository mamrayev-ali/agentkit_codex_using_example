FROM mcr.microsoft.com/devcontainers/universal:2

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Required by backend verification commands in Makefile.
RUN python3 -m pip install --no-cache-dir uv \
    && mkdir -p "${PLAYWRIGHT_BROWSERS_PATH}" \
    && pnpm dlx @playwright/test@1.52.0 install chromium \
    && chmod -R 755 "${PLAYWRIGHT_BROWSERS_PATH}"
