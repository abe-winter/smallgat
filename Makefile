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
