# TypeScript And JavaScript Adapter

Use this adapter when auditing TypeScript or JavaScript code. It covers frontend, backend, build, and package usage.

## Entrypoints To Check

- `package.json` scripts, `bin`, `exports`, `main`, `module`, and `types`.
- Framework routes: Next.js, Remix, Astro, SvelteKit, Nuxt, Express, NestJS, Vite, webpack, Rollup.
- `tsconfig*.json`, build configs, test configs, lint configs, Storybook, Playwright, Cypress.
- Serverless functions, workers, cron jobs, plugin files, generated clients.

## Tests

- `npm test`, `pnpm test`, `yarn test`, `bun test`
- `vitest`, `jest`, `mocha`, `playwright`, `cypress`
- Type checks with `tsc --noEmit` when configured.
- Build commands for frontend and package exports.

## Dependency Files

- `package.json`, `package-lock.json`, `npm-shrinkwrap.json`
- `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`
- Workspace files such as `pnpm-workspace.yaml`, `lerna.json`, `turbo.json`, `nx.json`

## Static Analysis Options

- `tsc --noEmit`
- ESLint with TypeScript parser.
- `depcheck`, `ts-prune`, `knip`, or project-approved equivalents.
- Bundler warnings and tree-shaking reports when available.

## Dead-Code Caveats

- File-system routing can make files live without imports.
- Package exports can be consumed by external users.
- Build tools and test runners load config files by convention.
- Dynamic `import()`, `require()`, string keys, decorators, and dependency injection can hide usage.
- Generated code and public `.d.ts` files may be contract surfaces.

## Dynamic Usage Examples

Example 1: dynamic import from a route or feature key.

```ts
const page = await import(`./pages/${slug}.ts`);
```

Static search for a specific page module may miss this runtime load.

Example 2: package export is used externally.

```json
{
  "exports": {
    "./testing": "./src/testing.ts"
  }
}
```

`src/testing.ts` may have no internal imports but still be public API.

## Evidence For Safe Removal

- No references in source, package exports, route conventions, configs, tests, docs, or generated manifests.
- Type check and relevant build pass.
- Tests cover route, package, or plugin loading path.
- Public package exports and changelog implications are reviewed.
