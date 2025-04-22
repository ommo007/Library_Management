import os
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database connection parameters with specific values
DB_PARAMS = {
    'dbname': 'library-management',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}

# Connection pool
_conn = None

def get_connection():
    """Get a database connection from the pool"""
    global _conn
    if _conn is None or _conn.closed:
        try:
            logger.info(f"Connecting to PostgreSQL database on {DB_PARAMS['host']}:{DB_PARAMS['port']}")
            # Log connection parameters for debugging (mask password for security)
            debug_params = dict(DB_PARAMS)
            debug_params['password'] = '***' if debug_params['password'] else 'empty'
            logger.debug(f"Connection parameters: {debug_params}")
            
            _conn = psycopg2.connect(**DB_PARAMS)
            logger.info("Database connection established successfully")
        except psycopg2.OperationalError as e:
            logger.error(f"Could not connect to the PostgreSQL database: {e}")
            logger.info("Please ensure PostgreSQL is running and the connection parameters are correct")
            logger.info(f"Current connection parameters (host:port): {DB_PARAMS['host']}:{DB_PARAMS['port']}")
            
            # Try alternate connection method with connection string
            try:
                logger.info("Attempting alternate connection method...")
                conn_string = f"dbname='{DB_PARAMS['dbname']}' user='{DB_PARAMS['user']}' password='{DB_PARAMS['password']}' host='{DB_PARAMS['host']}' port='{DB_PARAMS['port']}'"
                _conn = psycopg2.connect(conn_string)
                logger.info("Alternative connection method successful")
                return _conn
            except Exception as alt_e:
                logger.error(f"Alternative connection method failed: {alt_e}")
            
            raise
    return _conn

def get_cursor(conn=None, cursor_factory=psycopg2.extras.DictCursor):
    """Get a cursor with the specified factory"""
    if conn is None:
        conn = get_connection()
    return conn.cursor(cursor_factory=cursor_factory)

def execute_query(query, params=None, fetch=True, commit=False):
    """Execute a query and optionally fetch results or commit changes"""
    conn = get_connection()
    try:
        with get_cursor(conn) as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            if commit:
                conn.commit()
                return cursor.rowcount
            return None
    except Exception as e:
        if commit:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise

def create_tables():
    """Create database tables if they don't exist"""
    conn = get_connection()
    try:
        with get_cursor(conn) as cursor:
            # Create roles table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(64) UNIQUE NOT NULL,
                description VARCHAR(256),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(64) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(256) NOT NULL,
                role_id INTEGER REFERENCES roles(id) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create sections table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sections (
                id SERIAL PRIMARY KEY,
                name VARCHAR(64) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create books table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                title VARCHAR(256) NOT NULL,
                author VARCHAR(128) NOT NULL,
                isbn VARCHAR(20) UNIQUE,
                genre VARCHAR(64),
                section_id INTEGER REFERENCES sections(id) NOT NULL,
                available BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            conn.commit()
            
            # Create default roles if they don't exist
            cursor.execute("SELECT COUNT(*) FROM roles WHERE name = 'Admin'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO roles (name, description) VALUES (%s, %s)",
                    ("Admin", "System administrator with full privileges")
                )
                
            cursor.execute("SELECT COUNT(*) FROM roles WHERE name = 'Librarian'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO roles (name, description) VALUES (%s, %s)",
                    ("Librarian", "Library staff with management access")
                )
            
            cursor.execute("SELECT COUNT(*) FROM roles WHERE name = 'Student'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO roles (name, description) VALUES (%s, %s)",
                    ("Student", "Library user with limited access")
                )
            
            conn.commit()
            logger.info("Database tables created successfully")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating tables: {e}")
        raise

def initialize_purchase_system():
    """Create purchase tables and initial settings"""
    conn = get_connection()
    try:
        with get_cursor(conn) as cursor:
            # Create purchases table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) NOT NULL,
                book_id INTEGER REFERENCES books(id) NOT NULL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                price NUMERIC(10, 2) NOT NULL,
                status VARCHAR(20) DEFAULT 'completed',
                UNIQUE(user_id, book_id)
            )
            """)
            
            # Create purchase settings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_settings (
                id SERIAL PRIMARY KEY,
                allow_student_purchases BOOLEAN DEFAULT TRUE,
                default_book_price NUMERIC(10, 2) DEFAULT 9.99
            )
            """)
            
            # Check if settings exist, if not create default
            cursor.execute("SELECT COUNT(*) FROM purchase_settings")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO purchase_settings (allow_student_purchases, default_book_price) VALUES (true, 9.99)"
                )
            
            conn.commit()
            logger.info("Purchase system initialized successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error initializing purchase system: {e}")
        raise

