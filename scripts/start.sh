#!/bin/bash

# AI Video Generator - Start Script
# Starts all services in the correct order

set -e  # Exit on any error

echo "🚀 Starting AI Video Generator SaaS..."
echo "======================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
print_status "Checking Docker..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Check for environment file
if [ ! -f .env.production ] && [ ! -f .env ]; then
    print_warning "No environment file found. Creating from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your API keys before continuing."
    print_warning "Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, PIAPI_KEY"
    read -p "Have you updated the .env file with your API keys? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Please update the .env file with your API keys and run this script again."
        exit 1
    fi
fi

# Use production environment if available, otherwise use .env
ENV_FILE=".env"
if [ -f .env.production ]; then
    ENV_FILE=".env.production"
    print_status "Using production environment file"
fi

# Export environment variables
set -a  # automatically export all variables
source $ENV_FILE
set +a  # stop automatically exporting

print_status "Building Docker images..."
docker-compose -f docker-compose.production.yml build

print_status "Starting infrastructure services (PostgreSQL, Redis, MinIO)..."
docker-compose -f docker-compose.production.yml up -d postgres redis minio

print_status "Waiting for services to be healthy..."
sleep 15

# Check if services are healthy
print_status "Checking service health..."

# Check PostgreSQL
if docker-compose -f docker-compose.production.yml exec postgres pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} >/dev/null 2>&1; then
    print_success "PostgreSQL is ready"
else
    print_error "PostgreSQL is not ready"
    docker-compose -f docker-compose.production.yml logs postgres
    exit 1
fi

# Check Redis
if docker-compose -f docker-compose.production.yml exec redis redis-cli ping >/dev/null 2>&1; then
    print_success "Redis is ready"
else
    print_error "Redis is not ready"
    docker-compose -f docker-compose.production.yml logs redis
    exit 1
fi

# Check MinIO (might take a bit longer)
print_status "Waiting for MinIO to be ready..."
sleep 10
if curl -f http://localhost:9000/minio/health/live >/dev/null 2>&1; then
    print_success "MinIO is ready"
else
    print_warning "MinIO health check failed, but continuing..."
fi

print_status "Running database migrations..."
docker-compose -f docker-compose.production.yml run --rm backend python backend/app/init_db.py

print_status "Initializing MinIO buckets..."
docker-compose -f docker-compose.production.yml run --rm backend python backend/app/init_minio.py

print_status "Starting application services..."
docker-compose -f docker-compose.production.yml up -d backend celery_worker celery_beat

print_status "Starting frontend..."
docker-compose -f docker-compose.production.yml up -d frontend

print_status "Starting reverse proxy..."
docker-compose -f docker-compose.production.yml up -d nginx

print_status "Starting monitoring services..."
docker-compose -f docker-compose.production.yml up -d flower prometheus grafana

print_success "All services started successfully!"

echo ""
echo "🎉 AI Video Generator is now running!"
echo "=================================="
echo ""
echo "📱 Access Points:"
echo "  • Frontend:          http://localhost:3000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • MinIO Console:     http://localhost:9001"
echo "  • Flower (Celery):   http://localhost:5555"
echo "  • Prometheus:        http://localhost:9090"
echo "  • Grafana:           http://localhost:3001"
echo ""
echo "🔐 Default Credentials:"
echo "  • MinIO: ai-video-admin / (check .env file)"
echo "  • Grafana: admin / (check .env file)"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.production.yml ps

echo ""
echo "📝 To view logs: ./scripts/logs.sh"
echo "🛑 To stop all:  ./scripts/stop.sh"
echo "🔄 To restart:   ./scripts/reset.sh"
echo ""
print_success "Deployment completed successfully!"