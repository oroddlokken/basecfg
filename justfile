# Automatically load environment variables from a .env file.
# set dotenv-load

# list all targets
default:
    @just --list

# list all variables
var:
    @just --evaluate


# run formatters
fmt:
    black src tests example
    isort src tests example

# lint the code
lint:
    tox

# lint using pyright
lint-pyright:
    PYRIGHT_PYTHON_FORCE_VERSION=latest pyright src tests example

# run all linters
lint-all:
    just lint
    just lint-pyright

# run tests
test:
    pytest tests --cov-report=html --cov=src/voecfg

# run tests in docker
test-docker:
    docker build -f Dockerfile.test --build-arg PYTHON_VERSION=3.10 -t voecfg-docker-test:py310 .
    docker build -f Dockerfile.test --build-arg PYTHON_VERSION=3.11 -t voecfg-docker-test:py311 .
    docker build -f Dockerfile.test --build-arg PYTHON_VERSION=3.12 -t voecfg-docker-test:py312 .
    docker build -f Dockerfile.test --build-arg PYTHON_VERSION=3.13 -t voecfg-docker-test:py313 .