QUALITY_ROOT ?= $(CURDIR)
export PYTHONPATH := $(REPOSITORY_ROOT)$(if $(PYTHONPATH),:$(PYTHONPATH))
PYTHON := python3 -B
QUALITY := $(PYTHON) -m automation.quality.runner --root "$(QUALITY_ROOT)"

build: build-server build-web build-extension
test: test-python test-tooling test-server test-web test-extension test-mailprobe test-protocol
lint: lint-repo lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql \
    format-check typecheck check-protocol
generate: generate-protocol

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
	@$(PYTHON) -m unittest discover -q -b -s . -t . -p '*_tests.py'

test-tooling:
	@$(PYTHON) -m unittest discover -q -b -s automation/quality/tests -t . -p '*tooling_checks.py'

$(QUALITY_TARGETS):
	@$(QUALITY) $@

$(APPLICATION_TARGETS):
	@$(PYTHON) -m automation.build.application $@

coverage:
	@$(PYTHON) -m automation.build.coverage_report

check-patch-coverage: coverage
	@$(PYTHON) -m automation.build.patch_coverage

generate-protocol:
	@$(PYTHON) -m protocol.generator.cli generate
check-protocol:
	@$(PYTHON) -m protocol.generator.cli check
test-protocol:
	@$(PYTHON) -m protocol.generator.cli test

$(HOST_TARGETS):
	@echo 'make $@ needs Docker. Run it on the host.' >&2; exit 1
