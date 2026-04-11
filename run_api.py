#!/usr/bin/env python3
"""
Flask API server entrypoint for the current project.
"""

import argparse

from api import create_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vendor Dashboard API Server")
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=5000, help="API port")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    app = create_app()

    print("Starting Vendor Dashboard API Server...")
    print(f"API URL: http://{args.host}:{args.port}")
    print("Health: /api/v1/health")

    app.run(host=args.host, port=args.port, debug=args.debug)
