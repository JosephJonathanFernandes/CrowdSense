#!/usr/bin/env python3
"""
Quick start script for CrowdSense Enhanced
"""

if __name__ == "__main__":
    print("🌐 Starting CrowdSense Enhanced")
    
    try:
        import subprocess
        import sys
        
        # Default to web mode - just call main.py
        subprocess.run([sys.executable, "main.py", "web"])
        
    except KeyboardInterrupt:
        print("\n👋 CrowdSense stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Try: python main.py web")
