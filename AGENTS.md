# Repository Guidelines

## Project Structure & Module Organization
- `pages/`: Next.js pages and entry files (`_app.tsx`, `_document.tsx`, `index.tsx`).
- `public/` and `styles/`: Static assets and global styles.
- `data/`: Generated `.ics` calendar files (do not edit manually).
- `api/`: Python helpers for data generation (`data.py`, `gen*.py`, `utils.py`).
- `.github/workflows/`: Automation (GitHub Action updates calendars via Python script).

## Build, Test, and Development Commands
- Install: `bun install` (preferred) or `npm ci`.
- Dev server: `bun run dev` → starts Next.js at `http://localhost:3000`.
- Build: `bun run build` → compiles production assets.
- Start: `bun run start` → serves the production build.
- Lint: `bun run lint` → checks with ESLint (`next/core-web-vitals`).
- Update calendars (local):
  - `pip install -r requirements.txt`
  - `python getcal.py` → regenerates `.ics` files in `data/`.

## Coding Style & Naming Conventions
- Language: TypeScript (strict mode). Prefer functional React components.
- Pages: route files in `pages/` use lower-case names (e.g., `index.tsx`).
- Components: use `PascalCase` for component names and `camelCase` for variables.
- Linting: follow ESLint rules from `next/core-web-vitals`. Fix issues before pushing.

## Testing Guidelines
- No test runner is configured yet. If adding tests:
  - Place unit tests under `__tests__/` and name files `*.test.ts(x)`.
  - Prefer Jest + React Testing Library for components; consider Playwright for e2e.
  - Keep tests deterministic; avoid network calls without mocking.

## Commit & Pull Request Guidelines
- Commits: concise, imperative mood (e.g., "update calendars", "fix: handle empty events"). Group related changes.
- PRs: include a clear description, linked issues, and before/after screenshots for UI changes. Note any schema/data impacts.
- CI: ensure lint passes; regenerate `data/` locally if your change affects calendars.

## Security & Configuration Tips
- Runtime: Node `>=22 <23`, Bun `1.2.20`, Python `3.9+`.
- Do not commit secrets. For client-visible config, use `NEXT_PUBLIC_*` env vars.
- Large `.ics` assets live in `data/`; prefer scripted updates over manual edits.
