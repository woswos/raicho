.PHONY: lint lint-repo lint-pr lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql format format-sql format-check format-check-rust format-check-javascript format-check-sql typecheck test-tooling
.DEFAULT_GOAL := lint

TOOLING_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
QUALITY_ROOT ?= $(CURDIR)
QUALITY = python3 -B "$(TOOLING_ROOT)devbin/raicho_quality.py" --root "$(QUALITY_ROOT)"

.PHONY: tooling
tooling:
	@test -f /opt/quality/package-lock.json || { echo 'Run Make through docker compose -f compose/compose.tools.yaml run --rm check' >&2; exit 1; }

lint lint-repo lint-pr lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql format format-sql format-check format-check-rust format-check-javascript format-check-sql typecheck test-tooling: | tooling

lint: lint-repo lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql check-protocol

lint-repo:
	@python3 -B devbin/raicho_check_agent_config.py
	@python3 -B devbin/raicho_check_doc_naming.py
	@python3 -B devbin/raicho_check_source_naming.py
	@python3 -B devbin/raicho_check_skills.py
	@python3 -B -m unittest discover -s devbin -p 'raicho_*_tests.py'

lint-pr:
	@python3 -B devbin/raicho_check_pr.py

lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql:
	@$(QUALITY) $@

format format-sql format-check format-check-rust format-check-javascript format-check-sql typecheck:
	@$(QUALITY) $@

test-tooling:
	@python3 -B -m unittest discover -s devbin -p 'raicho_*tooling_checks.py'

.PHONY: build-app build-server build-web build-extension test-app test-server test-web test-extension test-mail-probe
build-app: build-server build-web build-extension
test-app: test-server test-web test-extension
build-server build-web build-extension test-server test-web test-extension test-mail-probe: | tooling

build-server build-web build-extension test-server test-web test-extension test-mail-probe:
	@python3 -B devbin/raicho_application.py $@

.PHONY: generate-protocol check-protocol test-protocol
generate-protocol check-protocol test-protocol: | tooling
generate-protocol:
	@python3 -B devbin/raicho_protocol.py generate
check-protocol:
	@python3 -B devbin/raicho_protocol.py check
test-protocol:
	@python3 -B devbin/raicho_protocol.py test
