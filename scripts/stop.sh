#!/bin/bash

# AI Video Generator - Stop Script
# Stops all services gracefully

set -e  # Exit on any error

echo "🛑 Stopping AI Video Generator SaaS..."
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

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    print_error "docker-compose is not installed."
    exit 1
fi

# Show current status
print_status "Current service status:"
docker-compose -f docker-compose.production.yml ps 2>/dev/null || echo "No services running"

print_status "Stopping all services..."

# Stop services gracefully
docker-compose -f docker-compose.production.yml down

print_success "All services stopped successfully!"

# Optional: Show remaining containers
REMAINING=$(docker ps --filter "name=ai-video" --format "table {{.Names}}\t{{.Status}}" | grep -v NAMES | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    print_warning "Some AI Video Generator containers may still be running:"
    docker ps --filter "name=ai-video" --format "table {{.Names}}\t{{.Status}}"
    echo ""
    echo "To force stop all: docker stop \$(docker ps -q --filter 'name=ai-video')"
fi

echo ""
echo "💾 Data Preservation:"
echo "  • PostgreSQL data: Preserved in Docker volume 'postgres_data'"
echo "  • MinIO data: Preserved in Docker volume 'minio_data'"
echo "  • Redis data: Preserved in Docker volume 'redis_data'"
echo ""
echo "🔄 To restart: ./scripts/start.sh"
echo "🗑️ To remove all data: docker-compose -f docker-compose.production.yml down -v"
echo ""
print_success "Stop completed successfully!"