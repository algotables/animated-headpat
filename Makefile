
PY ?= python
PORT ?= 7860
GUI ?= app.py

.PHONY: install gui

install:
	@pip install -r requirements.txt || true
	@ffmpeg -version >/dev/null 2>&1 || echo "NOTE: Install ffmpeg: apt-get update && apt-get install -y ffmpeg"

gui: install
	@$(PY) $(GUI)
