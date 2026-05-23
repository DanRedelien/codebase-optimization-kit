# Rust Adapter

Use this adapter when auditing Rust crates, workspaces, CLIs, services, or libraries.

## Entrypoints To Check

- `Cargo.toml`, workspace members, features, examples, benches, tests.
- `src/main.rs`, `src/lib.rs`, `src/bin/**`, `examples/**`, `benches/**`
- Build scripts: `build.rs`
- Macro crates, proc macros, plugin registries, generated code.
- FFI boundaries and exported symbols.

## Tests

- `cargo test`
- `cargo test --workspace`
- `cargo test --all-features` when feasible.
- `cargo clippy`, `cargo fmt --check`
- Project-specific integration, benchmark, or feature-matrix commands.

## Dependency Files

- `Cargo.toml`
- `Cargo.lock`
- `.cargo/config.toml`
- Build scripts and CI files that set features or targets.

## Static Analysis Options

- `cargo check`
- `cargo clippy`
- `cargo udeps` when available and compatible with the toolchain.
- `cargo tree` for dependency impact.
- `cargo metadata` for workspace and feature inspection.

## Dead-Code Caveats

- Feature flags can make code live only under certain builds.
- Macros can generate references invisible to simple text search.
- `build.rs` can generate source files or link native libraries.
- Public crate exports may be used by downstream crates.
- FFI symbols, serialization names, and trait implementations can be runtime contracts.

## Dynamic Usage Examples

Example 1: feature-gated module.

```rust
#[cfg(feature = "sqlite")]
mod sqlite_store;
```

The module may appear unused in a default build but be required for `--features sqlite`.

Example 2: registry through a macro.

```rust
inventory::submit! {
    Plugin::new("compress", run_compress)
}
```

The function may be discovered through registry iteration rather than direct calls.

## Evidence For Safe Removal

- Check default, workspace, and relevant feature builds.
- Confirm public exports, examples, benches, tests, and downstream contract expectations.
- Inspect `build.rs`, macros, generated code, and FFI boundaries.
- Run validation for the affected feature set or record why it cannot run.
