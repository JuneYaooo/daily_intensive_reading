import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { Source } from '../../types';

interface SourceFormProps {
  source?: Source;
  onSubmit: (source: Omit<Source, 'id'>) => void;
  onCancel: () => void;
}

const SourceForm: React.FC<SourceFormProps> = ({ source, onSubmit, onCancel }) => {
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (source) {
      setName(source.name);
      setUrl(source.url);
      setDescription(source.description);
    }
  }, [source]);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    
    if (!url.trim()) {
      setError('URL is required');
      return;
    }
    
    // Basic URL validation
    try {
      new URL(url);
    } catch (_) {
      setError('Please enter a valid URL');
      return;
    }
    
    onSubmit({ name, url, description });
    resetForm();
  };
  
  const resetForm = () => {
    setName('');
    setUrl('');
    setDescription('');
    setError(null);
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6 animate-fadeIn">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-[#1A365D]">
          {source ? 'Edit Source' : 'Add New Source'}
        </h2>
        <button
          onClick={onCancel}
          className="p-1 rounded-full hover:bg-gray-100 transition-colors"
          aria-label="Close form"
        >
          <X className="w-5 h-5 text-gray-500" />
        </button>
      </div>
      
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded-md text-sm">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Name <span className="text-red-500">*</span>
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0D9488] transition-all"
            placeholder="Enter source name"
            required
          />
        </div>
        
        <div className="mb-4">
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">
            URL <span className="text-red-500">*</span>
          </label>
          <input
            id="url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0D9488] transition-all"
            placeholder="https://example.com"
            required
          />
        </div>
        
        <div className="mb-6">
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description <span className="text-gray-400">(optional)</span>
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0D9488] transition-all"
            placeholder="Enter a brief description"
            rows={3}
          />
        </div>
        
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-[#0D9488] text-white rounded-md hover:bg-[#0B7A7A] transition-colors"
          >
            {source ? 'Update Source' : 'Add Source'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SourceForm;