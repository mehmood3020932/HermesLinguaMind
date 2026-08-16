#!/bin/bash
# Hermes LinguaMind — Stop All Services Script

echo "Stopping Hermes LinguaMind Backend Services..."

if [ -f ".pids" ]; then
    while IFS=: read -r service pid port; do
        if kill "$pid" 2>/dev/null; then
            echo "✅ Stopped $service (PID: $pid)"
        else
            echo "⚠️  $service was not running"
        fi
    done < .pids
    rm -f .pids
    echo "All services stopped."
else
    echo "No PID file found. Services may not be running."
fi

# Kill any remaining Python processes on Hermes ports
for port in 8000 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8011 8012 8013 8014 8015 8016 8017 8018 8019; do
    pid=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        kill "$pid" 2>/dev/null
        echo "Stopped process on port $port"
    fi
done
