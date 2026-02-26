FROM node:22-bookworm-slim

WORKDIR /app

RUN corepack enable

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend/ /app/

CMD ["pnpm", "start"]
