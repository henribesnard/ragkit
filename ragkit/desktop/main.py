# ragkit/desktop/main.py
import sys
import os
import argparse
import logging
from pathlib import Path

# Setup logging
def setup_logging():
    log_dir = Path.home() / ".ragkit" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "backend.log"
    
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Also log to stdout
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)
    
    return logging.getLogger("ragkit.desktop.main")

logger = setup_logging()

try:
    import uvicorn
    # Import app inside try block to catch import errors
    from ragkit.api.server import app
except Exception as e:
    logger.critical(f"Failed to import dependencies: {e}", exc_info=True)
    sys.exit(1)

def main():
    logger.info("Starting RAGKIT Backend...")
    parser = argparse.ArgumentParser(description="Ragkit Backend")
    parser.add_argument('--port', type=int, default=8000, help="Port to run the server on")
    
    # CLI mode arguments (legacy/testing)
    parser.add_argument('command', nargs='?', choices=['preview_ingestion'])
    parser.add_argument('--file', help="Path to file")
    parser.add_argument('--config', help="JSON config string")
    
    args = parser.parse_args()
    
    try:
        if args.port:
            # Server mode (used by Desktop App)
            logger.info(f"Starting uvicorn server on port {args.port}...")
            uvicorn.run(app, host="127.0.0.1", port=args.port)
        elif args.command == 'preview_ingestion':
            # CLI mode
            import json
            from ragkit.desktop.api import preview_ingestion
            if not args.file:
                print(json.dumps({"error": "Missing file path"}))
                return
                
            config = json.loads(args.config) if args.config else {}
            result = preview_ingestion(args.file, config)
            print(json.dumps(result, default=str))
            
    except Exception as e:
        logger.error(f"Runtime error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
