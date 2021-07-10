init:
	git submodule update --init --recursive
	poetry install

format:
	poetry run black .

lint:
	poetry run black --check .
	poetry run mypy

test:
	poetry run pytest

reset:
	rm -f poetry.lock
	poetry env remove python3
