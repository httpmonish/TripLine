kill $(lsof -t -i :8000) 2>/dev/null || true
.venv313/bin/python server.py > server_out.log 2>&1 &
SERVER_PID=$!
sleep 2
ARMORIQ_API_KEY=ak_live_87d1dc919b2fd66458f689766474e806e37c118618f8be9fb43133c1186588db .venv313/bin/pytest tests/test_phase6.py -v -s
TEST_CODE=$?
kill $SERVER_PID
cat server_out.log
exit $TEST_CODE
