import { motion } from 'framer-motion';
import PropTypes from 'prop-types';
import { PencilIcon, TrashIcon } from '@heroicons/react/24/outline';

function BookList({ books, onEdit, onDelete, onToggleAvailability }) {
  if (books.length === 0) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">No books found</h3>
        <p className="mt-2 text-sm text-gray-500">
          Try adjusting your search or filter criteria
        </p>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {books.map((book) => (
        <motion.div
          key={book.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white p-6 rounded-lg shadow-md"
        >
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-semibold text-gray-800">{book.title}</h3>
            <div className="flex space-x-2">
              <button
                onClick={() => onEdit(book)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <PencilIcon className="w-5 h-5 text-gray-600" />
              </button>
              <button
                onClick={() => onDelete(book.id)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <TrashIcon className="w-5 h-5 text-red-500" />
              </button>
            </div>
          </div>
          <p className="text-gray-600 mb-2">By {book.author}</p>
          <p className="text-sm text-gray-500 mb-4">Genre: {book.genre}</p>
          <button
            onClick={() => onToggleAvailability(book.id)}
            className={`w-full py-2 px-4 rounded ${
              book.available
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {book.available ? 'Available' : 'Borrowed'}
          </button>
        </motion.div>
      ))}
    </div>
  );
}

BookList.propTypes = {
  books: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      author: PropTypes.string.isRequired,
      genre: PropTypes.string.isRequired,
      available: PropTypes.bool.isRequired,
    })
  ).isRequired,
  onEdit: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onToggleAvailability: PropTypes.func.isRequired,
};

export default BookList;