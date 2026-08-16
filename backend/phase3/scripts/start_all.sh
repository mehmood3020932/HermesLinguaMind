#!/bin/bash
# Hermes LinguaMind — Start All Services Script

echo "Starting Hermes LinguaMind Backend Services..."
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to start a service
start_service() {
    local service=$1
    local port=$2
    local dir="services/$service"

    echo -e "${YELLOW}Starting $service on port $port...${NC}"

    if [ -f "$dir/main.py" ]; then
        cd "$dir" && python main.py > "../../logs/$service.log" 2>&1 &
        local pid=$!
        echo "$service:$pid:$port" >> ../../.pids
        cd ../..
        sleep 2

        # Check if service is running
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service started successfully${NC}"
        else
            echo -e "${RED}⚠️  $service may not be responding yet${NC}"
        fi
    else
        echo -e "${RED}❌ $service/main.py not found${NC}"
    fi
}

# Create logs directory
mkdir -p logs
rm -f .pids

# Start all services
start_service "api_gateway" 8000
start_service "llm_orchestration" 8001
start_service "tts" 8002
start_service "stt" 8003
start_service "viseme" 8004
start_service "pronunciation" 8005
start_service "coin_ledger" 8006
start_service "curriculum" 8007
start_service "memory" 8008
start_service "moderation" 8009
start_service "grammar_rule_db" 8010
start_service "content_generation" 8011
start_service "personalization" 8012
start_service "gesture_emotion" 8013
start_service "leaderboard" 8014
start_service "social_exchange" 8015
start_service "anti_fraud" 8016
start_service "live_conversation" 8017
start_service "observability" 8018
start_service "security" 8019

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}All services started!${NC}"
echo -e "${GREEN}API Gateway: http://localhost:8000/docs${NC}"
echo -e "${GREEN}Run 'tail -f logs/*.log' to view logs${NC}"
echo -e "${GREEN}Run './scripts/stop_all.sh' to stop all services${NC}"
