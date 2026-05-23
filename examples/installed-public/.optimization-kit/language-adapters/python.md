# Python Adapter

Use this adapter when auditing Python code. It highlights common entrypoints, dependency files, static analysis options, and dynamic usage risks.

## Entrypoints To Check

- `pyproject.toml`, `setup.py`, `setup.cfg`, `tox.ini`, `noxfile.py`, `Pipfile`, `requirements*.txt`
- Console scripts and package entry points.
- `__main__.py`, CLI modules, web app factories, ASGI/WSGI apps.
- Task runners, Celery/RQ jobs, Airflow DAGs, notebooks, migrations, management commands.
- Framework discovery paths such as Django apps, Flask blueprints, FastAPI routers, pytest plugins.

## Tests

- `pytest`, `unittest`, `tox`, `nox`, `coverage`
- Framework commands such as `python manage.py test`
- Type checks with `mypy` or `pyright` when configured.

## Dependency Files

- `pyproject.toml`, `poetry.lock`, `uv.lock`, `pdm.lock`
- `requirements*.txt`, `Pipfile.lock`, `conda*.yml`
- Dockerfiles and CI files that install extra packages.

## Static Analysis Options

- `ruff`, `flake8`, `pylint`
- `mypy`, `pyright`
- `vulture` for unused code candidates, with manual review.
- Import graph tools when already present in the project.

## Dead-Code Caveats

- Imports can happen through strings, entry points, framework registries, decorators, and migration loaders.
- Test fixtures may be discovered by name from `conftest.py`.
- Modules can be loaded by packaging metadata without direct imports.
- Removing files can break pickled data, migrations, plugin loading, or CLI entry points.

## Dynamic Usage Examples

Example 1: package entry point loads a function by string.

```toml
[project.scripts]
acme = "acme.cli:main"
```

Static search may show no direct import of `acme.cli.main`, but packaging invokes it at runtime.

Example 2: framework decorator registers a route.

```python
@router.get("/health")
def health_check():
    return {"ok": True}
```

The handler may be referenced only by decorator registration, not by direct calls.

## Evidence For Safe Removal

- No references in imports, entry points, config, migrations, tests, docs, and deployment files.
- Relevant test command passes.
- Runtime path or CLI entrypoint that could load the code has been exercised.
- Rollback plan restores removed module, package metadata, and dependency files.
