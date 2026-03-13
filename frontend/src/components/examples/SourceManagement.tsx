import React, { useEffect, useState } from 'react';
import { useSourceStore } from '../../store/stores';
import { Source } from '../../types';

const SourceManagement: React.FC = () => {
  const { sources, isLoading, error, fetchSources, createSource, updateSource, deleteSource } = useSourceStore();
  const [newSource, setNewSource] = useState<Source>({ name: '' });
  const [editingSource, setEditingSource] = useState<Source | null>(null);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    if (editingSource) {
      setEditingSource({ ...editingSource, [name]: value });
    } else {
      setNewSource({ ...newSource, [name]: value });
    }
  };

  const handleCreateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newSource.name.trim()) {
      await createSource(newSource);
      setNewSource({ name: '' });
    }
  };

  const handleUpdateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingSource && editingSource.id && editingSource.name.trim()) {
      await updateSource(editingSource.id, editingSource);
      setEditingSource(null);
    }
  };

  const handleDeleteSource = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this source?')) {
      await deleteSource(id);
    }
  };

  if (isLoading && sources.length === 0) {
    return <div>Loading sources...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Source Management</h2>
      
      {/* Create Source Form */}
      <div className="mb-6 p-4 bg-gray-50 rounded-md">
        <h3 className="text-lg font-semibold mb-2">Add New Source</h3>
        <form onSubmit={handleCreateSource}>
          <div className="flex flex-col space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name*</label>
              <input
                type="text"
                name="name"
                value={newSource.name}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">URL</label>
              <input
                type="text"
                name="url"
                value={newSource.url || ''}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                name="description"
                value={newSource.description || ''}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={3}
              />
            </div>
            <button
              type="submit"
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Add Source
            </button>
          </div>
        </form>
      </div>

      {/* Edit Source Form */}
      {editingSource && (
        <div className="mb-6 p-4 bg-yellow-50 rounded-md">
          <h3 className="text-lg font-semibold mb-2">Edit Source</h3>
          <form onSubmit={handleUpdateSource}>
            <div className="flex flex-col space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name*</label>
                <input
                  type="text"
                  name="name"
                  value={editingSource.name}
                  onChange={handleInputChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">URL</label>
                <input
                  type="text"
                  name="url"
                  value={editingSource.url || ''}
                  onChange={handleInputChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  name="description"
                  value={editingSource.description || ''}
                  onChange={handleInputChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                />
              </div>
              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                >
                  Update Source
                </button>
                <button
                  type="button"
                  onClick={() => setEditingSource(null)}
                  className="inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Sources List */}
      <div>
        <h3 className="text-lg font-semibold mb-2">Sources</h3>
        {sources.length === 0 ? (
          <p>No sources available.</p>
        ) : (
          <ul className="divide-y divide-gray-200">
            {sources.map((source) => (
              <li key={source.id} className="py-4">
                <div className="flex justify-between">
                  <div>
                    <h4 className="text-lg font-medium">{source.name}</h4>
                    {source.url && (
                      <p className="text-sm text-blue-600">
                        <a href={source.url} target="_blank" rel="noopener noreferrer">
                          {source.url}
                        </a>
                      </p>
                    )}
                    {source.description && <p className="mt-1 text-gray-500">{source.description}</p>}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setEditingSource(source)}
                      className="text-indigo-600 hover:text-indigo-900"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => source.id && handleDeleteSource(source.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default SourceManagement; 