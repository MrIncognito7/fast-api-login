.PHONY: install run test docker-up docker-down

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

test:
	pytest -q

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v
