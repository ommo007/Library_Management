import os
import logging
from datetime import datetime

from flask import Flask, render_template
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager
from flask import flash, redirect, url_for, request, render_template
from db import Book

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

@app.route('/books/<int:book_id>/purchase', methods=['POST'])
@login_required
def purchase_book(book_id):
    """Route to handle book purchase requests"""
    # Add debug logging
    logger.debug(f"Purchase request received for book {book_id} by user {current_user.id}")
    logger.debug(f"User is student: {current_user.is_student()}")
    
    if not current_user.is_student():
        flash('Only students can purchase books', 'danger')
        # Fix the redirect to the correct endpoint - likely 'main.books' not 'main.book_detail'
        return redirect(url_for('main.books', id=book_id))
        
    book = Book.get_by_id(book_id)
    if not book:
        flash('Book not found', 'danger')
        return redirect(url_for('main.books'))
        
    if not book.available:
        flash('This book is not available for purchase', 'warning')
        # Fix the redirect to the correct endpoint
        return redirect(url_for('main.books', id=book_id))
    
    success, message = book.purchase(current_user.id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    # Redirect to the main books page instead of the non-existent book_detail page
    return redirect(url_for('main.books'))

# Add new routes for students
@app.route('/student')
@login_required
def student_dashboard():
    """Student dashboard with purchase options"""
    if not current_user.is_student():
        flash('Access denied. Student access only.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all available books to display
    query = """
    SELECT b.*, s.name as section_name
    FROM books b
    JOIN sections s ON b.section_id = s.id
    WHERE b.available = TRUE
    ORDER BY b.title
    """
    
    available_books = []
    try:
        conn = db.get_connection()
        with db.get_cursor(conn) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                available_books.append(Book(
                    id=row['id'],
                    title=row['title'],
                    author=row['author'],
                    isbn=row['isbn'],
                    genre=row['genre'],
                    section_id=row['section_id'],
                    available=row['available'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    section_name=row['section_name']
                ))
    except Exception as e:
        logger.error(f"Error fetching available books: {e}")
    
    return render_template('student_dashboard.html', available_books=available_books)

@app.route('/student/purchases')
@login_required
def student_purchases():
    """Display books purchased by the student"""
    if not current_user.is_student():
        flash('Access denied. Student access only.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get the student's purchased books
    query = """
    SELECT b.*, s.name as section_name, p.purchase_date, p.price
    FROM purchases p
    JOIN books b ON p.book_id = b.id
    JOIN sections s ON b.section_id = s.id
    WHERE p.user_id = %s
    ORDER BY p.purchase_date DESC
    """
    
    purchases = []
    try:
        conn = db.get_connection()
        with db.get_cursor(conn) as cursor:
            cursor.execute(query, (current_user.id,))
            rows = cursor.fetchall()
            
            for row in rows:
                book = Book(
                    id=row['id'],
                    title=row['title'],
                    author=row['author'],
                    isbn=row['isbn'],
                    genre=row['genre'],
                    section_id=row['section_id'],
                    available=row['available'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    section_name=row['section_name']
                )
                purchases.append({
                    'book': book,
                    'purchase_date': row['purchase_date'],
                    'price': row['price']
                })
    except Exception as e:
        logger.error(f"Error fetching student purchases: {e}")
    
    return render_template('student_purchases.html', purchases=purchases)