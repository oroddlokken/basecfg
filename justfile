# list all targets
default:
    @just --list

# list all variables
var:
    @just --evaluate

# run formatters
fmt:
    uv run ruff format src tests
    uv run ruff check --fix --unsafe-fixes src tests

# lint the code
lint:
    uv run ruff format --check --diff src tests
    uv run ruff check src tests

# lint using pyright
lint-pyright:
    PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright src tests

# run all linters
lint-all:
    just lint
    just lint-pyright

# find dead code with vulture
vulture:
    uv run vulture src tests vulture_whitelist.py

# run tests
test:
    uv run pytest --timeout 30 -n 8 tests

# run only tests affected by code changes since last run
test-changed:
    uv run pytest --testmon --timeout 60 -n 8 tests

# run all tests with coverage
test-all:
    COVERAGE_CORE=sysmon uv run pytest --timeout 60 -n 8 tests --cov-report=html --cov=src/voecfg
