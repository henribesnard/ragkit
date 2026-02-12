# ragkit/desktop/main.py
import sys
import json
import argparse
from ragkit.desktop.api import preview_ingestion

def main():
    parser = argparse.ArgumentParser(description="Ragkit Backend CLI")
    parser.add_argument('command', choices=['preview_ingestion'])
    parser.add_argument('--file', help="Path to file")
    parser.add_argument('--config', help="JSON config string")
    
    args = parser.parse_args()
    
    if args.command == 'preview_ingestion':
        if not args.file:
            print(json.dumps({"error": "Missing file path"}))
            return
            
        config = json.loads(args.config) if args.config else {}
        try:
            result = preview_ingestion(args.file, config)
            print(json.dumps(result, default=str)) # default=str handles datetime
        except Exception as e:
            print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
