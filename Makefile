NAME=smallgat

db:
	docker run --name ${NAME}-db -e POSTGRES_PASSWORD=${PGPASSWORD} -d postgis/postgis:11-3.0

db-host:
	@docker inspect -f '{{.NetworkSettings.IPAddress}}' ${NAME}-db

psql:
	docker exec -it ${NAME}-db psql -U postgres

init-schema:
	automig_pg --glob schema.sql init

update-schema:
	automig_pg --glob schema.sql update

redis:
	docker run -d --name ${NAME}-redis redis

redis-host:
	@docker inspect -f '{{.NetworkSettings.IPAddress}}' ${NAME}-redis

redis-cli:
	docker exec -it ${NAME}-redis redis-cli

lint:
	pylint -E . blueprints/ util/

SHA = $(shell git rev-parse --short=8 HEAD)
IMAGE = $(CONTAINER_REPO)/smallgat:$(SHA)
push-container:
	if [ -z "$(git status --untracked-files=no --porcelain)" ]; then exit 1; fi
	echo $(IMAGE)
	docker build -t $(IMAGE) .
	docker push $(IMAGE)

MIG_IMAGE = $(CONTAINER_REPO)/smallgat-migrate:$(SHA)
push-migration:
	if [ -z "$(git status --untracked-files=no --porcelain)" ]; then exit 1; fi
	echo $(MIG_IMAGE)
	docker build -t $(MIG_IMAGE) -f automig.Dockerfile .
	docker push $(MIG_IMAGE)

keyfile.json:
	# workaround for broken GCR
	gcloud iam service-accounts keys create keyfile.json --iam-account $(shell cd terraform/ && terraform output pusher_email)

docker-login: keyfile.json
	# workaround for broken GCR
	cat $< | docker login -u _json_key --password-stdin https://gcr.io
