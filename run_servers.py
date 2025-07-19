import subprocess
import threading
import time
import os

def run_flask_server():
    """Run the Flask PDF server"""
    print("Starting Flask PDF server on port 5001...")
    subprocess.run(["python", "pdf_server.py"])

def run_streamlit_app():
    """Run the Streamlit app"""
    print("Starting Streamlit app...")
    subprocess.run(["streamlit", "run", "app.py"])

def main():
    print("Starting both servers...")
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    # Give Flask server time to start
    time.sleep(2)
    
    # Start Streamlit app in main thread
    run_streamlit_app()

if __name__ == "__main__":
    main() 