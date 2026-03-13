import React, { useState } from 'react';
import { Plus, Loader } from 'lucide-react';
import { Source } from '../../types';
import SourceItem from './SourceItem';
import SourceForm from './SourceForm';
import { useAppStore } from '../../store';

interface SourceListProps {
  isLoading?: boolean;
}

const SourceList: React.FC<SourceListProps> = ({ isLoading = false }) => {
  const { sources, addSource, updateSource, deleteSource } = useAppStore();
  const [isFormVisible, setIsFormVisible] = useState(false);
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null);
  
  const handleAddSource = () => {
    setEditingSource(null);
    setIsFormVisible(true);
  };
  
  const handleEditSource = (source: Source) => {
    setEditingSource(source);
    setIsFormVisible(true);
  };
  
  const handleDeleteSource = (id: number) => {
    setShowDeleteConfirm(id);
  };
  
  const confirmDelete = (id: number) => {
    deleteSource(id);
    setShowDeleteConfirm(null);
  };
  
  const handleSubmit = (sourceData: Omit<Source, 'id'>) => {
    if (editingSource && editingSource.id !== undefined) {
      updateSource(editingSource.id, sourceData);
    } else {
      addSource(sourceData);
    }
    setIsFormVisible(false);
    setEditingSource(null);
  };
  
  const handleCancel = () => {
    setIsFormVisible(false);
    setEditingSource(null);
  };
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-[#1A365D]">Your Sources</h2>
        <button
          onClick={handleAddSource}
          className="flex items-center px-4 py-2 bg-[#0D9488] text-white rounded-md hover:bg-[#0B7A7A] transition-colors"
        >
          <Plus className="w-5 h-5 mr-1" />
          <span>Add Source</span>
        </button>
      </div>
      
      {isFormVisible && (
        <SourceForm
          source={editingSource || undefined}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
        />
      )}
      
      {isLoading ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <div className="flex flex-col items-center justify-center">
            <Loader className="w-8 h-8 text-[#0D9488] animate-spin mb-4" />
            <p className="text-gray-600">Loading sources...</p>
          </div>
        </div>
      ) : sources.length === 0 && !isFormVisible ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-500 mb-4">You haven't added any information sources yet.</p>
          <button
            onClick={handleAddSource}
            className="px-4 py-2 bg-[#0D9488] text-white rounded-md hover:bg-[#0B7A7A] transition-colors"
          >
            Add Your First Source
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sources.map((source) => (
            <div key={source.id} className="relative">
              <SourceItem
                source={source}
                onEdit={handleEditSource}
                onDelete={handleDeleteSource}
              />
              
              {source.id !== undefined && showDeleteConfirm === source.id && (
                <div className="absolute inset-0 bg-white bg-opacity-95 rounded-lg flex flex-col items-center justify-center p-4 z-10 border border-red-100 shadow-md">
                  <p className="text-center mb-4">Are you sure you want to delete "{source.name}"?</p>
                  <div className="flex space-x-3">
                    <button
                      onClick={() => setShowDeleteConfirm(null)}
                      className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => source.id !== undefined && confirmDelete(source.id)}
                      className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SourceList;