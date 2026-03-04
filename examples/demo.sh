#!/bin/bash
# Demo script for qlog

echo "🚀 qlog Demo"
echo "============"
echo

# Generate sample logs
echo "📝 Generating sample logs..."
mkdir -p demo_logs

cat > demo_logs/app.log << 'EOF'
2024-03-03 10:00:01 [INFO] Application started
2024-03-03 10:00:02 [INFO] Connected to database
2024-03-03 10:00:05 [ERROR] Connection timeout to redis
2024-03-03 10:00:10 [INFO] Request processed: /api/users (200)
2024-03-03 10:00:15 [WARN] Slow query detected: 2.5s
2024-03-03 10:00:20 [ERROR] Exception in handler: NullPointerException
2024-03-03 10:00:25 [INFO] Cache hit: user-12345
2024-03-03 10:00:30 [INFO] Request processed: /api/products (200)
2024-03-03 10:00:35 [ERROR] Database connection lost
2024-03-03 10:00:40 [INFO] Reconnected to database
2024-03-03 10:00:45 [INFO] Health check passed
2024-03-03 10:00:50 [ERROR] Failed to send email: SMTP timeout
2024-03-03 10:00:55 [INFO] Background job completed
EOF

cat > demo_logs/nginx.log << 'EOF'
192.168.1.100 - - [03/Mar/2024:10:00:01 +0000] "GET / HTTP/1.1" 200 1234
192.168.1.101 - - [03/Mar/2024:10:00:05 +0000] "GET /api/users HTTP/1.1" 200 567
192.168.1.102 - - [03/Mar/2024:10:00:10 +0000] "POST /api/login HTTP/1.1" 500 89
192.168.1.103 - - [03/Mar/2024:10:00:15 +0000] "GET /api/products HTTP/1.1" 200 2345
192.168.1.104 - - [03/Mar/2024:10:00:20 +0000] "GET /admin HTTP/1.1" 403 45
192.168.1.105 - - [03/Mar/2024:10:00:25 +0000] "GET /api/users/1 HTTP/1.1" 404 67
EOF

echo "✓ Generated sample logs in demo_logs/"
echo

# Index logs
echo "📊 Indexing logs..."
python3 -m qlog.cli index 'demo_logs/*.log'
echo

# Search examples
echo "🔍 Searching for 'ERROR'..."
python3 -m qlog.cli search "ERROR" --context 1
echo

echo "📈 Index statistics:"
python3 -m qlog.cli stats
echo

echo "✨ Demo complete! Try your own searches:"
echo "  python3 -m qlog.cli search 'timeout'"
echo "  python3 -m qlog.cli search '500' --context 2"
