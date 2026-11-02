QUALITY_ROOT ?= $(CURDIR)
export PYTHONPATH := $(REPOSITORY_ROOT)$(if $(PYTHONPATH),:$(PYTHONPATH))
export CARGO_TERM_QUIET := $(if $(VERBOSE),false,true)
PYTHON := python3 -B
# Only the two filtered suites read TEST, and no test may see it.
unexport TEST
QUALITY := $(PYTHON) -m automation.quality.runner --root "$(QUALITY_ROOT)"

test: test-python test-tooling test-server test-web test-extension test-mailprobe test-protocol
lint: lint-repo lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql lint-spelling \
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
	@TEST='$(TEST)' $(STEP) $@ $(PYTHON) -m automation.build.python_suite python

test-tooling:
	@$(STEP) $@ $(PYTHON) -m automation.build.python_suite tooling

$(QUALITY_TARGETS):
	@$(STEP) $@ $(QUALITY) $@

$(APPLICATION_TARGETS):
	@$(if $(filter test-server,$@),TEST='$(TEST)' )$(STEP) $@ $(PYTHON) -m automation.build.application $@

coverage:
	@$(STEP) $@ $(PYTHON) -m automation.build.coverage_report

check-patch-coverage:
	@$(STEP) $@ $(PYTHON) -m automation.build.patch_coverage

audit:
	@$(STEP) $@ osv-scanner scan source $(if $(VERBOSE),,--verbosity=error) --lockfile Cargo.lock \
	    --lockfile package-lock.json --lockfile automation/tooling/requirements.txt

generate-protocol:
	@$(STEP) $@ $(PYTHON) -m protocol.generator.cli generate
check-protocol:
	@$(STEP) $@ $(PYTHON) -m protocol.generator.cli check
test-protocol:
	@$(STEP) $@ $(PYTHON) -m protocol.generator.cli test

$(HOST_TARGETS):
	@echo 'make $@ needs Docker. Run it on the host.' >&2; exit 1
