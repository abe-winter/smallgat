kubeconfig.yml:
	# todo: KUBECONFIG from .env-secure has a relative path, ruh roh
	gcloud container clusters get-credentials smallgat --zone us-central1-a

SQL_IP = $(shell cd ../terraform && terraform output sql_ip)
SQL_USER = $(shell cd ../terraform && terraform output sql_user)
tf-secrets.env:
	rm -f $@
	echo AUTOMIG_CON=postgresql://$(SQL_USER):$(TF_VAR_sql_readwrite_password)@$(SQL_IP)/postgres >> $@

run-migration:
	kubectl apply -k .
	kubectl create job --from=cronjob/migrate migrate-$(shell date +%Y%m%d-%H%M)
