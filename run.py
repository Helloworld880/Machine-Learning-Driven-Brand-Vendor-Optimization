#!/usr/bin/env python3
"""
Vendor Dashboard Launcher
Enhanced with new features and capabilities
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import VendorDashboard
from core.database import DatabaseManager
from core.auth import Authentication
from enhancements.workflow_engine import WorkflowEngine
from scripts.auto_backup import BackupManager
from scripts.report_scheduler import ReportScheduler
from monitoring.health_checks import HealthMonitor

class DashboardLauncher:
    def __init__(self):
        self.setup_logging()
        self.parser = self.setup_argparse()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/application.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_argparse(self):
        parser = argparse.ArgumentParser(description='Vendor Dashboard Launcher')
        
        parser.add_argument('--mode', choices=['web', 'api', 'mobile', 'cli'], 
                          default='web', help='Run mode')
        parser.add_argument('--port', type=int, default=8501, 
                          help='Port for web server')
        parser.add_argument('--host', default='0.0.0.0', 
                          help='Host for web server')
        parser.add_argument('--debug', action='store_true', 
                          help='Enable debug mode')
        parser.add_argument('--init-db', action='store_true', 
                          help='Initialize database')
        parser.add_argument('--backup', action='store_true', 
                          help='Run backup')
        parser.add_argument('--generate-reports', action='store_true', 
                          help='Generate scheduled reports')
        parser.add_argument('--health-check', action='store_true', 
                          help='Run health checks')
        
        return parser
        
    def initialize_system(self):
        """Initialize all system components"""
        self.logger.info("Initializing Vendor Dashboard System...")
        
        # Initialize database
        db_manager = DatabaseManager()
        if self.args.init_db:
            db_manager.initialize_database()
            self.logger.info("Database initialized successfully")
            
        # Initialize authentication
        auth = Authentication()
        auth.initialize_default_users()
        self.logger.info("Authentication system initialized")
        
        # Initialize workflows
        workflow_engine = WorkflowEngine()
        workflow_engine.initialize_workflows()
        self.logger.info("Workflow engine initialized")
        
    def run_web_dashboard(self):
        """Launch the web dashboard"""
        self.logger.info("Starting Web Dashboard...")
        dashboard = VendorDashboard()
        
        # Note: In production, you would use:
        # streamlit run app.py --server.port {port} --server.address {host}
        dashboard.run()
        
    def run_api_server(self):
        """Launch the API server"""
        self.logger.info("Starting API Server...")
        from core.api import APIServer
        api_server = APIServer(host=self.args.host, port=self.args.port + 1)
        api_server.run()
        
    def run_mobile_interface(self):
        """Launch mobile-optimized interface"""
        self.logger.info("Starting Mobile Interface...")
        from enhancements.mobile_dashboard import MobileDashboard
        mobile_dashboard = MobileDashboard()
        mobile_dashboard.run()
        
    def run_backup(self):
        """Execute backup procedure"""
        self.logger.info("Running backup...")
        backup_manager = BackupManager()
        backup_manager.perform_backup()
        self.logger.info("Backup completed successfully")
        
    def generate_reports(self):
        """Generate scheduled reports"""
        self.logger.info("Generating scheduled reports...")
        report_scheduler = ReportScheduler()
        report_scheduler.generate_scheduled_reports()
        self.logger.info("Report generation completed")
        
    def run_health_checks(self):
        """Execute system health checks"""
        self.logger.info("Running health checks...")
        health_monitor = HealthMonitor()
        health_report = health_monitor.run_comprehensive_checks()
        
        if health_report['status'] == 'healthy':
            self.logger.info("All health checks passed")
        else:
            self.logger.warning("Some health checks failed")
            for check, result in health_report['checks'].items():
                if not result['passed']:
                    self.logger.error(f"Check failed: {check} - {result['message']}")
                    
    def run(self):
        """Main execution method"""
        self.args = self.parser.parse_args()
        
        try:
            # System initialization
            self.initialize_system()
            
            # Execute specific tasks
            if self.args.backup:
                self.run_backup()
                
            if self.args.generate_reports:
                self.generate_reports()
                
            if self.args.health_check:
                self.run_health_checks()
                
            # Start main application based on mode
            if self.args.mode == 'web':
                self.run_web_dashboard()
            elif self.args.mode == 'api':
                self.run_api_server()
            elif self.args.mode == 'mobile':
                self.run_mobile_interface()
            elif self.args.mode == 'cli':
                self.logger.info("CLI mode activated - use specific commands")
                
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
            if self.args.debug:
                raise e
            sys.exit(1)

if __name__ == "__main__":
    launcher = DashboardLauncher()
    launcher.run()