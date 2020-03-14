NAME=smallgat

db:
	docker run --name ${NAME}-db -e POSTGRES_PASSWORD=${PGPASSWORD} -d postgis/postgis:11-3.0

db-host:
	@docker inspect -f '{{.NetworkSettings.IPAddress}}' ${NAME}-db

psql:
	docker exec -it ${NAME}-db psql -U postgres
