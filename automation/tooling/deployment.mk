DEPLOYMENT_PROJECT := $(or $(RAICHO_PROJECT),$(COMPOSE_PROJECT_NAME),raicho)
DEPLOYMENT_STATE := $(or $(RAICHO_STATE_DIRECTORY),$(REPOSITORY_ROOT).raicho/$(DEPLOYMENT_PROJECT))
DEPLOYMENT_CREDENTIALS := $(DEPLOYMENT_STATE)/credentials
# Single-quotes a value for the shell, escaping the single quotes it contains.
shell_quote = '$(subst ','\'',$(1))'
QUOTED_CREDENTIALS := $(call shell_quote,$(DEPLOYMENT_CREDENTIALS))
# The credentials directory belongs to the container user, so only its existence is visible here.
# Make's wildcard splits paths on spaces, so the shell tests the quoted path instead.
ENROLLED := $(shell test -d $(QUOTED_CREDENTIALS) && printf enrolled)
DEPLOYMENT_COMPOSE := docker compose --progress $(PROGRESS) -p $(DEPLOYMENT_PROJECT) -f $(REPOSITORY_ROOT)compose.yaml
# strip would also squeeze repeated spaces inside the quoted path, so it covers only STEP.
DEPLOYMENT := $(if $(ENROLLED),RAICHO_CREDENTIAL_DIRECTORY=$(QUOTED_CREDENTIALS) )$(strip $(STEP))
DEPLOYED_COMPOSE := $(strip $(DEPLOYMENT_COMPOSE) $(if $(ENROLLED),-f $(REPOSITORY_ROOT)compose.credentials.yaml))
APPLICATION_ADDRESS := echo "Raicho: http://127.0.0.1:$${RAICHO_PORT:-8080}"

deploy:
	@DEPLOYMENT_PROJECT='$(DEPLOYMENT_PROJECT)' DEPLOYMENT_STATE=$(call shell_quote,$(DEPLOYMENT_STATE)) \
	    DEPLOYMENT_ENROLLED='$(ENROLLED)' \
	    bash $(REPOSITORY_ROOT)automation/tooling/deployment_help.bash

deploy-up: images
	@$(DEPLOYMENT) $@ $(DEPLOYED_COMPOSE) up -d --wait
	@$(APPLICATION_ADDRESS)

deploy-admin: images
	@$(DEPLOYMENT) $@ $(DEPLOYED_COMPOSE) -f $(REPOSITORY_ROOT)compose.admin.yaml up -d --wait
	@$(APPLICATION_ADDRESS)
	@echo "Thunderbird desktop: http://127.0.0.1:$${RAICHO_ADMIN_PORT:-6080}/vnc.html?autoconnect=true&resize=remote"

deploy-down:
	@$(STEP) $@ $(DEPLOYMENT_COMPOSE) down

deploy-clean: tooling-image
	@$(QUIET_DOCKER) $(STEP) $@ bash $(REPOSITORY_ROOT)automation/tooling/deploy_clean.bash

$(filter deploy-connector-%,$(DEPLOYMENT_TARGETS)): images
	@$(QUIET_DOCKER) $(STEP) $@ bash $(REPOSITORY_ROOT)deploy/credentials/connector.bash $(@:deploy-connector-%=%)
