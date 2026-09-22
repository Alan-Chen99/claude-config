.PHONY: test test-clean cov dist

test:
	pytest -q tests/

test-clean:
	psql "$(DATABASE_URL)" -c 'drop schema if exists svc_test cascade'

cov:
	pytest -q --cov=svc tests/

dist:
	python -m build
