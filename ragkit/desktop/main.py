# ragkit/desktop/main.py
import sys
import os
import argparse
import uvicorn
from ragkit.api.server import app

def main():
    parser = argparse.ArgumentParser(description="Ragkit Backend")
    parser.add_argument('--port', type=int, default=8000, help="Port to run the server on")
    
    # CLI mode arguments (legacy/testing)
    parser.add_argument('command', nargs='?', choices=['preview_ingestion'])
    parser.add_argument('--file', help="Path to file")
    parser.add_argument('--config', help="JSON config string")
    
    args = parser.parse_args()
    
    if args.port:
        # Server mode (used by Desktop App)
        print(f"Starting server on port {args.port}...")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
    elif args.command == 'preview_ingestion':
        # CLI mode
        import json
        from ragkit.desktop.api import preview_ingestion
        if not args.file:
            print(json.dumps({"error": "Missing file path"}))
            return
            
        config = json.loads(args.config) if args.config else {}
        try:
            result = preview_ingestion(args.file, config)
            print(json.dumps(result, default=str))
        except Exception as e:
            print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
