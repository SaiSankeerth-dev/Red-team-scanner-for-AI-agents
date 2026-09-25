.PHONY: test scan serve video lint clean

test:
	pytest -q

scan:
	python -m redline scan --target vulnerable
	python -m redline scan --target hardened

serve:
	python -m redline serve

video:
	python video/build_video.py

lint:
	python -m compileall -q redline

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache
