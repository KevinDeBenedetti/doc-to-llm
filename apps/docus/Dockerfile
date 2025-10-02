ARG PNPM_VERSION=10.17.1
ARG NODE_VERSION=22.20.0-slim

FROM docker.io/node:${NODE_VERSION} AS dev

WORKDIR /app

RUN npm install --ignore-scripts --location=global pnpm@${PNPM_VERSION}
COPY ./package.json ./pnpm-lock.yaml ./pnpm-workspace.yaml ./

RUN pnpm install --frozen-lockfile && pnpm store prune

COPY . .

CMD ["pnpm", "run", "dev"]