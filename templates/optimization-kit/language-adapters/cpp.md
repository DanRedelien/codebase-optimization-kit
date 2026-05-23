# C And C++ Adapter

Use this adapter when auditing C, C++, native libraries, bindings, or mixed native projects.

## Entrypoints To Check

- Build files: `CMakeLists.txt`, `Makefile`, `meson.build`, `BUILD`, `.vcxproj`, package recipes.
- Library exports, headers, generated sources, bindings, plugins, tests, examples.
- Platform-specific files, compile definitions, feature flags, and linker scripts.
- JNI, Python extensions, Node native addons, or other FFI boundaries.

## Tests

- Project build and test command: CTest, GoogleTest, Catch2, Bazel, Meson, Ninja, Make, MSBuild.
- Platform or configuration matrix when relevant.
- Sanitizers, static analysis, ABI checks, or integration tests when configured.

## Dependency Files

- CMake, Meson, Bazel, Make, Visual Studio project files.
- `conanfile.*`, `vcpkg.json`, package lockfiles.
- System package lists, Dockerfiles, CI scripts.
- Generated-code schemas and native binding manifests.

## Static Analysis Options

- Compiler warnings with the project build.
- `clang-tidy`, `cppcheck`, include-what-you-use when configured.
- Linker map files or symbol checks.
- Build graph queries from CMake, Bazel, or Meson.

## Dead-Code Caveats

- Macros, templates, and explicit instantiations can hide usage.
- Linker exports and ABI symbols can be public contracts.
- Dynamic loading through `dlopen`, `LoadLibrary`, plugin registries, or factory names can hide usage.
- Platform-specific build files can reference code unused on the current machine.
- Headers can be public API even when no local source includes them.

## Dynamic Usage Examples

Example 1: plugin loaded by symbol name.

```cpp
auto handle = dlopen(path.c_str(), RTLD_NOW);
auto create = reinterpret_cast<CreateFn>(dlsym(handle, "create_plugin"));
```

The exported `create_plugin` symbol may be required without a direct C++ call.

Example 2: macro-generated registration.

```cpp
REGISTER_COMMAND("compress", CompressCommand)
```

The command class may be discovered through a generated registry rather than direct construction.

## Evidence For Safe Removal

- Check build files for all target platforms and configurations.
- Inspect headers, exported symbols, registries, FFI bindings, and generated sources.
- Build and test the affected target configuration.
- Confirm ABI or plugin contract impact before deleting symbols or headers.
