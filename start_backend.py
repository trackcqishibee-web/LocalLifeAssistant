#!/usr/bin/env python3
"""
Startup script for the Local Life Assistant backend
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    # Change to the backend directory
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    print("🚀 Starting Local Life Assistant Backend...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the FastAPI server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped.")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
