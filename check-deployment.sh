#!/bin/bash
# Quick deployment verification script

echo "🔍 Checking RVA Deployment..."
echo ""

# Check if containers are running
echo "📦 Container Status:"
docker ps --filter "name=rva" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Check database
echo "🗄️  Database Status:"
if docker ps | grep -q "rva-db"; then
    echo "  ✓ PostgreSQL container running"
    docker exec rva-db pg_isready -U rva && echo "  ✓ PostgreSQL accepting connections" || echo "  ✗ PostgreSQL not ready"
else
    echo "  ✗ PostgreSQL container not found"
fi
echo ""

# Check application
echo "🚀 Application Status:"
if docker ps | grep -q "rva-app"; then
    echo "  ✓ Application container running"
    
    # Check backend workers
    echo ""
    echo "  Backend worker processes:"
    docker exec rva-app ps aux | grep "[u]vicorn" | grep -v grep || echo "    ⚠️  No uvicorn workers found!"
    
    # Check database configuration
    echo ""
    echo "  Environment variables:"
    docker exec rva-app printenv | grep -E "DB_MODE|DB_URL|UVICORN_WORKERS" || echo "    ⚠️  DB env vars not set"
    
    # Test API endpoint
    echo ""
    echo "  Testing API endpoints:"
    
    # Root endpoint
    if curl -sf http://localhost:8060/ > /dev/null 2>&1; then
        echo "    ✓ Root endpoint responding"
    else
        echo "    ✗ Root endpoint failed"
    fi
    
    # Products endpoint
    if curl -sf http://localhost:8060/api/products > /dev/null 2>&1; then
        echo "    ✓ Products API responding"
        PRODUCT_COUNT=$(curl -s http://localhost:8060/api/products | grep -o '"product_id"' | wc -l)
        echo "    ✓ Found $PRODUCT_COUNT products"
    else
        echo "    ✗ Products API failed"
    fi
    
    # Auth endpoint
    if curl -sf http://localhost:8060/docs > /dev/null 2>&1; then
        echo "    ✓ API docs responding"
    else
        echo "    ✗ API docs failed"
    fi
else
    echo "  ✗ Application container not found"
fi

echo ""
echo "📝 Recent Application Logs:"
echo "----------------------------------------"
docker logs --tail=20 rva-app 2>&1 | grep -E "(🗄️|✓|✅|⚠️|❌|ERROR|Starting|Uvicorn|worker)"
echo "----------------------------------------"

echo ""
echo "📝 Database Initialization Errors (if any):"
echo "----------------------------------------"
docker logs rva-db 2>&1 | grep -i "error" | tail -5
echo "----------------------------------------"

echo ""
echo "💡 Quick Commands:"
echo "  View all app logs:  docker logs -f rva-app"
echo "  View DB logs:       docker logs -f rva-db"
echo "  Restart:            docker-compose -f docker-compose.rva-db.yml restart"
echo "  Reset database:     docker-compose -f docker-compose.rva-db.yml down && docker volume rm rva-pgdata && docker-compose -f docker-compose.rva-db.yml up -d"

