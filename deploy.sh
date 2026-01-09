#!/bin/bash
# RVA Deployment Helper Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MODE="postgres"
PORT=8060
WORKERS=4
ACTION="start"

# Display help
show_help() {
    cat << EOF
RVA Deployment Helper

Usage: $0 [OPTIONS]

OPTIONS:
    -m, --mode MODE         Deployment mode: memory, sqlite, postgres (default: postgres)
    -p, --port PORT         Application port (default: 8060)
    -w, --workers WORKERS   Number of workers for postgres mode (default: 4)
    -a, --action ACTION     Action: start, stop, restart, logs, status, reset (default: start)
    -h, --help              Show this help message

EXAMPLES:
    # Start with PostgreSQL (production)
    $0 --mode postgres --workers 8

    # Start with SQLite (demos)
    $0 --mode sqlite

    # Start with in-memory (testing)
    $0 --mode memory

    # Check status
    $0 --action status

    # View logs
    $0 --action logs

    # Reset database
    $0 --action reset --mode postgres

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Validate mode
case $MODE in
    memory|sqlite|postgres)
        ;;
    *)
        echo -e "${RED}Invalid mode: $MODE${NC}"
        echo "Valid modes: memory, sqlite, postgres"
        exit 1
        ;;
esac

# Determine compose file
case $MODE in
    memory)
        COMPOSE_FILE="docker-compose.memory.yml"
        CONTAINER_NAME="rva-memory"
        ;;
    sqlite)
        COMPOSE_FILE="docker-compose.sqlite.yml"
        CONTAINER_NAME="rva-sqlite"
        ;;
    postgres)
        COMPOSE_FILE="docker-compose.rva-db.yml"
        CONTAINER_NAME="rva-app"
        ;;
esac

# Export environment variables
export RVA_PORT=$PORT
export UVICORN_WORKERS=$WORKERS

# Execute action
case $ACTION in
    start)
        echo -e "${BLUE}Starting RVA in ${YELLOW}${MODE}${BLUE} mode...${NC}"
        echo -e "${BLUE}Port: ${YELLOW}${PORT}${NC}"
        if [ "$MODE" = "postgres" ]; then
            echo -e "${BLUE}Workers: ${YELLOW}${WORKERS}${NC}"
        fi
        
        docker-compose -f "$COMPOSE_FILE" up -d
        
        echo ""
        echo -e "${GREEN}✓ RVA started successfully!${NC}"
        echo -e "${BLUE}Access the application at: ${YELLOW}http://localhost:${PORT}${NC}"
        echo -e "${BLUE}API docs: ${YELLOW}http://localhost:${PORT}/docs${NC}"
        echo ""
        echo -e "${BLUE}View logs: ${NC}docker logs -f ${CONTAINER_NAME}"
        ;;
    
    stop)
        echo -e "${BLUE}Stopping RVA...${NC}"
        docker-compose -f "$COMPOSE_FILE" down
        echo -e "${GREEN}✓ RVA stopped${NC}"
        ;;
    
    restart)
        echo -e "${BLUE}Restarting RVA...${NC}"
        docker-compose -f "$COMPOSE_FILE" restart
        echo -e "${GREEN}✓ RVA restarted${NC}"
        ;;
    
    logs)
        echo -e "${BLUE}Showing logs for ${CONTAINER_NAME}...${NC}"
        docker logs -f "$CONTAINER_NAME"
        ;;
    
    status)
        echo -e "${BLUE}RVA Status:${NC}"
        docker-compose -f "$COMPOSE_FILE" ps
        
        if docker ps | grep -q "$CONTAINER_NAME"; then
            echo ""
            echo -e "${GREEN}✓ RVA is running${NC}"
            echo -e "${BLUE}Health check:${NC}"
            if curl -sf "http://localhost:${PORT}/" > /dev/null; then
                echo -e "${GREEN}✓ Application is responding${NC}"
            else
                echo -e "${RED}✗ Application is not responding${NC}"
            fi
        else
            echo -e "${RED}✗ RVA is not running${NC}"
        fi
        ;;
    
    reset)
        echo -e "${YELLOW}⚠️  This will delete all data!${NC}"
        read -p "Are you sure? (yes/no): " -r
        echo
        if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo -e "${BLUE}Stopping RVA...${NC}"
            docker-compose -f "$COMPOSE_FILE" down
            
            case $MODE in
                sqlite)
                    echo -e "${BLUE}Removing SQLite volume...${NC}"
                    docker volume rm rva-sqlite-data || true
                    ;;
                postgres)
                    echo -e "${BLUE}Removing PostgreSQL volume...${NC}"
                    docker volume rm rva-pgdata || true
                    ;;
                memory)
                    echo -e "${YELLOW}Memory mode doesn't persist data${NC}"
                    ;;
            esac
            
            echo -e "${BLUE}Restarting RVA...${NC}"
            docker-compose -f "$COMPOSE_FILE" up -d
            
            echo -e "${GREEN}✓ Database reset complete${NC}"
        else
            echo -e "${YELLOW}Reset cancelled${NC}"
        fi
        ;;
    
    *)
        echo -e "${RED}Unknown action: $ACTION${NC}"
        echo "Valid actions: start, stop, restart, logs, status, reset"
        exit 1
        ;;
esac

