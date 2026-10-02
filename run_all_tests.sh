kill $(lsof -t -i :8000) 2>/dev/null || true
.venv313/bin/python server.py > server_out.log 2>&1 &
SERVER_PID=$!
sleep 2
ARMORIQ_API_KEY="${ARMORIQ_API_KEY:-mock_key_for_testing}" .venv313/bin/pytest -v -s tests/
TEST_CODE=$?
kill $SERVER_PID
exit $TEST_CODE
