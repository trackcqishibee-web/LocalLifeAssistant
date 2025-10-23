#!/bin/bash

# Docker Management Script for Local Life Assistant
# This script provides easy management commands for Docker deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from the deploy/docker directory."
    exit 1
fi

# Function to show usage
show_usage() {
    echo "🐳 Local Life Assistant Docker Management"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  build     - Build all Docker images"
    echo "  logs      - Show logs for all services"
    echo "  status    - Show status of all services"
    echo "  update    - Update and restart services"
    echo "  clean     - Clean up unused Docker resources"
    echo "  backup    - Backup ChromaDB data"
    echo "  restore   - Restore ChromaDB data from backup"
    echo ""
}

# Function to start services
start_services() {
    print_status "Starting Local Life Assistant services..."
    docker-compose up -d
    print_status "Services started successfully!"
    echo "🌐 Frontend: http://localhost"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📊 Health Check: http://localhost:8000/health"
}

# Function to stop services
stop_services() {
    print_status "Stopping Local Life Assistant services..."
    docker-compose down
    print_status "Services stopped successfully!"
}

# Function to restart services
restart_services() {
    print_status "Restarting Local Life Assistant services..."
    docker-compose restart
    print_status "Services restarted successfully!"
}

# Function to build images
build_images() {
    print_status "Building Docker images..."
    docker-compose build --no-cache
    print_status "Images built successfully!"
}

# Function to show logs
show_logs() {
    print_status "Showing logs (Press Ctrl+C to exit)..."
    docker-compose logs -f
}

# Function to show status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    echo ""
    print_status "Docker System Info:"
    docker system df
}

# Function to update services
update_services() {
    print_status "Updating Local Life Assistant..."
    git pull
    docker-compose build
    docker-compose up -d
    print_status "Update complete!"
}

# Function to clean up
clean_up() {
    print_warning "Cleaning up unused Docker resources..."
    docker system prune -f
    docker volume prune -f
    print_status "Cleanup complete!"
}

# Function to backup data
backup_data() {
    BACKUP_FILE="chroma_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    print_status "Creating backup: $BACKUP_FILE"
    docker run --rm -v locallifeassistant_chroma_data:/data -v $(pwd):/backup alpine tar czf /backup/$BACKUP_FILE -C /data .
    print_status "Backup created: $BACKUP_FILE"
}

# Function to restore data
restore_data() {
    if [ -z "$1" ]; then
        print_error "Please provide backup file: $0 restore backup_file.tar.gz"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        exit 1
    fi
    
    print_warning "Restoring from backup: $1"
    print_warning "This will overwrite existing data. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        docker run --rm -v locallifeassistant_chroma_data:/data -v $(pwd):/backup alpine tar xzf /backup/$1 -C /data
        print_status "Data restored successfully!"
    else
        print_status "Restore cancelled."
    fi
}

# Main script logic
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    build)
        build_images
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    update)
        update_services
        ;;
    clean)
        clean_up
        ;;
    backup)
        backup_data
        ;;
    restore)
        restore_data "$2"
        ;;
    *)
        show_usage
        ;;
esac
