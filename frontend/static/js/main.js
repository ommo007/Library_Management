document.addEventListener('DOMContentLoaded', function() {
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
                return;
            }
            
            // Build URL with parameters
            const url = `/search?query=${encodeURIComponent(query)}&section=${sectionId}`;
            
            // Fetch search results
            fetch(url)
                .then(response => response.json())
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
                    resultsContainer.innerHTML = '<div class="p-3">Error fetching results</div>';
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
                e.preventDefault();
                performSearch();
            });
        }
    }
    
    // Book availability toggle (for librarians)
    const availabilityToggles = document.querySelectorAll('.availability-toggle');
    
    availabilityToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const bookId = this.dataset.bookId;
            const available = this.checked;
            
            fetch(`/books/${bookId}/toggle-availability`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({ available })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update UI
                    const statusElement = document.querySelector(`#book-${bookId}-status`);
                    if (statusElement) {
                        statusElement.className = available ? 'badge bg-success' : 'badge bg-danger';
                        statusElement.textContent = available ? 'Available' : 'Unavailable';
                    }
                }
            })
            .catch(error => {
                console.error('Error updating book availability:', error);
                // Revert the toggle
                this.checked = !available;
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
        });
    });
});
