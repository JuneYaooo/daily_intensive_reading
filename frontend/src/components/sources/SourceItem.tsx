import React from 'react';
import { Edit, Trash2, Globe } from 'lucide-react';
import { Source } from '../../types';

interface SourceItemProps {
  source: Source;
  onEdit: (source: Source) => void;
  onDelete: (id: number) => void;
}

const SourceItem: React.FC<SourceItemProps> = ({ source, onEdit, onDelete }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 transition-all duration-300 hover:shadow-lg border border-gray-100">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="text-lg font-medium text-[#1A365D]">{source.name}</h3>
          <div className="flex items-center text-gray-500 text-sm mt-1">
            <Globe className="w-4 h-4 mr-1" />
            <a 
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#0D9488] hover:underline truncate max-w-xs"
            >
              {source.url}
            </a>
          </div>
          {source.description && (
            <p className="text-gray-600 mt-2 text-sm">{source.description}</p>
          )}
        </div>
        
        <div className="flex space-x-2 ml-4">
          <button 
            onClick={() => onEdit(source)}
            className="p-1.5 text-gray-500 hover:text-[#0D9488] rounded-full hover:bg-gray-100 transition-colors"
            aria-label="Edit source"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button 
            onClick={() => source.id !== undefined && onDelete(source.id)}
            className="p-1.5 text-gray-500 hover:text-red-500 rounded-full hover:bg-gray-100 transition-colors"
            aria-label="Delete source"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SourceItem;