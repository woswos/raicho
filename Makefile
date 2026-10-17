.PHONY: lint lint-repo lint-pr lint-bash lint-python lint-javascript lint-typescript lint-rust format format-check format-check-rust format-check-javascript typecheck test-tooling
.DEFAULT_GOAL := lint

TOOLING_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
QUALITY_ROOT ?= $(CURDIR)
QUALITY = python3 -B "$(TOOLING_ROOT)devbin/raicho_quality.py" --root "$(QUALITY_ROOT)"

.PHONY: tooling
tooling:
	@test -f /opt/quality/package-lock.json || { echo 'Run Make through docker compose -f compose.tools.yaml run --rm check' >&2; exit 1; }

lint lint-repo lint-pr lint-bash lint-python lint-javascript lint-typescript lint-rust format format-check format-check-rust format-check-javascript typecheck test-tooling: | tooling

lint: lint-repo lint-bash lint-python lint-javascript lint-typescript lint-rust

lint-repo:
	@python3 -B devbin/raicho_check_agent_config.py
	@python3 -B devbin/raicho_check_doc_naming.py
	@python3 -B devbin/raicho_check_skills.py
	@python3 -B -m unittest discover -s devbin -p 'raicho_*_tests.py'

lint-pr:
	@python3 -B devbin/raicho_check_pr.py

lint-bash lint-python lint-javascript lint-typescript lint-rust:
	@$(QUALITY) $@

format format-check format-check-rust format-check-javascript typecheck:
	@$(QUALITY) $@

test-tooling:
	@python3 -B -m unittest discover -s devbin -p 'raicho_tooling_checks.py'
