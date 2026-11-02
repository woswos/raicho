PROGRESS := $(if $(VERBOSE),auto,quiet)
TOOLS := docker compose --progress $(PROGRESS) -f $(REPOSITORY_ROOT)automation/tooling/compose.yaml
ifdef GITHUB_EVENT_PATH
TOOLS += -f $(REPOSITORY_ROOT)automation/tooling/compose.ci.yaml
endif
ifdef RAICHO_CACHE_DIRECTORY
# Compose resolves a relative bind source from its first file's directory, so pass Make's absolute path.
override RAICHO_CACHE_DIRECTORY := $(abspath $(RAICHO_CACHE_DIRECTORY))
export RAICHO_CACHE_DIRECTORY
TOOLS += -f $(REPOSITORY_ROOT)automation/tooling/compose.cache.yaml
endif
# A linked worktree keeps its Git metadata outside the mounted checkout.
GIT_COMMON := $(shell git -C $(REPOSITORY_ROOT) rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
MOUNTS := $(if $(GIT_COMMON),$(if $(filter $(REPOSITORY_ROOT)%,$(GIT_COMMON)/),,--volume $(GIT_COMMON):$(GIT_COMMON):ro))
# Both services share the Cargo cache, so they run as the caller.
RUN := LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) VERBOSE=$(VERBOSE) TEST='$(TEST)' \
    $(strip $(TOOLS) run --rm $(MOUNTS))
CHECK := $(RUN) check make
WRITE := $(RUN) format make

.PHONY: tooling-image
tooling-image:
	@$(if $(RAICHO_CACHE_DIRECTORY),mkdir -p '$(RAICHO_CACHE_DIRECTORY)' && )$(STEP) $@ $(TOOLS) build

$(filter-out $(WRITING_TARGETS),$(CONTAINER_TARGETS)): tooling-image
	@$(CHECK) $@

$(WRITING_TARGETS): tooling-image
	@$(WRITE) $@

GIT_HEAD = $(shell git -C $(REPOSITORY_ROOT) rev-parse HEAD 2>/dev/null)
RAICHO_COMMIT ?= $(if $(GIT_HEAD),$(GIT_HEAD)$(shell git -C $(REPOSITORY_ROOT) diff --quiet HEAD -- || echo -dirty),unknown)

images:
	@RAICHO_COMMIT=$(RAICHO_COMMIT) $(STEP) $@ docker compose --progress $(PROGRESS) -f $(REPOSITORY_ROOT)compose.yaml build

QUIET_DOCKER := $(if $(VERBOSE),,COMPOSE_PROGRESS=quiet BUILDKIT_PROGRESS=quiet)
ACCEPTANCE := $(QUIET_DOCKER) $(STEP)

acceptance: acceptance-runtime acceptance-connector acceptance-credentials acceptance-browsing acceptance-mail

acceptance-runtime:
	@$(ACCEPTANCE) $@ bash $(REPOSITORY_ROOT)automation/acceptance/runtime/run.bash

acceptance-connector:
	@$(ACCEPTANCE) $@ bash $(REPOSITORY_ROOT)automation/acceptance/connector/run.bash

acceptance-credentials:
	@$(ACCEPTANCE) $@ bash $(REPOSITORY_ROOT)automation/acceptance/credentials/run.bash

acceptance-browsing:
	@$(ACCEPTANCE) $@ bash $(REPOSITORY_ROOT)automation/acceptance/browsing/run.bash

acceptance-mail:
	@$(ACCEPTANCE) $@ bash $(REPOSITORY_ROOT)mailprobe/tests/check_mail_compatibility.bash

shell: tooling-image
	@$(RUN) check bash

clean:
	@$(STEP) $@ bash $(REPOSITORY_ROOT)automation/tooling/clean.bash

mrproper:
	@$(STEP) $@ bash $(REPOSITORY_ROOT)automation/tooling/mrproper.bash

include $(REPOSITORY_ROOT)automation/tooling/deployment.mk
