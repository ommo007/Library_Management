import os
import sys
import logging
from app import app
import db  # Import the entire module instead of specific functions

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Starting Library Management System")
        
        # Check for template directory
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        if not os.path.exists(template_dir):
            logger.error(f"Template directory not found: {template_dir}")
            logger.info("Make sure all template files are in the correct location")
        else:
            logger.info(f"Template directory found: {template_dir}")
        
        # Initialize database
        logger.info("Initializing database tables...")
        db.create_tables()
        
        logger.info("Initializing purchase system...")
        db.initialize_purchase_system()
        
        # Register blueprint URLs for debugging
        logger.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            logger.info(f"Route: {rule}, Endpoint: {rule.endpoint}")
        
        # Start the app with better error handling
        logger.info("Starting web server on http://localhost:5000")
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}", exc_info=True)
        sys.exit(1)