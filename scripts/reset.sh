#!/bin/bash

# AI Video Generator - Reset Script
# Completely resets the environment and data

set -e  # Exit on any error

echo "🔄 Resetting AI Video Generator SaaS..."
echo "====================================="

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

# Warning about data loss
print_warning "⚠️  WARNING: This will delete ALL data including:"
print_warning "   • All projects and screenplays"
print_warning "   • All uploaded files and generated content"
print_warning "   • All approval history"
print_warning "   • All export data"
print_warning "   • All user activities"
echo ""

read -p "Are you sure you want to continue? This cannot be undone. (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Reset cancelled."
    exit 0
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    print_error "docker-compose is not installed."
    exit 1
fi

print_status "Stopping all services..."
docker-compose -f docker-compose.production.yml down

print_status "Removing all volumes (this will delete all data)..."
docker-compose -f docker-compose.production.yml down -v

print_status "Removing all images to force rebuild..."
docker-compose -f docker-compose.production.yml down --rmi all

print_status "Cleaning up Docker system..."
docker system prune -f

print_status "Rebuilding all images..."
docker-compose -f docker-compose.production.yml build --no-cache

print_status "Starting infrastructure services..."
docker-compose -f docker-compose.production.yml up -d postgres redis minio

print_status "Waiting for services to initialize..."
sleep 20

print_status "Running fresh database migrations..."
docker-compose -f docker-compose.production.yml run --rm backend python backend/app/init_db.py

print_status "Initializing fresh MinIO buckets..."
docker-compose -f docker-compose.production.yml run --rm backend python backend/app/init_minio.py

print_status "Starting all application services..."
docker-compose -f docker-compose.production.yml up -d

print_success "Reset completed successfully!"

echo ""
echo "🎉 AI Video Generator has been reset!"
echo "==================================="
echo ""
echo "📱 Access Points:"
echo "  • Frontend:          http://localhost:3000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • MinIO Console:     http://localhost:9001"
echo "  • Flower (Celery):   http://localhost:5555"
echo "  • Prometheus:        http://localhost:9090"
echo "  • Grafana:           http://localhost:3001"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.production.yml ps

echo ""
echo "📝 To view logs: ./scripts/logs.sh"
echo "🛑 To stop all:  ./scripts/stop.sh"
echo ""
print_success "Fresh environment is ready!"