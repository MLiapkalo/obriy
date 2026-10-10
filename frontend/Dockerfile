FROM ghcr.io/pnpm/pnpm:12.10.1

ENV PATH="/app/node_modules/.bin:$PATH"
WORKDIR /app

COPY pnpm-lock.yaml package.json ./
RUN --mount=type=cache,target=/pnpm/store \
    pnpm install --frozen-lockfile --store-dir /pnpm/store

COPY . .

EXPOSE 5173
CMD ["vite", "--host", "0.0.0.0"]
