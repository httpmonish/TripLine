import subprocess
import time
import sys

def main():
    print("Starting Tripline Demo...")
    
    # 1. Prepare
    subprocess.run([sys.executable, "demo/prepare_demo.py"], check=True)
    
    # 2. Start MCP server
    print("Starting server...")
    server = subprocess.Popen([sys.executable, "server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    
    # 3. Start Dashboard
    print("Starting dashboard...")
    dashboard = subprocess.Popen([sys.executable, "-m", "uvicorn", "dashboard.app:app", "--port", "8080"])
    time.sleep(2)
    
    print("\n" + "="*50)
    print("Tripline Demo Environment is LIVE.")
    print("Dashboard available at: http://localhost:8080")
    print("Demo Runs (Attack A and B) pre-populated for deterministic fallback.")
    print("="*50 + "\n")
    
    print("Press Ctrl+C to stop.")
    try:
        dashboard.wait()
    except KeyboardInterrupt:
        pass
    finally:
        print("Cleaning up...")
        server.kill()
        dashboard.kill()
        
if __name__ == "__main__":
    main()
