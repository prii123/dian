# Makefile para facilitar el uso de Docker

.PHONY: help build up down restart logs shell clean test health

# Variables
DOCKER_COMPOSE = docker-compose
SERVICE_NAME = dian-api
IMAGE_NAME = dian-rest-api

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construir la imagen Docker
	$(DOCKER_COMPOSE) build

up: ## Iniciar el servicio
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Servicio iniciado!"
	@echo "📍 API: http://localhost:8000"
	@echo "📚 Docs: http://localhost:8000/docs"
	@echo "🏥 Health: http://localhost:8000/health"

down: ## Detener el servicio
	$(DOCKER_COMPOSE) down

restart: ## Reiniciar el servicio
	$(DOCKER_COMPOSE) restart

logs: ## Ver logs en tiempo real
	$(DOCKER_COMPOSE) logs -f $(SERVICE_NAME)

shell: ## Entrar al contenedor
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) bash

ps: ## Ver estado de los contenedores
	$(DOCKER_COMPOSE) ps

stats: ## Ver estadísticas de uso de recursos
	docker stats $(SERVICE_NAME)

health: ## Verificar el estado del servicio
	@echo "🏥 Verificando health check..."
	@curl -s http://localhost:8000/health | jq || echo "❌ Error al conectar"

rebuild: ## Reconstruir y reiniciar
	$(DOCKER_COMPOSE) up -d --build
	@echo "✅ Servicio reconstruido y reiniciado!"

clean: ## Limpiar contenedores, volúmenes y redes
	$(DOCKER_COMPOSE) down -v
	@echo "🧹 Limpieza completa!"

clean-all: clean ## Limpiar todo incluyendo imágenes
	docker rmi $(IMAGE_NAME):latest || true
	@echo "🧹 Limpieza total completada!"

test-api: ## Probar endpoints básicos
	@echo "🧪 Probando API..."
	@echo "1️⃣ Root endpoint:"
	@curl -s http://localhost:8000/ | jq
	@echo "\n2️⃣ Health check:"
	@curl -s http://localhost:8000/health | jq
	@echo "\n✅ Pruebas completadas!"

prod: ## Ejecutar en modo producción
	@echo "🚀 Iniciando en modo producción..."
	$(DOCKER_COMPOSE) -f docker-compose.yml up -d
	@echo "✅ Servicio iniciado en modo producción!"

dev: ## Ejecutar en modo desarrollo (con reload)
	@echo "🔧 Iniciando en modo desarrollo..."
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up

install: ## Instalar dependencias (playwright)
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) playwright install chromium

# Alias comunes
start: up
stop: down
log: logs
