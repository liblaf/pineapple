default: gen-init lint

build:
    pyproject-build
    check-wheel-contents dist/*.whl
    twine check --strict dist/*

gen-init:
    ./scripts/gen-init.sh

lint: lint-python lint-toml

lint-python:
    ruff format
    ruff check --fix --statistics

lint-toml:
    sort-toml .ruff.toml pyproject.toml

upgrade:
    pixi upgrade
    just
