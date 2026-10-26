REPOSITORY_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

QUALITY_TARGETS := lint-bash lint-python lint-javascript lint-typescript lint-rust lint-sql \
    format format-bash format-python format-javascript format-rust format-sql \
    format-check format-check-bash format-check-python format-check-javascript format-check-rust \
    format-check-sql typecheck
APPLICATION_TARGETS := build-server build-web build-extension test-server test-web test-extension test-mailprobe
PROTOCOL_TARGETS := generate-protocol check-protocol test-protocol
CONTAINER_TARGETS := build test lint generate lint-repo lint-pr test-python test-tooling coverage \
    check-patch-coverage $(QUALITY_TARGETS) $(APPLICATION_TARGETS) $(PROTOCOL_TARGETS)
WRITING_TARGETS := format format-bash format-python format-javascript format-rust format-sql \
    generate generate-protocol
HOST_TARGETS := images acceptance acceptance-runtime acceptance-connector acceptance-credentials \
    acceptance-mail clean

.DEFAULT_GOAL := lint
.PHONY: $(CONTAINER_TARGETS) $(HOST_TARGETS)

ifdef RAICHO_TOOLING_CONTAINER
include $(REPOSITORY_ROOT)automation/tooling/container.mk
else
include $(REPOSITORY_ROOT)automation/tooling/host.mk
endif
