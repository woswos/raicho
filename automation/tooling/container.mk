QUALITY_ROOT ?= $(CURDIR)
export PYTHONPATH := $(REPOSITORY_ROOT)$(if $(PYTHONPATH),:$(PYTHONPATH))
PYTHON := python3 -B
QUALITY := $(PYTHON) -m automation.quality.runner --root "$(QUALITY_ROOT)"

build: build-server build-web build-extension
test: test-python test-tooling test-server test-web test-extension test-mailprobe test-protocol
lint: lint-repo lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql \
    format-check typecheck check-protocol
generate: generate-protocol

REPOSITORY_CHECKS := automation.repository.check_agent_config automation.repository.check_doc_naming \
    automation.repository.check_source_naming automation.repository.check_directory_naming \
    automation.repository.check_schema_naming automation.repository.check_skills automation.release.version

lint-repo:
	@$(STEP) $@ sh -c 'for check in $(REPOSITORY_CHECKS); do $(PYTHON) -m "$$check" || exit; done'

lint-pr:
	@$(STEP) $@ $(PYTHON) -m automation.repository.check_pr

test-python:
	@$(STEP) $@ $(PYTHON) -m automation.build.python_tests . '*_tests.py'

test-tooling:
	@$(STEP) $@ $(PYTHON) -m automation.build.python_tests automation/quality/tests '*tooling_checks.py'

$(QUALITY_TARGETS):
	@$(STEP) $@ $(QUALITY) $@

$(APPLICATION_TARGETS):
	@$(STEP) $@ $(PYTHON) -m automation.build.application $@

coverage:
	@$(STEP) $@ $(PYTHON) -m automation.build.coverage_report

check-patch-coverage:
	@$(STEP) $@ $(PYTHON) -m automation.build.patch_coverage

generate-protocol:
	@$(STEP) $@ $(PYTHON) -m protocol.generator.cli generate
check-protocol:
	@$(STEP) $@ $(PYTHON) -m protocol.generator.cli check
test-protocol:
	@$(STEP) $@ $(PYTHON) -m protocol.generator.cli test

$(HOST_TARGETS):
	@echo 'make $@ needs Docker. Run it on the host.' >&2; exit 1
