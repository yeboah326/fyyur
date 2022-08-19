SHELL := /bin/zsh

create-migrations:
	source ./env/bin/activate; \
	python3.7 -m flask db init; \

migration:
	source ./env/bin/activate; \
	python3.7 -m flask db migrate; \
	python3.7 -m flask db upgrade; \

run-server:
	python3.7 -m flask run --reload