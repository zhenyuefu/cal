# Repository Guidelines

## Project Structure & Module Organization
- `src/app`: App Router pages and API routes
  - Locale routes: `src/app/[locale]/{layout.tsx,page.tsx}` for `/zh` and `/fr` (root `src/app/page.tsx` redirects to `/zh`).
  - API: `src/app/api/build-ics/route.ts`.
- `src/lib`: Shared TypeScript utilities and WASM loader (`wasm.ts`, `constants.ts`).
- `public/`: Static assets and outputs: `public/wasm/ics_wasm.wasm`, `public/preprocessed/index.json`.
- `data/`: Fetched ICS and preprocessed JSON bundles under `data/preprocessed/*.json`.
- `rust/`: Rust workspace with crates: `fetcher`, `preprocess`, `ics_wasm`.
- Config: `biome.json`, `tsconfig.json`, `next.config.ts`, `postcss.config.mjs`.

## Build, Test, and Development Commands
- `bun run dev` (or `npm run dev`): Start Next.js with Turbopack.
- `bun run build` (or `npm run build`): Production build.
- `bun run start`: Serve the production build.
- `bun run lint` / `bun run format`: Lint and format via Biome.
- `bun run fetch`: Fetch raw calendar data (requires `CAL_USERNAME`, `CAL_PASSWORD`).
- `bun run preprocess`: Transform raw data into `data/preprocessed/*.json` and `public/preprocessed/index.json`.
- `bun run build:wasm`: Build Rust `ics_wasm` to `public/wasm/ics_wasm.wasm`.

## Coding Style & Naming Conventions
- Use TypeScript. Biome enforces formatting and linting (2‑space indent; fix via `bun run format`).
- Components: PascalCase (`MyWidget.tsx`); utilities: camelCase exports; folders/kebab-case.
- API routes: `src/app/api/<resource>/route.ts` with clear handler separation.
- Prefer pure functions in `src/lib`; avoid side effects in React Server Components.

## Testing Guidelines
- No test runner is configured yet. If adding tests, prefer Vitest with `*.test.ts` near sources or under `src/__tests__/`.
- Aim for coverage on `src/lib` and API routes; mock filesystem and network.

## Commit & Pull Request Guidelines
- Commits: Imperative mood and scoped (e.g., `feat: add ICS export`, `fix(api): guard empty payload`).
- PRs: Describe intent, link issues, list steps to validate, and include screenshots for UI changes.
- When changing Rust or WASM boundaries, note the required `bun run build:wasm` in the PR.
- Ensure lint/format pass and data artifacts are regenerated when relevant (`fetch`/`preprocess`).

## Security & Configuration Tips
- Store secrets in `.env.local` (never commit). Required: `CAL_USERNAME`, `CAL_PASSWORD` for fetch.
- Do not include sensitive raw data in PRs; only derived `data/preprocessed/` where appropriate.
