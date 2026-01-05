.PHONY: help install install-dev setup test lint format clean deploy destroy

help:
	@echo "Football Analytics Serverless - Makefile Commands"
	@echo "=================================================="
	@echo "install          - Install production dependencies"
	@echo "install-dev      - Install development dependencies"
	@echo "setup            - Complete project setup"
	@echo "test             - Run all tests"
	@echo "test-unit        - Run unit tests"
	@echo "test-integration - Run integration tests"
	@echo "test-coverage    - Run tests with coverage report"
	@echo "lint             - Run linters"
	@echo "format           - Format code with black and isort"
	@echo "type-check       - Run mypy type checker"
	@echo "clean            - Clean build artifacts"
	@echo "run-local        - Run local development server"
	@echo "generate-data    - Generate synthetic match data"
	@echo "deploy-infra     - Deploy infrastructure with Terraform"
	@echo "deploy-lambda    - Deploy Lambda functions"
	@echo "deploy           - Deploy complete system"
	@echo "destroy          - Destroy all AWS resources"
	@echo "load-test        - Run load tests"
	@echo "docs             - Generate documentation"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

setup: install-dev
	@echo "Setting up project..."
	cp config/config.example.env config/config.env
	mkdir -p data/raw data/processed data/synthetic
	mkdir -p logs
	@echo "Setup complete! Please edit config/config.env with your settings."

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term tests/

lint:
	flake8 src/ tests/
	pylint src/

format:
	black src/ tests/ scripts/
	isort src/ tests/ scripts/

type-check:
	mypy src/

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf .mypy_cache/ .tox/

run-local:
	python scripts/run_local.py

generate-data:
	python scripts/generate_synthetic_data.py --matches 10 --output data/synthetic

deploy-infra:
	cd infrastructure/terraform && terraform init && terraform apply

deploy-lambda:
	./scripts/deploy_lambda.sh

deploy: deploy-infra deploy-lambda
	@echo "Deployment complete!"

destroy:
	cd infrastructure/terraform && terraform destroy

load-test:
	./scripts/load_test.sh --scenario medium --duration 300

load-test-high:
	./scripts/load_test.sh --scenario high --duration 300

docs:
	cd docs && make html

check-deps:
	pip list --outdated

security-scan:
	bandit -r src/
	safety check

pre-commit:
	pre-commit run --all-files

init-localstack:
	docker-compose up -d
	./scripts/init_localstack.sh

stop-localstack:
	docker-compose down

all: clean install-dev test lint
