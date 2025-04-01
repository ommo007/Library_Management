document.addEventListener('DOMContentLoaded', function() {
    // Check if we're running on a server or as static files
    const isStaticFile = window.location.protocol === 'file:';
    
    // Define API base URL (change this to your actual backend URL when deploying)
    const apiBaseUrl = isStaticFile ? '' : 'http://localhost:5000';
    
    // Set up CSRF token for all AJAX requests
    const setupCSRF = () => {
        if (!isStaticFile) {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            if (csrfToken) {
                // Set up CSRF for all fetch requests
                const originalFetch = window.fetch;
                window.fetch = function(url, options = {}) {
                    const isFullUrl = url.startsWith('http');
                    const fetchUrl = isFullUrl ? url : `${apiBaseUrl}${url}`;
                    
                    // Only add CSRF token to same-origin POST/PUT/DELETE requests
                    if (!isFullUrl && options.method && options.method !== 'GET') {
                        if (!options.headers) {
                            options.headers = {};
                        }
                        if (options.headers instanceof Headers) {
                            options.headers.append('X-CSRFToken', csrfToken);
                        } else {
                            options.headers['X-CSRFToken'] = csrfToken;
                        }
                    }
                    
                    // Add credentials for cross-origin requests
                    if (!options.credentials) {
                        options.credentials = 'include';
                    }
                    
                    return originalFetch.call(this, fetchUrl, options);
                };
            }
        }
    };
    
    setupCSRF();
    
    // Authentication check - fetch user data and update UI accordingly
    function checkAuthentication() {
        if (isStaticFile) {
            // In static mode, check localStorage
            const authData = localStorage.getItem('authData');
            if (authData) {
                const userData = JSON.parse(authData);
                updateAuthUI(userData);
                return userData;
            }
            return null;
        } else {
            // With backend, fetch from API
            return fetch('/api/user')
                .then(response => response.json())
                .then(userData => {
                    updateAuthUI(userData);
                    return userData;
                })
                .catch(error => {
                    console.error('Error checking authentication:', error);
                    return { authenticated: false };
                });
        }
    }
    
    // Update UI based on authentication status
    function updateAuthUI(userData) {
        const authNav = document.querySelector('.navbar-nav:last-child');
        if (!authNav) return;
        
        if (userData && userData.authenticated) {
            // User is logged in, update navigation
            let roleClass = 'badge-student';
            let roleName = 'Student';
            
            if (userData.is_admin) {
                roleClass = 'bg-danger';
                roleName = 'Admin';
            } else if (userData.is_librarian) {
                roleClass = 'badge-librarian';
                roleName = 'Librarian';
            }
            
            authNav.innerHTML = `
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" 
                      data-bs-toggle="dropdown" aria-expanded="false">
                        <i class="fas fa-user-circle me-1"></i>${userData.username}
                        <span class="badge ${roleClass}">${roleName}</span>
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="navbarDropdown">
                        ${userData.is_admin ? `<li><a class="dropdown-item" href="${isStaticFile ? './admin_dashboard.html' : '/auth/admin'}">
                            <i class="fas fa-tachometer-alt me-1"></i>Admin Dashboard
                        </a></li>
                        <li><hr class="dropdown-divider"></li>` : ''}
                        <li><a class="dropdown-item" href="#" id="logout-btn">Logout</a></li>
                    </ul>
                </li>
            `;
            
            // Set up logout button
            const logoutBtn = document.getElementById('logout-btn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    if (isStaticFile) {
                        localStorage.removeItem('authData');
                        window.location.href = './index.html';
                    } else {
                        window.location.href = '/auth/logout';
                    }
                });
            }
            
            // Show librarian-only elements if applicable
            if (userData.is_librarian || userData.is_admin) {
                document.querySelectorAll('.librarian-only').forEach(el => {
                    el.classList.remove('d-none');
                });
                
                // Update "Add Book" link to point to the correct URL
                const addBookBtn = document.querySelector('a.btn-success[href="./create_book.html"]');
                if (addBookBtn && !isStaticFile) {
                    addBookBtn.href = '/books/create';
                }
            }
        }
    }
    
    // Run auth check when page loads
    checkAuthentication();
    
    // Live search functionality
    const searchInput = document.getElementById('search-input');
    const sectionFilter = document.getElementById('section-filter');
    const resultsContainer = document.getElementById('search-results');
    const searchForm = document.getElementById('search-form');
    
    if (searchInput && resultsContainer) {
        let debounceTimer;
        
        // Function to perform search
        const performSearch = () => {
            const query = searchInput.value.trim();
            const sectionId = sectionFilter ? sectionFilter.value : '';
            
            if (query.length < 2 && !sectionId) {
                resultsContainer.innerHTML = '';
                resultsContainer.classList.add('d-none');
                return;
            }
            
            // Build URL with parameters
            const url = `${apiBaseUrl}/search?query=${encodeURIComponent(query)}&section=${sectionId}`;
            
            if (isStaticFile) {
                // If static file, show sample results
                resultsContainer.classList.remove('d-none');
                resultsContainer.innerHTML = `
                    <div class="p-2 border-bottom search-result-item">
                        <a href="#" class="text-decoration-none">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="mb-0">The Great Gatsby</h6>
                                    <p class="small text-muted mb-0">by F. Scott Fitzgerald</p>
                                    <p class="small text-muted mb-0">Section: Classics</p>
                                </div>
                                <div><span class="badge bg-success">Available</span></div>
                            </div>
                        </a>
                    </div>
                    <div class="p-2 border-bottom search-result-item">
                        <a href="#" class="text-decoration-none">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="mb-0">To Kill a Mockingbird</h6>
                                    <p class="small text-muted mb-0">by Harper Lee</p>
                                    <p class="small text-muted mb-0">Section: Classics</p>
                                </div>
                                <div><span class="badge bg-success">Available</span></div>
                            </div>
                        </a>
                    </div>
                `;
                return;
            }
            
            // Show loading indicator
            resultsContainer.innerHTML = '<div class="p-3 text-center"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> Searching...</div>';
            resultsContainer.classList.remove('d-none');
            
            // Fetch search results
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Clear previous results
                    resultsContainer.innerHTML = '';
                    
                    if (data.length === 0) {
                        resultsContainer.innerHTML = '<div class="p-3">No results found</div>';
                        return;
                    }
                    
                    // Display results
                    data.forEach(book => {
                        const availabilityBadge = book.available ? 
                            '<span class="badge bg-success">Available</span>' : 
                            '<span class="badge bg-danger">Unavailable</span>';
                            
                        const resultItem = document.createElement('div');
                        resultItem.className = 'p-2 border-bottom search-result-item';
                        resultItem.innerHTML = `
                            <a href="/books/${book.id}" class="text-decoration-none">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6 class="mb-0">${book.title}</h6>
                                        <p class="small text-muted mb-0">by ${book.author}</p>
                                        <p class="small text-muted mb-0">Section: ${book.section}</p>
                                    </div>
                                    <div>${availabilityBadge}</div>
                                </div>
                            </a>
                        `;
                        
                        resultsContainer.appendChild(resultItem);
                    });
                })
                .catch(error => {
                    console.error('Error fetching search results:', error);
                    resultsContainer.innerHTML = '<div class="p-3">Error fetching results. Please try again.</div>';
                });
        };
        
        // Debounce search input
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(performSearch, 300);
        });
        
        // Handle section filter change
        if (sectionFilter) {
            sectionFilter.addEventListener('change', performSearch);
        }
        
        // Handle form submission
        if (searchForm) {
            searchForm.addEventListener('submit', function(e) {
                if (isStaticFile) {
                    e.preventDefault();
                    performSearch();
                }
            });
        }
        
        // Close search results when clicking outside
        document.addEventListener('click', function(e) {
            if (!resultsContainer.contains(e.target) && e.target !== searchInput) {
                resultsContainer.classList.add('d-none');
            }
        });
    }
    
    // Book availability toggle (for librarians)
    const availabilityToggles = document.querySelectorAll('.availability-toggle');
    
    availabilityToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const bookId = this.dataset.bookId;
            const available = this.checked;
            
            if (isStaticFile) {
                // Update UI for demo
                const statusElement = document.querySelector(`#book-${bookId}-status`);
                if (statusElement) {
                    statusElement.className = available ? 'badge bg-success' : 'badge bg-danger';
                    statusElement.textContent = available ? 'Available' : 'Unavailable';
                }
                return;
            }
            
            // Show loading indicator
            const statusElement = document.querySelector(`#book-${bookId}-status`);
            if (statusElement) {
                statusElement.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
            }
            
            fetch(`/books/${bookId}/toggle-availability`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ available })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Update UI
                    if (statusElement) {
                        statusElement.className = available ? 'badge bg-success' : 'badge bg-danger';
                        statusElement.textContent = available ? 'Available' : 'Unavailable';
                    }
                    
                    // Show toast notification
                    showToast(`Book ${available ? 'marked as available' : 'marked as unavailable'}`);
                } else {
                    throw new Error('Update failed');
                }
            })
            .catch(error => {
                console.error('Error updating book availability:', error);
                // Revert the toggle
                this.checked = !available;
                if (statusElement) {
                    statusElement.className = !available ? 'badge bg-success' : 'badge bg-danger';
                    statusElement.textContent = !available ? 'Available' : 'Unavailable';
                }
                showToast('Failed to update book status', 'danger');
            });
        });
    });
    
    // Delete confirmation
    const deleteButtons = document.querySelectorAll('.btn-delete');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
            
            if (isStaticFile) {
                e.preventDefault();
                // For demo, just hide the parent card
                const bookCard = this.closest('.book-card') || this.closest('.col');
                if (bookCard) {
                    bookCard.style.opacity = '0.5';
                    setTimeout(() => {
                        bookCard.remove();
                    }, 500);
                }
                showToast('Book deleted successfully');
            }
        });
    });
    
    // Toast notification function
    function showToast(message, type = 'success') {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        
        // Initialize and show the toast
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        
        // Remove toast after it's hidden
        toastEl.addEventListener('hidden.bs.toast', function() {
            toastEl.remove();
        });
    }
    
    // Initialize any user-specific UI elements based on authentication status
    function initUserInterface() {
        if (isStaticFile) {
            // For demo purposes, we can add a login/logout toggle button
            const loginButtons = document.querySelectorAll('.nav-link[href="./login.html"]');
            const registerButtons = document.querySelectorAll('.nav-link[href="./register.html"]');
            
            loginButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    if (e.ctrlKey || e.metaKey) return; // Allow opening in new tab
                    
                    e.preventDefault();
                    const isLoggedIn = document.querySelector('.dropdown-toggle');
                    
                    if (!isLoggedIn) {
                        // Simulate login by replacing login/register with user dropdown
                        const navbarNav = document.querySelector('.navbar-nav:last-child');
                        if (navbarNav) {
                            navbarNav.innerHTML = `
                                <li class="nav-item dropdown">
                                    <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" 
                                       data-bs-toggle="dropdown" aria-expanded="false">
                                        <i class="fas fa-user-circle me-1"></i>Demo User
                                        <span class="badge badge-student">Student</span>
                                    </a>
                                    <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="navbarDropdown">
                                        <li><a class="dropdown-item" href="./index.html">Logout</a></li>
                                    </ul>
                                </li>
                            `;
                            
                            // Reload the page to show "logged in" state
                            window.location.href = './index.html';
                        }
                    }
                });
            });
        }
    }
    
    initUserInterface();
});
