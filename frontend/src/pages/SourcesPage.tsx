import React, { useEffect } from 'react';
import SourceList from '../components/sources/SourceList';
import { useAppStore } from '../store';

const SourcesPage: React.FC = () => {
  const { fetchSources, isLoadingSources } = useAppStore();
  
  useEffect(() => {
    // Fetch sources when the component mounts
    fetchSources();
  }, [fetchSources]);
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-[#FF6B6B]">信息源管理</h1>
      </div>
      
      <SourceList isLoading={isLoadingSources} />
    </div>
  );
};

export default SourcesPage;