def purchase_book(user_id, book_id):
    """Process a book purchase by a student"""
    conn = get_connection()
    try:
        # First check if student purchases are allowed
        with get_cursor(conn) as cursor:
            cursor.execute("SELECT allow_student_purchases, default_book_price FROM purchase_settings LIMIT 1")
            settings = cursor.fetchone()
            
            if not settings or not settings['allow_student_purchases']:
                logger.warning("Student purchases are currently disabled")
                return False, "Book purchases are currently disabled"
            
            # Get user and verify it's a student
            cursor.execute("SELECT r.name FROM users u JOIN roles r ON u.role_id = r.id WHERE u.id = %s", (user_id,))
            user_role = cursor.fetchone()
            if not user_role or user_role['name'] != 'Student':
                logger.warning(f"Non-student user {user_id} attempted to purchase a book")
                return False, "Only students can purchase books"
            
            # Check if book exists and is available
            cursor.execute("SELECT title, available FROM books WHERE id = %s", (book_id,))
            book = cursor.fetchone()
            if not book:
                logger.warning(f"Attempted to purchase non-existent book ID {book_id}")
                return False, "Book not found"
                
            if not book['available']:
                logger.warning(f"Attempted to purchase unavailable book {book_id}")
                return False, "Book is not available for purchase"
            
            # Process the purchase
            try:
                cursor.execute(
                    "INSERT INTO purchases (user_id, book_id, price) VALUES (%s, %s, %s)",
                    (user_id, book_id, settings['default_book_price'])
                )
                
                # Update book availability
                cursor.execute("UPDATE books SET available = false WHERE id = %s", (book_id,))
                
                conn.commit()
                logger.info(f"Book {book_id} purchased successfully by user {user_id}")
                return True, f"Successfully purchased {book['title']}"
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                logger.warning(f"User {user_id} already purchased book {book_id}")
                return False, "You have already purchased this book"
                
    except Exception as e:
        conn.rollback()
        logger.error(f"Error during book purchase: {e}")
        return False, "An error occurred while processing your purchase"

# Model classes for data access

