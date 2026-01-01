# Makefile for Agricultural Management System
# Provides convenient commands for development and deployment

.PHONY: help build up down logs clean test

help:
	@echo "Agricultural Management System - Makefile Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup       - Initial setup (copy .env.example to .env)"
	@echo "  make build       - Build all Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make logs-f      - Follow logs from all services"
	@echo "  make ps          - Show running services"
	@echo "  make clean       - Stop services and remove volumes"
	@echo "  make db-reset    - Reset all databases (WARNING: deletes all data)"
	@echo ""

setup:
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created. Please edit it with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi

build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting services..."
	docker-compose up -d
	@echo ""
	@echo "Services started! Check status with: make ps"
	@echo "View logs with: make logs-f"
	@echo ""
	@echo "API Gateway: http://localhost"
	@echo "RabbitMQ Management: http://localhost:15672 (user/pass from .env)"
	@echo "MinIO Console: http://localhost:9001 (user/pass from .env)"

down:
	@echo "Stopping services..."
	docker-compose down

restart: down up

logs:
	docker-compose logs

logs-f:
	docker-compose logs -f

ps:
	@docker-compose ps

clean:
	@echo "WARNING: This will stop all services and remove all volumes (data will be lost)."
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	docker-compose down -v
	@echo "Cleanup complete."

db-reset:
	@echo "Resetting databases..."
	docker-compose down postgres
	docker volume rm application_agricole_postgres_data
	docker-compose up -d postgres
	@echo "Database reset complete. Services will recreate tables on startup."
