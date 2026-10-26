TOOLS := docker compose -f $(REPOSITORY_ROOT)automation/tooling/compose.yaml
ifdef GITHUB_EVENT_PATH
TOOLS += -f $(REPOSITORY_ROOT)automation/tooling/compose.ci.yaml
endif
# A linked worktree keeps its Git metadata outside the mounted checkout.
GIT_COMMON := $(shell git -C $(REPOSITORY_ROOT) rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
MOUNTS := $(if $(GIT_COMMON),$(if $(filter $(REPOSITORY_ROOT)%,$(GIT_COMMON)/),,--volume $(GIT_COMMON):$(GIT_COMMON):ro))
CHECK := $(strip $(TOOLS) run --rm $(MOUNTS)) check make
WRITE := LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(strip $(TOOLS) run --rm $(MOUNTS)) format make

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
	@docker compose -f $(REPOSITORY_ROOT)compose.yaml build
