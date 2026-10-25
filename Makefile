.PHONY: lint lint-repo lint-pr lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql format format-sql format-check format-check-rust format-check-javascript format-check-sql typecheck test-tooling
.DEFAULT_GOAL := lint

TOOLING_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
QUALITY_ROOT ?= $(CURDIR)
export PYTHONPATH := $(TOOLING_ROOT)$(if $(PYTHONPATH),:$(PYTHONPATH))
QUALITY = python3 -B -m automation.quality.runner --root "$(QUALITY_ROOT)"

.PHONY: tooling
tooling:
	@test -f /opt/quality/package-lock.json || { echo 'Run Make through docker compose -f compose/compose.tools.yaml run --rm check' >&2; exit 1; }

lint lint-repo lint-pr lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql format format-sql format-check format-check-rust format-check-javascript format-check-sql typecheck test-tooling: | tooling

lint: lint-repo lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql check-protocol

lint-repo:
	@python3 -B -m automation.repository.check_agent_config
	@python3 -B -m automation.repository.check_doc_naming
	@python3 -B -m automation.repository.check_source_naming
	@python3 -B -m automation.repository.check_directory_naming
	@python3 -B -m automation.repository.check_schema_naming
	@python3 -B -m automation.repository.check_skills
	@python3 -B -m automation.release.version
	@python3 -B -m unittest discover -s automation -t . -p '*_tests.py'
	@python3 -B -m unittest discover -s extension/tests -t . -p '*_tests.py'
	@python3 -B -m unittest discover -s runtime/credentials/tests -t . -p '*_tests.py'
	@python3 -B -m unittest discover -s protocol/generator/tests -t . -p '*_tests.py'

lint-pr:
	@python3 -B -m automation.repository.check_pr

lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql:
	@$(QUALITY) $@

format format-sql format-check format-check-rust format-check-javascript format-check-sql typecheck:
	@$(QUALITY) $@

test-tooling:
	@python3 -B -m unittest discover -s automation/quality/tests -t . -p '*tooling_checks.py'

.PHONY: build-app build-server build-web build-extension test-app test-server test-web test-extension test-mailprobe
build-app: build-server build-web build-extension
test-app: test-server test-web test-extension
build-server build-web build-extension test-server test-web test-extension test-mailprobe: | tooling

build-server build-web build-extension test-server test-web test-extension test-mailprobe:
	@python3 -B -m automation.build.application $@

.PHONY: generate-protocol check-protocol test-protocol
generate-protocol check-protocol test-protocol: | tooling
generate-protocol:
	@python3 -B -m protocol.generator.cli generate
check-protocol:
	@python3 -B -m protocol.generator.cli check
test-protocol:
	@python3 -B -m protocol.generator.cli test
