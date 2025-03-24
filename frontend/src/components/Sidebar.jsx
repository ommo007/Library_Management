import { useState } from 'react';
import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import { XMarkIcon, Bars3Icon, BookOpenIcon, PlusIcon } from '@heroicons/react/24/outline';

function Sidebar({ onNavigate }) {
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    { id: 'books', label: 'View Books', icon: BookOpenIcon },
    { id: 'add', label: 'Add Book', icon: PlusIcon },
  ];

  return (
    <>
    {/* Overlay for mobile */}
    {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-20"
          onClick={() => setIsOpen(false)}
        />
      )}
      <button
  onClick={() => setIsOpen(!isOpen)}
  className="lg:hidden fixed top-4 left-4 z-40 p-2 bg-white rounded-lg shadow-md"
>
        {isOpen ? (
          <XMarkIcon className="w-6 h-6" />
        ) : (
          <Bars3Icon className="w-6 h-6" />
        )}
      </button>

      <motion.div
  initial={{ x: -300 }}
  animate={{ x: isOpen ? 0 : -300 }}
  className="fixed top-0 left-0 h-full w-64 bg-white shadow-lg lg:translate-x-0 z-30"
>
        <div className="p-6">
          <h2 className="text-2xl font-bold text-primary-500 mb-8">Library MS</h2>
          <nav>
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  onNavigate(item.id);
                  setIsOpen(false);
                }}
                className="w-full flex items-center space-x-2 p-3 rounded-lg hover:bg-primary-50 text-gray-700 mb-2"
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </motion.div>
    </>
  );
}

Sidebar.propTypes = {
  onNavigate: PropTypes.func.isRequired,
};

export default Sidebar;