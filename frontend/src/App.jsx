import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './components/Sidebar';
import BookList from './components/BookList';
import BookForm from './components/BookForm';
import Modal from './components/Modal';
import { BookOpenIcon } from '@heroicons/react/24/outline';

function App() {

  const initialBooks = [
    {
      id: '1',
      title: 'The Great Gatsby',
      author: 'F. Scott Fitzgerald',
      genre: 'Fiction',
      available: true
    },
    {
      id: '2',
      title: 'Dune',
      author: 'Frank Herbert',
      genre: 'Science Fiction',
      available: true
    },
    {
      id: '3',
      title: 'Murder on the Orient Express',
      author: 'Agatha Christie',
      genre: 'Mystery',
      available: false
    }
  ];

  const [books, setBooks] = useState(initialBooks);
  const [currentView, setCurrentView] = useState('books');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [editingBook, setEditingBook] = useState(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [bookToDelete, setBookToDelete] = useState(null);

  

  const handleAddBook = (bookData) => {
    const newBook = {
      ...bookData,
      id: Date.now().toString(),
    };
    setBooks([...books, newBook]);
    setCurrentView('books');
  };

  const handleEditBook = (bookData) => {
    setBooks(books.map((book) => 
      book.id === editingBook.id ? { ...book, ...bookData } : book
    ));
    setEditingBook(null);
  };

  const handleDeleteBook = (id) => {
    setBookToDelete(id);
    setIsDeleteModalOpen(true);
  };

  const confirmDelete = () => {
    setBooks(books.filter((book) => book.id !== bookToDelete));
    setIsDeleteModalOpen(false);
    setBookToDelete(null);
  };

  const handleToggleAvailability = (id) => {
    setBooks(books.map((book) =>
      book.id === id ? { ...book, available: !book.available } : book
    ));
  };

  const filteredBooks = books.filter((book) => {
    const matchesSearch = book.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesGenre = !selectedGenre || book.genre === selectedGenre;
    return matchesSearch && matchesGenre;  // Add this return statement
  });

  const genres = ['Fiction', 'Non-Fiction', 'Science Fiction', 'Mystery', 'Romance'];

  return (
    
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm fixed w-full z-10">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 lg:ml-64">
      <div className="flex items-center">
        <BookOpenIcon className="h-8 w-8 text-primary-500" />
        <h1 className="ml-3 text-2xl font-bold text-gray-900">Library Management System</h1>
      </div>
    </div>
  </header>
      <Sidebar onNavigate={setCurrentView} />

      <main className="lg:ml-64 p-8 pt-24"> 
        <AnimatePresence mode="wait">
          {currentView === 'books' ? (
            <motion.div
              key="books"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="mb-8 flex flex-col md:flex-row md:items-center md:space-x-4">
                <input
                  type="text"
                  placeholder="Search books..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="mb-4 md:mb-0 p-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-300"
                />
                <select
                  value={selectedGenre}
                  onChange={(e) => setSelectedGenre(e.target.value)}
                  className="p-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-300"
                >
                  <option value="">All Genres</option>
                  {genres.map((genre) => (
                    <option key={genre} value={genre}>
                      {genre}
                    </option>
                  ))}
                </select>
              </div>

              <BookList
                books={filteredBooks}
                onEdit={setEditingBook}
                onDelete={handleDeleteBook}
                onToggleAvailability={handleToggleAvailability}
              />
            </motion.div>
          ) : (
            <motion.div
              key="add"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <BookForm onSubmit={handleAddBook} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <Modal isOpen={!!editingBook} onClose={() => setEditingBook(null)}>
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">Edit Book</h2>
          <BookForm
            book={editingBook}
            onSubmit={handleEditBook}
            onCancel={() => setEditingBook(null)}
          />
        </div>
      </Modal>

      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)}>
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">Confirm Delete</h2>
          <p className="mb-4">Are you sure you want to delete this book?</p>
          <div className="flex justify-end space-x-4">
            <button
              onClick={() => setIsDeleteModalOpen(false)}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={confirmDelete}
              className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
            >
              Delete
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

export default App;