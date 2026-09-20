# Flinge — start / stop API + UI
ROOT     := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
RUN      := $(ROOT)/.run
API_DIR  := $(ROOT)/flinge
UI_DIR   := $(ROOT)/flinge-ui
API_PORT ?= 8765
UI_PORT  ?= 5173

.PHONY: start stop start-api start-ui stop-api stop-ui status help

help:
	@echo "make start      — start API (:$(API_PORT)) and UI (:$(UI_PORT))"
	@echo "make stop       — stop both"
	@echo "make start-api  / make stop-api"
	@echo "make start-ui   / make stop-ui"
	@echo "make status"

start: start-api start-ui
	@echo ""
	@echo "API  http://127.0.0.1:$(API_PORT)"
	@echo "UI   http://localhost:$(UI_PORT)"
	@echo "     http://localhost:$(UI_PORT)/heartbreak"

stop: stop-ui stop-api
	@echo "Stopped."

start-api:
	@mkdir -p "$(RUN)"
	@if [ -f "$(RUN)/api.pid" ] && kill -0 $$(cat "$(RUN)/api.pid") 2>/dev/null; then \
		echo "API already running (pid $$(cat "$(RUN)/api.pid"))"; \
	elif lsof -tiTCP:$(API_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
		echo "API port $(API_PORT) already in use"; \
	else \
		cd "$(API_DIR)" && nohup python -m flinge serve --host 127.0.0.1 --port $(API_PORT) \
			> "$(RUN)/api.log" 2>&1 & echo $$! > "$(RUN)/api.pid"; \
		echo "API started (pid $$(cat "$(RUN)/api.pid")) → $(RUN)/api.log"; \
	fi

start-ui:
	@mkdir -p "$(RUN)"
	@if [ -f "$(RUN)/ui.pid" ] && kill -0 $$(cat "$(RUN)/ui.pid") 2>/dev/null; then \
		echo "UI already running (pid $$(cat "$(RUN)/ui.pid"))"; \
	elif lsof -tiTCP:$(UI_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
		echo "UI port $(UI_PORT) already in use"; \
	else \
		cd "$(UI_DIR)" && nohup npm run dev -- --host 127.0.0.1 --port $(UI_PORT) \
			> "$(RUN)/ui.log" 2>&1 & echo $$! > "$(RUN)/ui.pid"; \
		echo "UI started (pid $$(cat "$(RUN)/ui.pid")) → $(RUN)/ui.log"; \
	fi

stop-api:
	@if [ -f "$(RUN)/api.pid" ]; then \
		kill $$(cat "$(RUN)/api.pid") 2>/dev/null || true; \
		rm -f "$(RUN)/api.pid"; \
	fi
	@-lsof -tiTCP:$(API_PORT) -sTCP:LISTEN 2>/dev/null | xargs kill 2>/dev/null || true
	@echo "API stopped"

stop-ui:
	@if [ -f "$(RUN)/ui.pid" ]; then \
		kill $$(cat "$(RUN)/ui.pid") 2>/dev/null || true; \
		rm -f "$(RUN)/ui.pid"; \
	fi
	@-lsof -tiTCP:$(UI_PORT) -sTCP:LISTEN 2>/dev/null | xargs kill 2>/dev/null || true
	@echo "UI stopped"

status:
	@printf "API  :$(API_PORT)  "; \
	if lsof -tiTCP:$(API_PORT) -sTCP:LISTEN >/dev/null 2>&1; then echo "up"; else echo "down"; fi
	@printf "UI   :$(UI_PORT)  "; \
	if lsof -tiTCP:$(UI_PORT) -sTCP:LISTEN >/dev/null 2>&1; then echo "up"; else echo "down"; fi
