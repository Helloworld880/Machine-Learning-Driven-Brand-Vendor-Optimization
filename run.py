#!/usr/bin/env python3
"""
Project launcher for the current repository layout.

Supported modes:
- web: start the Streamlit dashboard
- api: start the Flask API server
- cli: verify local project initialization
"""

import argparse
import logging
import os
import subprocess
import sys

from core_modules.database import DatabaseManager


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class DashboardLauncher:
    def __init__(self):
        self.parser = self._build_parser()
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(os.path.join(BASE_DIR, "logs", "application.log")),
                logging.StreamHandler(sys.stdout),
            ],
        )
        return logging.getLogger(__name__)

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Vendor Dashboard Launcher")
        parser.add_argument("--mode", choices=["web", "api", "cli"], default="web")
        parser.add_argument("--host", default="0.0.0.0", help="Server host")
        parser.add_argument("--port", type=int, default=8501, help="Server port")
        parser.add_argument("--debug", action="store_true", help="Enable debug logging")
        parser.add_argument("--init-db", action="store_true", help="Initialize database")
        return parser

    def initialize_system(self):
        self.logger.info("Initializing project database...")
        DatabaseManager()
        self.logger.info("Database ready")

    def run_web_dashboard(self):
        self.logger.info("Starting Streamlit dashboard...")
        command = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            os.path.join(BASE_DIR, "app.py"),
            "--server.port",
            str(self.args.port),
            "--server.address",
            self.args.host,
        ]
        subprocess.run(command, check=True, cwd=BASE_DIR)

    def run_api_server(self):
        self.logger.info("Starting Flask API server...")
        command = [
            sys.executable,
            os.path.join(BASE_DIR, "run_api.py"),
            "--host",
            self.args.host,
            "--port",
            str(self.args.port),
        ]
        if self.args.debug:
            command.append("--debug")
        subprocess.run(command, check=True, cwd=BASE_DIR)

    def run_cli(self):
        self.logger.info("CLI mode: project initialization completed successfully.")
        self.logger.info("Use '--mode web' for Streamlit or '--mode api' for the Flask API.")

    def run(self):
        self.args = self.parser.parse_args()
        if self.args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        try:
            self.initialize_system()
            if self.args.mode == "web":
                self.run_web_dashboard()
            elif self.args.mode == "api":
                self.run_api_server()
            else:
                self.run_cli()
        except subprocess.CalledProcessError as exc:
            self.logger.error("Launcher command failed with exit code %s", exc.returncode)
            raise
        except Exception as exc:
            self.logger.error("Application error: %s", exc)
            raise


if __name__ == "__main__":
    DashboardLauncher().run()
