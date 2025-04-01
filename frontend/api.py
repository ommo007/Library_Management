from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from db import Book, Section

api_bp = Blueprint('api', __name__)

@api_bp.route('/books')
def get_books():
    """API endpoint to get all books for frontend display"""
    section_id = request.args.get('section', type=int, default=0)
    query = request.args.get('query', '')
    
    search_results = Book.search(
        query=query if query else None,
        section_id=section_id if section_id and section_id > 0 else None,
        per_page=50  # Get more books for frontend
    )
    
    books = []
    for book in search_results['items']:
        books.append({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn,
            'genre': book.genre,
            'available': book.available,
            'section': {
                'id': book.section.id,
                'name': book.section.name
            } if book.section else None
        })
    
    return jsonify(books)

@api_bp.route('/books/<int:id>')
def get_book(id):
    """API endpoint to get a single book by ID"""
    book = Book.get_by_id(id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    book_data = {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'isbn': book.isbn,
        'genre': book.genre,
        'available': book.available,
        'section': {
            'id': book.section.id,
            'name': book.section.name
        } if book.section else None
    }
    
    return jsonify(book_data)

@api_bp.route('/sections')
def get_sections():
    """API endpoint to get all sections"""
    sections = Section.get_all()
    
    sections_data = []
    for section in sections:
        sections_data.append({
            'id': section.id,
            'name': section.name,
            'description': section.description
        })
    
    return jsonify(sections_data)

@api_bp.route('/user')
def get_user_status():
    """API endpoint to get current user status"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'username': current_user.username,
            'role': {
                'id': current_user.role.id,
                'name': current_user.role.name
            } if current_user.role else None,
            'is_admin': current_user.is_admin(),
            'is_librarian': current_user.is_librarian()
        })
    else:
        return jsonify({
            'authenticated': False
        })

@api_bp.route('/search')
def search_books():
    """API endpoint for live search functionality"""
    query = request.args.get('query', '')
    section_id = request.args.get('section', type=int, default=0)
    
    if not query and (not section_id or section_id <= 0):
        return jsonify([])
    
    search_results = Book.search(
        query=query if query else None,
        section_id=section_id if section_id and section_id > 0 else None,
        per_page=10  # Limit results for dropdown
    )
    
    books = []
    for book in search_results['items']:
        books.append({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'section': book.section.name if book.section else 'Unknown',
            'available': book.available
        })
    
    return jsonify(books)
