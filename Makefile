.PHONY: clean build-dev install-dev install test lint uml watch open view

clean:
	rm -rf build/ dist/ *.egg-info
	rm -f *.drawio tests/fixtures/*.drawio
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build-dev:
	python3 -m pip install -e .

install-dev: clean build-dev

install:
	python3 -m pip install .

test:
	python3 -m pytest -v

lint:
	python3 -m ruff check src/

uml:
	whiteprint ./tests/fixtures/sample.py -o ./tests/fixtures/sample.drawio
	whiteprint ./tests/fixtures/sample.rs -o ./tests/fixtures/sample_rust.drawio

view:
	@echo "Python: tests/fixtures/sample.drawio"
	@echo "Rust:   tests/fixtures/sample_rust.drawio"

open: uml
	xdg-open "$(PWD)/tests/fixtures/sample.drawio" 2>/dev/null || open "$(PWD)/tests/fixtures/sample.drawio" 2>/dev/null || echo "Opened $(PWD)/tests/fixtures/sample.drawio"
	xdg-open "$(PWD)/tests/fixtures/sample_rust.drawio" 2>/dev/null || open "$(PWD)/tests/fixtures/sample_rust.drawio" 2>/dev/null || echo "Opened $(PWD)/tests/fixtures/sample_rust.drawio"

watch:
	@echo "Watching for changes... (press Ctrl+C to stop)"
	@while true; do \
		inotifywait -q -e modify -r src/ tests/fixtures/ 2>/dev/null || true; \
		make uml; \
	done
