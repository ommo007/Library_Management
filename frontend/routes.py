from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime

from db import Book, Section, Pagination
from forms import BookForm, SectionForm, SearchForm

main_bp = Blueprint('main', __name__)

# Decorator for librarian-only routes
def librarian_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_librarian():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# Home page
@main_bp.route('/')
def index():
    return render_template('index.html')

# Books routes
@main_bp.route('/books')
@login_required
def books():
    search_form = SearchForm()
    section_id = request.args.get('section', type=int, default=0)
    search_query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)
    
    # Get paginated books using our search function
    paginated_books = Book.search(
        query=search_query if search_query else None,
        section_id=section_id if section_id else None,
        page=page,
        per_page=12
    )
    
    # Create a compatible pagination object
    books = Pagination(
        items=paginated_books['items'],
        page=paginated_books['page'],
        per_page=paginated_books['per_page'],
        total=paginated_books['total']
    )
    
    return render_template('books/index.html', books=books, form=search_form, 
                          section_id=section_id, search_query=search_query)

@main_bp.route('/books/<int:id>')
@login_required
def show_book(id):
    book = Book.get_by_id(id)
    if not book:
        abort(404)
    return render_template('books/show.html', book=book)

@main_bp.route('/books/create', methods=['GET', 'POST'])
@login_required
@librarian_required
def create_book():
    form = BookForm()
    
    if form.validate_on_submit():
        book = Book(
            title=form.title.data,
            author=form.author.data,
            isbn=form.isbn.data,
            genre=form.genre.data,
            section_id=form.section_id.data,
            available=form.available.data
        )
        
        if book.create():
            flash('Book added successfully.', 'success')
            return redirect(url_for('main.books'))
        else:
            flash('Error creating book. Please try again.', 'danger')
    
    return render_template('books/create.html', form=form)

@main_bp.route('/books/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@librarian_required
def edit_book(id):
    """Edit book details"""
    book = Book.get_by_id(id)
    if not book:
        flash('Book not found', 'danger')
        return redirect(url_for('main.books'))
    
    # Create form with original book data
    form = BookForm()
    
    # Pre-populate section choices (assuming you have a form with dropdown)
    sections = Section.get_all()
    form.section_id.choices = [(s.id, s.name) for s in sections]
    
    if request.method == 'GET':
        # Pre-populate form fields for GET request
        form.title.data = book.title
        form.author.data = book.author
        form.isbn.data = book.isbn
        form.genre.data = book.genre
        form.section_id.data = book.section_id
        form.available.data = book.available
    
    if form.validate_on_submit():
        try:
            # Update book with form data
            book.title = form.title.data
            book.author = form.author.data
            book.isbn = form.isbn.data
            book.genre = form.genre.data
            book.section_id = form.section_id.data
            book.available = form.available.data
            
            # Log the update operation
            current_app.logger.info(f"Updating book ID {id}: {book.title}")
            
            # Explicitly update and commit to database
            success = book.update()
            
            if success:
                flash('Book updated successfully', 'success')
                current_app.logger.info(f"Book ID {id} updated successfully")
                return redirect(url_for('main.books'))
            else:
                flash('Error updating book', 'danger')
                current_app.logger.error(f"Database error updating book ID {id}")
        except Exception as e:
            current_app.logger.error(f"Exception updating book ID {id}: {str(e)}")
            flash(f'Error updating book: {str(e)}', 'danger')
    
    return render_template('books/edit.html', form=form, book=book)

@main_bp.route('/books/<int:id>/delete', methods=['POST'])
@login_required
@librarian_required
def delete_book(id):
    book = Book.get_by_id(id)
    if not book:
        abort(404)
    
    if book.delete():
        flash('Book deleted successfully.', 'success')
    else:
        flash('Error deleting book. Please try again.', 'danger')
    
    return redirect(url_for('main.books'))

# Sections routes
@main_bp.route('/sections')
@login_required
@librarian_required
def sections():
    sections = Section.get_all()
    return render_template('sections/index.html', sections=sections)

@main_bp.route('/sections/create', methods=['GET', 'POST'])
@login_required
@librarian_required
def create_section():
    form = SectionForm()
    
    if form.validate_on_submit():
        # Check if section with this name already exists
        if Section.get_by_name(form.name.data):
            flash(f'Section "{form.name.data}" already exists.', 'danger')
            return render_template('sections/create.html', form=form)
        
        section = Section(
            name=form.name.data,
            description=form.description.data
        )
        
        if section.create():
            flash('Section created successfully.', 'success')
            return redirect(url_for('main.sections'))
        else:
            flash('Error creating section. Please try again.', 'danger')
    
    return render_template('sections/create.html', form=form)

@main_bp.route('/sections/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@librarian_required
def edit_section(id):
    section = Section.get_by_id(id)
    if not section:
        abort(404)
    
    form = SectionForm(original_name=section.name, obj=section)
    
    if form.validate_on_submit():
        # Check if name changed and if new name already exists
        if form.name.data != section.name and Section.get_by_name(form.name.data):
            flash(f'Section "{form.name.data}" already exists.', 'danger')
            return render_template('sections/edit.html', form=form, section=section)
        
        section.name = form.name.data
        section.description = form.description.data
        
        if section.update():
            flash('Section updated successfully.', 'success')
            return redirect(url_for('main.sections'))
        else:
            flash('Error updating section. Please try again.', 'danger')
    
    return render_template('sections/edit.html', form=form, section=section)

@main_bp.route('/sections/<int:id>/delete', methods=['POST'])
@login_required
@librarian_required
def delete_section(id):
    section = Section.get_by_id(id)
    if not section:
        abort(404)
    
    # Check if section has books
    if len(section.books) > 0:
        flash(f'Cannot delete section "{section.name}" because it contains books.', 'danger')
        return redirect(url_for('main.sections'))
    
    if section.delete():
        flash('Section deleted successfully.', 'success')
    else:
        flash('Error deleting section. Please try again.', 'danger')
    
    return redirect(url_for('main.sections'))

# Search route (AJAX)
@main_bp.route('/search')
@login_required
def search():
    query = request.args.get('query', '')
    section_id = request.args.get('section', type=int, default=0)
    
    if not query and not section_id:
        return jsonify([])
    
    # Use our search function to find books
    search_results = Book.search(
        query=query if query else None,
        section_id=section_id if section_id else None,
        per_page=10  # Limit to 10 results
    )
    
    # Format results
    results = [{
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'section': book._section_name,
        'available': book.available
    } for book in search_results['items']]
    
    return jsonify(results)