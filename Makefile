install:
	python3 -m pip install -r requirements.txt
	python3 -m pip install -e .

prepare:
	python3 scripts/prepare_data.py

figures:
	python3 scripts/export_figures.py

lint:
	ruff check src scripts
	black --check src scripts

format:
	black src scripts
	ruff check --fix src scripts

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
