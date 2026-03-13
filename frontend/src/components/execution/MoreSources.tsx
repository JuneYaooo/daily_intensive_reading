import React from 'react';
import { Brief } from '../../types';
import { ArrowUpRight, Heart } from 'lucide-react';

interface MoreSourcesProps {
  allBriefs: Brief[];
  displayedBriefIds: string[];
  onSelectBrief: (briefId: string) => void;
}

const MoreSources: React.FC<MoreSourcesProps> = ({
  allBriefs,
  displayedBriefIds,
  onSelectBrief,
}) => {
  // 过滤出未显示的简报
  const moreBriefs = allBriefs
    .filter(brief => !displayedBriefIds.includes(brief.id))
    .sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
    .slice(0, 5); // 只显示最近的5个
  
  if (moreBriefs.length === 0) {
    return null;
  }
  
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {moreBriefs.map(brief => (
          <div
            key={brief.id}
            onClick={() => onSelectBrief(brief.id)}
            className="bg-white rounded-lg border border-gray-200 p-3 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex justify-between">
              <h4 className="font-medium text-sm line-clamp-1">{brief.sourceName}</h4>
              
              <div className="flex items-center space-x-1">
                {brief.isFavorite && (
                  <Heart className="w-3.5 h-3.5 text-[#FF3B30] fill-[#FF3B30]" />
                )}
                <ArrowUpRight className="w-3.5 h-3.5 text-gray-400" />
              </div>
            </div>
            
            <div className="text-xs text-gray-500 mt-1 line-clamp-1">
              {brief.sourceUrl ? (
                <div className="flex items-center">
                  <span className="truncate">{brief.sourceUrl}</span>
                </div>
              ) : (
                <span>创建于 {new Date(brief.createdAt).toLocaleString()}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MoreSources;