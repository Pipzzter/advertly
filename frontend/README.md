# Advertly — Frontend

Vue 3 + TypeScript + Vite single-page app for Advertly. It provides the UI for pasting
an HTML template and raw advertorial copy, calling the backend generator, previewing the
result, and downloading it as a self-contained ZIP.

> The full project overview, architecture, and setup live in the [root README](../README.md).

## Prerequisites

- Node.js 20+

## Develop

```bash
npm install
npm run dev        # Vite dev server on http://localhost:5173
```

## Build & checks

```bash
npm run build      # type-check + production build to dist/
npm run type-check # vue-tsc, no emit
npm run lint       # eslint --fix
npm run format     # prettier
```

## Configuration

Copy `.env.example` to `.env`:

```env
VITE_API_URL=/api/v1
```

API requests target `VITE_API_URL`. In the Docker setup this path is proxied to the
backend by nginx (see `docker/frontend/nginx.conf`).

## Structure

```
src/
├── api/          # typed API clients (agents/copyInjection.ts)
├── components/   # brand, layout, and feature components
├── layouts/      # page shell
├── pages/        # HomePage, CopyInjectionPage
├── router/       # vue-router routes
└── types/        # shared types (agent registry)
```
