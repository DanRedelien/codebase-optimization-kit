# Go Adapter

Use this adapter when auditing Go modules, services, CLIs, libraries, or generated code.

## Entrypoints To Check

- `go.mod`, `go.work`, `main` packages, `cmd/**`
- HTTP handlers, RPC services, jobs, plugins, migrations, generated files.
- `init()` functions, build tags, `embed` directives, cgo files.
- Public packages consumed by other modules.

## Tests

- `go test ./...`
- Package-specific `go test`
- `go test -tags <tag> ./...` for important build tags.
- `go vet`, `staticcheck` when used by the project.

## Dependency Files

- `go.mod`
- `go.sum`
- `go.work`, `go.work.sum`
- Tool files, generated code configs, Dockerfiles, and CI install steps.

## Static Analysis Options

- `go test`
- `go vet`
- `staticcheck`
- `go list -deps`, `go list -json`
- `go mod graph`, `go mod why`

## Dead-Code Caveats

- `init()` can register behavior without direct calls.
- Build tags can hide platform or feature-specific usage.
- Reflection, `plugin.Open`, RPC registration, and template names can hide references.
- Public exported identifiers may be used outside the module.
- Generated files can be recreated from schemas or annotations.

## Dynamic Usage Examples

Example 1: handler registered in `init()`.

```go
func init() {
    http.HandleFunc("/debug/health", health)
}
```

The `health` function may be live even when no direct call exists.

Example 2: embedded files used by name.

```go
//go:embed templates/*.html
var templatesFS embed.FS
```

Removing a template file can break runtime lookup without changing Go imports.

## Evidence For Safe Removal

- Check imports, build tags, `init()`, generated files, embed patterns, and configs.
- Run tests for affected packages and important tags.
- Confirm public package consumers or module exports are not relying on the symbol.
- Validate deployment or runtime path when handlers, jobs, or plugins are involved.
