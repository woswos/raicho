PROGRESS := $(if $(VERBOSE),auto,quiet)
TOOLS := docker compose --progress $(PROGRESS) -f $(REPOSITORY_ROOT)automation/tooling/compose.yaml
ifdef GITHUB_EVENT_PATH
TOOLS += -f $(REPOSITORY_ROOT)automation/tooling/compose.ci.yaml
endif
# A linked worktree keeps its Git metadata outside the mounted checkout.
GIT_COMMON := $(shell git -C $(REPOSITORY_ROOT) rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
MOUNTS := $(if $(GIT_COMMON),$(if $(filter $(REPOSITORY_ROOT)%,$(GIT_COMMON)/),,--volume $(GIT_COMMON):$(GIT_COMMON):ro))
# Both services share the Cargo cache, so they run as the caller.
RUN := LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) CARGO_TERM_QUIET=$(if $(VERBOSE),false,true) \
    $(strip $(TOOLS) run --rm $(MOUNTS))
CHECK := $(RUN) check make
WRITE := $(RUN) format make

.PHONY: tooling-image
tooling-image:
	@$(TOOLS) build

$(filter-out build $(WRITING_TARGETS),$(CONTAINER_TARGETS)): tooling-image
	@$(CHECK) $@

$(WRITING_TARGETS): tooling-image
	@$(WRITE) $@

build: tooling-image
	@$(CHECK) build
	@$(MAKE) --no-print-directory images

images:
	@docker compose --progress $(PROGRESS) -f $(REPOSITORY_ROOT)compose.yaml build

acceptance: acceptance-runtime acceptance-connector acceptance-credentials acceptance-mail

acceptance-runtime:
	@bash $(REPOSITORY_ROOT)automation/acceptance/runtime/check_runtime.bash

acceptance-connector:
	@bash $(REPOSITORY_ROOT)automation/acceptance/connector/check_connector.bash

acceptance-credentials:
	@bash $(REPOSITORY_ROOT)automation/acceptance/credentials/check_credentials.bash

acceptance-mail:
	@bash $(REPOSITORY_ROOT)mailprobe/tests/check_mail_compatibility.bash

clean:
	@bash $(REPOSITORY_ROOT)automation/tooling/clean.bash