class User(UserMixin):
    def __init__(self, id=None, username=None, email=None, password_hash=None, role_id=None, 
                 created_at=None, updated_at=None, role_name=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role_id = role_id
        self.created_at = created_at
        self.updated_at = updated_at
        self._role_name = role_name
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get user by ID"""
        query = """
        SELECT u.*, r.name as role_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = %s
        """
        result = execute_query(query, (user_id,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                role_id=row['role_id'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                role_name=row['role_name']
            )
        return None
    
    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        query = """
        SELECT u.*, r.name as role_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.username = %s
        """
        result = execute_query(query, (username,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                role_id=row['role_id'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                role_name=row['role_name']
            )
        return None
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        query = """
        SELECT u.*, r.name as role_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.email = %s
        """
        result = execute_query(query, (email,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                role_id=row['role_id'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                role_name=row['role_name']
            )
        return None
    
    def create(self):
        """Create a new user"""
        query = """
        INSERT INTO users (username, email, password_hash, role_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id, created_at, updated_at
        """
        try:
            logger.info(f"Creating new user with username: {self.username}, email: {self.email}")
            
            # Make sure we have valid role_id
            if not self.role_id:
                # Default to Student role if not specified
                student_role = Role.get_by_name('Student')
                if student_role:
                    self.role_id = student_role.id
                    logger.info(f"Using default Student role (id: {self.role_id})")
                else:
                    logger.error("Failed to find Student role for new user")
                    return False
            
            conn = get_connection()
            with get_cursor(conn) as cursor:
                cursor.execute(query, (self.username, self.email, self.password_hash, self.role_id))
                row = cursor.fetchone()
                
                if row:
                    self.id = row['id']
                    self.created_at = row['created_at']
                    self.updated_at = row['updated_at']
                    conn.commit()  # Explicit commit
                    logger.info(f"User created successfully. ID: {self.id}")
                    return True
                else:
                    conn.rollback()
                    logger.error("User creation failed - no row returned")
                    return False
                    
        except psycopg2.errors.UniqueViolation as e:
            logger.error(f"User creation failed - duplicate entry: {e}")
            if 'username' in str(e).lower():
                logger.warning(f"Username '{self.username}' already exists")
            elif 'email' in str(e).lower():
                logger.warning(f"Email '{self.email}' already in use")
            return False
        except Exception as e:
            logger.error(f"User creation failed with error: {e}")
            return False

    # Add a static method for user registration
    @classmethod
    def register(cls, username, email, password, role_name='Student'):
        """Register a new user with specified credentials"""
        try:
            # Check if username or email already exists
            if cls.get_by_username(username):
                logger.warning(f"Registration failed: Username '{username}' already exists")
                return None, "Username already exists"
                
            if cls.get_by_email(email):
                logger.warning(f"Registration failed: Email '{email}' already in use")
                return None, "Email address already in use"
                
            # Get role
            role = Role.get_by_name(role_name)
            if not role:
                logger.error(f"Registration failed: Role '{role_name}' not found")
                return None, f"Role '{role_name}' not found"
                
            # Create user
            user = cls(username=username, email=email, role_id=role.id)
            user.set_password(password)
            
            if user.create():
                logger.info(f"User registered successfully: {username}")
                return user, None
            else:
                return None, "Failed to create user record"
                
        except Exception as e:
            logger.exception(f"Unexpected error during user registration: {e}")
            return None, "An unexpected error occurred"
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def is_librarian(self):
        """Check if user is a librarian"""
        return self._role_name == 'Librarian'
    
    def is_student(self):
        """Check if user is a student"""
        return self._role_name == 'Student'
        
    def is_admin(self):
        """Check if user is an admin"""
        return self._role_name == 'Admin'

class Role:
    def __init__(self, id=None, name=None, description=None, created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def get_all(cls):
        """Get all roles"""
        query = "SELECT * FROM roles ORDER BY name"
        result = execute_query(query)
        return [
            cls(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in result
        ]
    
    @classmethod
    def get_by_name(cls, name):
        """Get role by name"""
        query = "SELECT * FROM roles WHERE name = %s"
        result = execute_query(query, (name,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return None
    
    @classmethod
    def get_by_id(cls, role_id):
        """Get role by ID"""
        query = "SELECT * FROM roles WHERE id = %s"
        result = execute_query(query, (role_id,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return None

class Section:
    def __init__(self, id=None, name=None, description=None, created_at=None, updated_at=None, books=None):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at
        self.books = books or []
    
    @classmethod
    def get_all(cls):
        """Get all sections"""
        query = "SELECT * FROM sections ORDER BY name"
        result = execute_query(query)
        return [
            cls(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in result
        ]
    
    @classmethod
    def get_by_id(cls, section_id):
        """Get section by ID"""
        query = "SELECT * FROM sections WHERE id = %s"
        result = execute_query(query, (section_id,))
        if result:
            row = result[0]
            section = cls(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            
            # Get books for this section
            books_query = "SELECT * FROM books WHERE section_id = %s ORDER BY title"
            books_result = execute_query(books_query, (section_id,))
            section.books = [
                Book(
                    id=book_row['id'],
                    title=book_row['title'],
                    author=book_row['author'],
                    isbn=book_row['isbn'],
                    genre=book_row['genre'],
                    section_id=book_row['section_id'],
                    available=book_row['available'],
                    created_at=book_row['created_at'],
                    updated_at=book_row['updated_at'],
                    section_name=row['name']
                )
                for book_row in books_result
            ]
            
            return section
        return None
    
    @classmethod
    def get_by_name(cls, name):
        """Get section by name"""
        query = "SELECT * FROM sections WHERE name = %s"
        result = execute_query(query, (name,))
        if result:
            row = result[0]
            return cls(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return None
    
    def create(self):
        """Create a new section"""
        query = """
        INSERT INTO sections (name, description)
        VALUES (%s, %s)
        RETURNING id, created_at, updated_at
        """
        result = execute_query(
            query,
            (self.name, self.description),
            commit=True
        )
        if result:
            row = result[0]
            self.id = row['id']
            self.created_at = row['created_at']
            self.updated_at = row['updated_at']
            return True
        return False
    
    def update(self):
        """Update section"""
        query = """
        UPDATE sections
        SET name = %s, description = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING updated_at
        """
        result = execute_query(
            query,
            (self.name, self.description, self.id),
            commit=True
        )
        if result:
            self.updated_at = result[0]['updated_at']
            return True
        return False
    
    def delete(self):
        """Delete section"""
        query = "DELETE FROM sections WHERE id = %s"
        return execute_query(query, (self.id,), fetch=False, commit=True) > 0
    
    def count_books(self):
        """Count books in this section"""
        query = "SELECT COUNT(*) FROM books WHERE section_id = %s"
        result = execute_query(query, (self.id,))
        return result[0][0] if result else 0

class Book:
    def __init__(self, id=None, title=None, author=None, isbn=None, genre=None, section_id=None,
                available=True, created_at=None, updated_at=None, section_name=None):
        self.id = id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.genre = genre
        self.section_id = section_id
        self.available = available
        self.created_at = created_at
        self.updated_at = updated_at
        self._section_name = section_name
        self._section = None
    
    @property
    def section(self):
        """Get section for this book (lazy loading)"""
        if self._section is None and self.section_id is not None:
            self._section = Section.get_by_id(self.section_id)
        return self._section
    
    @classmethod
    def get_all(cls, page=1, per_page=12):
        """Get all books with pagination"""
        count_query = "SELECT COUNT(*) FROM books"
        count = execute_query(count_query)[0][0]
        
        offset = (page - 1) * per_page
        query = """
        SELECT b.*, s.name as section_name
        FROM books b
        JOIN sections s ON b.section_id = s.id
        ORDER BY b.title
        LIMIT %s OFFSET %s
        """
        result = execute_query(query, (per_page, offset))
        
        books = [
            cls(
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
            for row in result
        ]
        
        # Return a pagination-like object
        return {
            'items': books,
            'page': page,
            'per_page': per_page,
            'total': count,
            'pages': (count + per_page - 1) // per_page
        }
    
    @classmethod
    def get_by_id(cls, book_id):
        """Get book by ID"""
        query = """
        SELECT b.*, s.name as section_name
        FROM books b
        JOIN sections s ON b.section_id = s.id
        WHERE b.id = %s
        """
        result = execute_query(query, (book_id,))
        if result:
            row = result[0]
            return cls(
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
        return None
    
    @classmethod
    def search(cls, query=None, section_id=None, page=1, per_page=12):
        """Search books by title, author, or ISBN, and optionally filter by section"""
        params = []
        where_clauses = []
        
        if query:
            where_clauses.append("(b.title ILIKE %s OR b.author ILIKE %s OR b.isbn ILIKE %s)")
            params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
        
        if section_id:
            where_clauses.append("b.section_id = %s")
            params.append(section_id)
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Count total matches
        count_query = f"""
        SELECT COUNT(*) 
        FROM books b
        WHERE {where_clause}
        """
        count = execute_query(count_query, params)[0][0]
        
        # Get paginated results
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        query = f"""
        SELECT b.*, s.name as section_name
        FROM books b
        JOIN sections s ON b.section_id = s.id
        WHERE {where_clause}
        ORDER BY b.title
        LIMIT %s OFFSET %s
        """
        
        result = execute_query(query, params)
        
        books = [
            cls(
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
            for row in result
        ]
        
        # Return a pagination-like object
        return {
            'items': books,
            'page': page,
            'per_page': per_page,
            'total': count,
            'pages': (count + per_page - 1) // per_page
        }
    
    @classmethod
    def get_by_id(cls, book_id):
        """Get book by ID"""
        query = """
        SELECT b.*, s.name as section_name
        FROM books b
        JOIN sections s ON b.section_id = s.id
        WHERE b.id = %s
        """
        result = execute_query(query, (book_id,))
        if result:
            row = result[0]
            return cls(
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
        return None
    
    def create(self):
        """Create a new book"""
        query = """
        INSERT INTO books (title, author, isbn, genre, section_id, available)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, created_at, updated_at
        """
        result = execute_query(
            query,
            (self.title, self.author, self.isbn, self.genre, self.section_id, self.available),
            commit=True
        )
        if result:
            row = result[0]
            self.id = row['id']
            self.created_at = row['created_at']
            self.updated_at = row['updated_at']
            return True
        return False
    
    def update(self):
        """Update book"""
        query = """
        UPDATE books
        SET title = %s, author = %s, isbn = %s, genre = %s, section_id = %s, available = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING updated_at
        """
        
        logger.info(f"Updating book ID {self.id}: {self.title}")
        
        try:
            conn = get_connection()
            with get_cursor(conn) as cursor:
                cursor.execute(
                    query,
                    (self.title, self.author, self.isbn, self.genre, self.section_id, self.available, self.id)
                )
                result = cursor.fetchone()
                
                if result:
                    self.updated_at = result['updated_at']
                    conn.commit()  # Explicitly commit the transaction
                    logger.info(f"Book update committed to database: ID {self.id}")
                    return True
                else:
                    conn.rollback()
                    logger.error(f"No rows updated for book ID {self.id}")
                    return False
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating book ID {self.id}: {str(e)}")
            return False
    
    def delete(self):
        """Delete book"""
        query = "DELETE FROM books WHERE id = %s"
        return execute_query(query, (self.id,), fetch=False, commit=True) > 0
    
    def purchase(self, user_id):
        """Purchase this book for the specified user"""
        success, message = purchase_book(user_id, self.id)
        return success, message

# Helper class for pagination to mimic SQLAlchemy's pagination
class Pagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page
    
    @property
    def has_prev(self):
        return self.page > 1
    
    @property
    def has_next(self):
        return self.page < self.pages
    
    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge or
                (num > self.page - left_current - 1 and num < self.page + right_current) or
                num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num