#!/bin/bash

# AI Video Generator - Logs Script
# View logs from all services

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

echo "📝 AI Video Generator - Service Logs"
echo "==================================="

# Check if a specific service is requested
if [ -n "$1" ]; then
    SERVICE=$1
    print_status "Showing logs for service: $SERVICE"
    docker-compose -f docker-compose.production.yml logs -f --tail=100 $SERVICE
else
    print_status "Showing logs for all services (last 100 lines each)"
    echo ""
    echo "Available services to view individually:"
    echo "  • postgres     - PostgreSQL database"
    echo "  • redis        - Redis cache and queues" 
    echo "  • minio        - MinIO object storage"
    echo "  • backend      - FastAPI application"
    echo "  • celery_worker - Celery background tasks"
    echo "  • celery_beat  - Celery scheduler"
    echo "  • frontend     - React frontend"
    echo "  • nginx        - Reverse proxy"
    echo "  • flower       - Celery monitoring"
    echo "  • prometheus   - Metrics collection"
    echo "  • grafana      - Metrics visualization"
    echo ""
    echo "Usage: $0 [service_name] to view specific service logs"
    echo "Press Ctrl+C to exit"
    echo ""
    
    # Show all logs with color coding
    docker-compose -f docker-compose.production.yml logs -f --tail=50
fi