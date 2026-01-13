install:
	poetry install

lint:
	poetry run ruff check .

run:
	poetry run database

build:
	poetry build

publish:
	poetry publish --dry-run

package-install:
	python3 -m pip install dist/*.whl
