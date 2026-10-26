REPOSITORY_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
QUALITY_ROOT ?= $(CURDIR)
export PYTHONPATH := $(REPOSITORY_ROOT)$(if $(PYTHONPATH),:$(PYTHONPATH))
PYTHON := python3 -B
QUALITY := $(PYTHON) -m automation.quality.runner --root "$(QUALITY_ROOT)"

QUALITY_TARGETS := lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql \
    format format-sql format-check format-check-rust format-check-javascript format-check-sql typecheck
APPLICATION_TARGETS := build-server build-web build-extension test-server test-web test-extension test-mailprobe
TARGETS := lint lint-repo lint-pr test-python test-tooling build-app test-app coverage \
    generate-protocol check-protocol test-protocol $(QUALITY_TARGETS) $(APPLICATION_TARGETS)

.DEFAULT_GOAL := lint
.PHONY: tooling $(TARGETS)
$(TARGETS): | tooling

tooling:
	@test -f /opt/quality/package-lock.json || { echo 'Run Make through docker compose -f automation/tooling/compose.yaml run --rm check' >&2; exit 1; }

lint: lint-repo lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql check-protocol
build-app: build-server build-web build-extension
test-app: test-server test-web test-extension

lint-repo:
	@$(PYTHON) -m automation.repository.check_agent_config
	@$(PYTHON) -m automation.repository.check_doc_naming
	@$(PYTHON) -m automation.repository.check_source_naming
	@$(PYTHON) -m automation.repository.check_directory_naming
	@$(PYTHON) -m automation.repository.check_schema_naming
	@$(PYTHON) -m automation.repository.check_skills
	@$(PYTHON) -m automation.release.version

lint-pr:
	@$(PYTHON) -m automation.repository.check_pr

test-python:
	@$(PYTHON) -m unittest discover -s . -t . -p '*_tests.py'

test-tooling:
	@$(PYTHON) -m unittest discover -s automation/quality/tests -t . -p '*tooling_checks.py'

$(QUALITY_TARGETS):
	@$(QUALITY) $@

$(APPLICATION_TARGETS):
	@$(PYTHON) -m automation.build.application $@

coverage:
	@$(PYTHON) -m automation.build.coverage_report

generate-protocol:
	@$(PYTHON) -m protocol.generator.cli generate
check-protocol:
	@$(PYTHON) -m protocol.generator.cli check
test-protocol:
	@$(PYTHON) -m protocol.generator.cli test
