import os
import logging
from datetime import datetime

from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize extensions
login_manager = LoginManager()
csrf = CSRFProtect()
jwt = JWTManager()

# Create Flask app
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("SESSION_SECRET", "library_management_secret_key")
app.config["JWT_SECRET_KEY"] = os.environ.get("SESSION_SECRET", "library_management_jwt_key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 86400  # 1 day

# Initialize extensions with app
login_manager.init_app(app)
csrf.init_app(app)
jwt.init_app(app)

# Configure login
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Initialize database
with app.app_context():
    import db
    db.create_tables()
    
    # Create initial admin account if none exists
    from db import User, Role
    
    admin_role = Role.get_by_name('Admin')
    if admin_role:
        # Check if any admin user exists
        conn = db.get_connection()
        with db.get_cursor(conn) as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE role_id = %s",
                (admin_role.id,)
            )
            if cursor.fetchone()[0] == 0:
                # Create default admin account
                admin_user = User(
                    username="admin",
                    email="admin@librarylens.com",
                    role_id=admin_role.id
                )
                admin_user.set_password("admin@password")
                admin_user.create()
                logger.info("Created initial admin account (username: admin)")
            
            # Create default roles if they don't exist
            cursor.execute("SELECT COUNT(*) FROM roles WHERE name = 'Librarian'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO roles (name, description) VALUES (%s, %s)",
                    ("Librarian", "Library staff with full access")
                )
            
            cursor.execute("SELECT COUNT(*) FROM roles WHERE name = 'Student'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO roles (name, description) VALUES (%s, %s)",
                    ("Student", "Library user with limited access")
                )
                
            cursor.execute("SELECT COUNT(*) FROM roles WHERE name = 'Admin'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO roles (name, description) VALUES (%s, %s)",
                    ("Admin", "System administrator with all privileges")
                )
            
            conn.commit()

# Import and register blueprints
from routes import main_bp
from auth import auth_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from db import User
    return User.get_by_id(int(user_id))

# Context processor to inject 'now' into all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}