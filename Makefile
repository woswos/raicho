REPOSITORY_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

QUALITY_TARGETS := lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql lint-spelling \
    format format-bash format-python format-javascript format-rust format-sql \
    format-check format-check-bash format-check-python format-check-javascript format-check-rust \
    format-check-sql format-spelling typecheck
APPLICATION_TARGETS := build-server build-web build-extension test-server test-web test-extension test-mailprobe \
    benchmark
PROTOCOL_TARGETS := generate-protocol check-protocol test-protocol
CONTAINER_TARGETS := build test lint generate lint-repo lint-pr test-python test-tooling coverage \
    check-patch-coverage $(QUALITY_TARGETS) $(APPLICATION_TARGETS) $(PROTOCOL_TARGETS)
WRITING_TARGETS := format format-bash format-python format-javascript format-rust format-sql format-spelling \
    generate generate-protocol
HOST_TARGETS := images acceptance acceptance-runtime acceptance-connector acceptance-credentials \
    acceptance-mail clean mrproper

ifneq ($(findstring xterm,${TERM}),)
    override COLOR_BLACK := $(shell tput -Txterm setaf 0)
    override COLOR_RED := $(shell tput -Txterm setaf 1)
    override COLOR_GREEN := $(shell tput -Txterm setaf 2)
    override COLOR_YELLOW := $(shell tput -Txterm setaf 3)
    override COLOR_BLUE := $(shell tput -Txterm setaf 4)
    override COLOR_PURPLE := $(shell tput -Txterm setaf 5)
    override COLOR_CYAN := $(shell tput -Txterm setaf 6)
    override COLOR_WHITE := $(shell tput -Txterm setaf 7)
    override COLOR_RESET := $(shell tput -Txterm sgr0)
else
    override COLOR_BLACK :=
    override COLOR_RED :=
    override COLOR_GREEN :=
    override COLOR_YELLOW :=
    override COLOR_BLUE :=
    override COLOR_PURPLE :=
    override COLOR_CYAN :=
    override COLOR_WHITE :=
    override COLOR_RESET :=
endif
export COLOR_BLACK COLOR_RED COLOR_GREEN COLOR_YELLOW COLOR_BLUE COLOR_PURPLE COLOR_CYAN COLOR_WHITE COLOR_RESET
STEP := bash $(REPOSITORY_ROOT)automation/tooling/step.bash

.DEFAULT_GOAL := lint
.PHONY: $(CONTAINER_TARGETS) $(HOST_TARGETS)

ifdef RAICHO_TOOLING_CONTAINER
include $(REPOSITORY_ROOT)automation/tooling/container.mk
else
include $(REPOSITORY_ROOT)automation/tooling/host.mk
endif
