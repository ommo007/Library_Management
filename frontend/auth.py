from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from db import User, Role
from forms import LoginForm, RegistrationForm, LibrarianCreationForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if user is already authenticated
    if current_user.is_authenticated:
        # If admin, redirect to admin dashboard
        if current_user.is_admin():
            return redirect(url_for('auth.admin_dashboard'))
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Find the user by username
        user = User.get_by_username(form.username.data)
        
        # Check if user exists and password is correct
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login', admin='1' if request.args.get('admin') == '1' else None))
        
        # Log the user in
        login_user(user, remember=form.remember_me.data)
        
        # If this is an admin login and user is admin, redirect to admin dashboard
        if request.args.get('admin') == '1' and user.is_admin():
            flash(f'Welcome, Admin {user.username}!', 'success')
            return redirect(url_for('auth.admin_dashboard'))
        
        # If user is admin but not from admin login, also go to dashboard
        if user.is_admin():
            flash(f'Welcome, Admin {user.username}!', 'success')
            return redirect(url_for('auth.admin_dashboard'))
        
        # For regular users, proceed with normal flow
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.books')
            
        flash(f'Welcome, {user.username}!', 'success')
        return redirect(next_page)
    
    # Check if this is an admin login attempt
    is_admin_login = request.args.get('admin') == '1'
    
    return render_template('auth/login.html', form=form, is_admin_login=is_admin_login)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect if user is already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    
    # Set choices for the role field - only Student role allowed for registration
    student_role = Role.get_by_name('Student')
    if student_role:
        form.role.choices = [(str(student_role.id), student_role.name)]
    
    if form.validate_on_submit():
        # Check if username already exists
        if User.get_by_username(form.username.data):
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if email already exists
        if User.get_by_email(form.email.data):
            flash('Email already registered. Please use a different email.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            role_id=int(form.role.data)
        )
        user.set_password(form.password.data)
        
        # Save user to database
        if user.create():
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/admin')
@login_required
def admin_dashboard():
    # Check if the user is an admin
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('auth/admin_dashboard.html')

@auth_bp.route('/admin/create-librarian', methods=['GET', 'POST'])
@login_required
def create_librarian():
    # Check if the user is an admin
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    form = LibrarianCreationForm()
    
    # Set choices for the role field - only Librarian role allowed
    librarian_role = Role.get_by_name('Librarian')
    if librarian_role:
        form.role.choices = [(str(librarian_role.id), librarian_role.name)]
        form.role.data = str(librarian_role.id)  # Pre-select the Librarian role
    
    if form.validate_on_submit():
        # Check if username already exists
        if User.get_by_username(form.username.data):
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.create_librarian'))
        
        # Check if email already exists
        if User.get_by_email(form.email.data):
            flash('Email already registered. Please use a different email.', 'danger')
            return redirect(url_for('auth.create_librarian'))
        
        # Create new librarian user
        librarian = User(
            username=form.username.data,
            email=form.email.data,
            role_id=int(form.role.data)
        )
        librarian.set_password(form.password.data)
        
        # Save user to database
        if librarian.create():
            flash(f'Librarian account for {librarian.username} created successfully!', 'success')
            return redirect(url_for('auth.admin_dashboard'))
        else:
            flash('An error occurred while creating the librarian account.', 'danger')
    
    return render_template('auth/create_librarian.html', form=form)