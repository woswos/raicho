DEPLOYMENT_PROJECT := $(or $(RAICHO_PROJECT),$(COMPOSE_PROJECT_NAME),raicho)
DEPLOYMENT_CREDENTIALS := $(or $(RAICHO_STATE_DIRECTORY),$(REPOSITORY_ROOT).raicho/$(DEPLOYMENT_PROJECT))/credentials
# The credentials directory belongs to the container user, so only its existence is visible here.
ENROLLED := $(wildcard $(DEPLOYMENT_CREDENTIALS)/)
DEPLOYMENT_COMPOSE := docker compose --progress $(PROGRESS) -p $(DEPLOYMENT_PROJECT) -f $(REPOSITORY_ROOT)compose.yaml
DEPLOYMENT := $(strip $(if $(ENROLLED),RAICHO_CREDENTIAL_DIRECTORY=$(DEPLOYMENT_CREDENTIALS)) $(STEP))
DEPLOYED_COMPOSE := $(strip $(DEPLOYMENT_COMPOSE) $(if $(ENROLLED),-f $(REPOSITORY_ROOT)compose.credentials.yaml))
APPLICATION_ADDRESS := echo "Raicho: http://127.0.0.1:$${RAICHO_PORT:-8080}"

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
