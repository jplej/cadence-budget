.PHONY: install dev migrate migrations superuser shell prod-up prod-down

install:
	uv sync

dev:
	docker compose up -d
	uv run manage.py runserver

migrate:
	uv run manage.py migrate

migrations:
	uv run manage.py makemigrations

superuser:
	uv run manage.py createsuperuser

shell:
	uv run manage.py shell

messages:
	uv run manage.py makemessages -a
	uv run manage.py compilemessages

prod-up:
	docker compose -f docker-compose.prod.yml up --build -d

prod-down:
	docker compose -f docker-compose.prod.yml down
