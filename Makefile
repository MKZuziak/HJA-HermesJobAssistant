# Hermes Job Assistant: one entry point for setup and operations.
# Run `make` (or `make help`) to list the targets.

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE := docker compose
EXEC    := docker exec -u hermes hermes
EXEC_IT := docker exec -it -u hermes hermes

.PHONY: help init build up down restart ps logs shell wizard login configure install \
        profile jobs run status bootstrap backup update lint

help: ## List targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-11s\033[0m %s\n", $$1, $$2}'

# --- Lifecycle -------------------------------------------------------------

init: ## One-time host setup: folders, templates, .env, secrets.env
	@bash scripts/init-host.sh

build: ## Build the image (Hermes + Claude Code)
	$(COMPOSE) build

up: ## Start Hermes in the background
	$(COMPOSE) up -d
	@echo "Dashboard: http://localhost:9119 (admin / DASH_PASS from .env)"

down: ## Stop and remove the container (data is kept)
	$(COMPOSE) down

restart: ## Restart (cancels a scheduled run in progress)
	$(COMPOSE) restart

ps: ## Container status and health
	$(COMPOSE) ps

logs: ## Follow the logs (Ctrl-C stops following, not Hermes)
	$(COMPOSE) logs -f --tail 100

shell: ## Open a shell inside the container
	$(EXEC_IT) sh

# --- Setup -----------------------------------------------------------------

wizard: ## First-run setup wizard (answers in docs/setup.md)
	$(COMPOSE) run --rm hermes setup

login: ## Connect your Claude subscription and choose the model
	$(EXEC_IT) claude auth login
	$(EXEC_IT) hermes plugins install claude-subscription-directsdk
	$(EXEC_IT) hermes model

configure: ## Apply secrets.env and project settings (idempotent)
	@test -f secrets.env || { echo "secrets.env missing: run make init"; exit 1; }
	docker exec -i -u hermes hermes python3 /opt/hja/scripts/apply_config.py < secrets.env

install: ## Install repo skills, cron script and SOUL.md into Hermes
	$(EXEC) sh /opt/hja/scripts/install.sh

profile: ## Build the scout-profile skill from your materials
	$(EXEC) hermes chat -Q --query-file /opt/hja/prompts/build-profile.md

jobs: ## Create or update the scheduled jobs (idempotent)
	$(EXEC) sh /opt/hja/scripts/jobs.sh

bootstrap: configure restart install profile jobs ## configure, restart, install, profile, jobs

# --- Operations ------------------------------------------------------------

run: ## Run the scout now and wait for it (10-20 min)
	$(EXEC_IT) hermes cron run scout

status: ## Scheduled jobs and recent runs
	$(EXEC) hermes cron list
	$(EXEC) hermes cron runs --limit 10

backup: ## Archive repo config, Hermes state and your scout folders
	@out=$$HOME/hja-backup-$$(date +%F).tgz; \
	tar czf "$$out" -C "$$HOME" \
	  "$$(realpath --relative-to="$$HOME" "$(CURDIR)")" .hermes scout && \
	chmod 600 "$$out" && echo "Backup: $$out (contains secrets; store it safely)"

update: ## Pull the newest base image, rebuild and restart
	$(COMPOSE) build --pull --no-cache
	$(COMPOSE) up -d

lint: ## Run the same checks as CI (needs Docker)
	docker run --rm -v "$(CURDIR):/mnt:ro,Z" -w /mnt koalaman/shellcheck:stable scripts/*.sh agent/scripts/*.sh
	docker run --rm -i hadolint/hadolint < Dockerfile
	python3 -m py_compile agent/scripts/*.py && rm -rf agent/scripts/__pycache__
	DASH_PASS=lint $(COMPOSE) --env-file .env.example config -q
	@echo "lint: ok"
