# Java And JVM Adapter

Use this adapter when auditing Java, Kotlin, Scala, or mixed JVM projects. Adapt commands to the build tool in use.

## Entrypoints To Check

- `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle`, `gradle.properties`
- Application main classes, Spring Boot apps, servlet initializers, CLI commands, jobs.
- Annotations, dependency injection, reflection, ServiceLoader providers, resources.
- `src/main/resources/**`, migrations, schemas, generated sources.

## Tests

- `mvn test`, `mvn verify`
- `gradle test`, `gradle check`
- Framework integration tests and profile-specific tests.
- Static checks configured by the project.

## Dependency Files

- Maven `pom.xml`, parent POMs, BOMs.
- Gradle build files, version catalogs, lockfiles.
- `MANIFEST.MF`, service descriptors, Dockerfiles, CI files.

## Static Analysis Options

- Build tool dependency tasks.
- IDE or compiler warnings, Error Prone, Checkstyle, PMD, SpotBugs when configured.
- `jdeps` for module and dependency insight.
- Test coverage or mutation tools when already present.

## Dead-Code Caveats

- Annotations and dependency injection can instantiate classes without direct `new`.
- Reflection can load classes by string.
- Service provider files can make classes live.
- Resource names, serialization IDs, database migrations, and class names can be contracts.
- Public library APIs may be consumed outside the repo.

## Dynamic Usage Examples

Example 1: ServiceLoader provider.

```text
META-INF/services/com.acme.Plugin
```

The file may name `com.acme.impl.ZipPlugin`, making it live without direct source references.

Example 2: Spring component discovery.

```java
@Component
class InvoiceJob implements Runnable {
    public void run() {}
}
```

The class can be instantiated by component scanning rather than explicit construction.

## Evidence For Safe Removal

- Check source references, annotations, resources, service descriptors, reflection strings, and framework config.
- Run unit and integration tests for affected profiles.
- Verify package exports, public APIs, migrations, and serialized data contracts.
- Include rollback for source, resources, and dependency metadata.
