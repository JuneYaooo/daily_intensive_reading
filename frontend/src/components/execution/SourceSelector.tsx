import React from 'react';
import { Check, Info } from 'lucide-react';
import { Source } from '../../types';
import { useAppStore } from '../../store';

interface SourceSelectorProps {
  sources: Source[];
  selectedSourceIds: number[];
  onToggleSource: (id: number) => void;
}

const SourceSelector: React.FC<SourceSelectorProps> = ({
  sources,
  selectedSourceIds,
  onToggleSource
}) => {
  if (sources.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <p className="text-gray-500 mb-2">No sources available</p>
        <p className="text-sm text-gray-400">Add sources in the Sources section</p>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h3 className="font-semibold text-[#1A365D]">Select Sources to Curate</h3>
          <div className="text-sm text-gray-500">
            {selectedSourceIds.length} of {sources.length} selected
          </div>
        </div>
      </div>
      
      <div className="divide-y divide-gray-100 max-h-[400px] overflow-y-auto">
        {sources.map((source) => (
          <SourceItem
            key={source.id}
            source={source}
            isSelected={source.id !== undefined && selectedSourceIds.includes(source.id)}
            onToggle={() => source.id !== undefined && onToggleSource(source.id)}
          />
        ))}
      </div>
    </div>
  );
};

interface SourceItemProps {
  source: Source;
  isSelected: boolean;
  onToggle: () => void;
}

const SourceItem: React.FC<SourceItemProps> = ({ source, isSelected, onToggle }) => {
  return (
    <div
      className={`p-3 transition-colors cursor-pointer ${
        isSelected ? 'bg-[#F0F9F8]' : 'hover:bg-gray-50'
      }`}
      onClick={onToggle}
    >
      <div className="flex items-start">
        <div className="flex-shrink-0 pt-0.5">
          <div
            className={`w-5 h-5 rounded-md border flex items-center justify-center ${
              isSelected ? 'bg-[#0D9488] border-[#0D9488]' : 'border-gray-300'
            }`}
          >
            {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
          </div>
        </div>
        
        <div className="ml-3 flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-800">{source.name}</div>
          <div className="text-xs text-gray-500 truncate">{source.url}</div>
        </div>
        
        {source.description && (
          <div className="ml-2 group relative flex-shrink-0">
            <Info className="w-4 h-4 text-gray-400" />
            <div className="absolute right-0 w-64 p-2 bg-white border border-gray-100 rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10 text-xs text-gray-600">
              {source.description}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SourceSelector;