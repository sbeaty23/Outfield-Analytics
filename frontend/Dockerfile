FROM node:24-alpine

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

CMD ["sh", "-c", "exec npm run dev -- --hostname \"$FRONTEND_HOST\" --port \"$FRONTEND_PORT\""]
