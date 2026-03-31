import React, { useEffect, useState } from 'react';
import { Play, Loader } from 'lucide-react';
import { useAppStore } from '../store';
import SourceSelector from '../components/execution/SourceSelector';
import PromptEditor from '../components/execution/PromptEditor';
import BriefCard from '../components/execution/BriefCard';
import MoreSources from '../components/execution/MoreSources';

const CurationPage: React.FC = () => {
  const {
    sources,
    selectedSourceIds,
    toggleSourceSelection,
    settings,
    customFilterPrompt,
    customSummaryPrompt,
    setCustomFilterPrompt,
    setCustomSummaryPrompt,
    resetCustomPrompts,
    generateBriefs,
    currentBriefs,
    briefs,
    isGenerating,
    generatingStatus,
    selectBrief,
    fetchSources
  } = useAppStore();
  
  useEffect(() => {
    // Fetch sources when the component mounts
    fetchSources();
    
    // 调试日志：显示当前的设置
    console.log('当前设置:', settings);
    console.log('当前自定义过滤提示:', customFilterPrompt);
    console.log('当前自定义总结提示:', customSummaryPrompt);
  }, [fetchSources, settings]);
  
  const handleResetFilterPrompt = () => {
    console.log('重置过滤提示');
    resetCustomPrompts(); // 重置所有自定义提示
  };
  
  const handleResetSummaryPrompt = () => {
    console.log('重置总结提示');
    resetCustomPrompts(); // 重置所有自定义提示
  };
  
  const handleExecute = () => {
    console.log('执行生成，当前提示:', {
      filterPrompt: customFilterPrompt || settings.filterPrompt,
      summaryPrompt: customSummaryPrompt || settings.summaryPrompt
    });
    
    // Clear existing briefs before generating new ones
    useAppStore.setState({ currentBriefs: [] });
    
    // Start generation process
    generateBriefs();
  };
  
  const displayedBriefIds = currentBriefs.map(brief => brief.id);
  
  // 将当前简报分为两组：生成的卡片和URL-only
  const generatedBriefs = currentBriefs.filter(brief => brief.sourceId === 'generated');
  const urlOnlyBriefs = currentBriefs.filter(brief => brief.sourceId === 'url-only');
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-[#1C1C1E]">每日精读</h1>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <SourceSelector
            sources={sources}
            selectedSourceIds={selectedSourceIds}
            onToggleSource={toggleSourceSelection}
          />
          
          <PromptEditor
            type="filter"
            defaultValue={settings.filterPrompt || ''}
            onChange={setCustomFilterPrompt}
            onReset={handleResetFilterPrompt}
          />
          
          <PromptEditor
            type="summary"
            defaultValue={settings.summaryPrompt || ''}
            onChange={setCustomSummaryPrompt}
            onReset={handleResetSummaryPrompt}
          />
          
          <div className="flex justify-center">
            <button
              onClick={handleExecute}
              disabled={selectedSourceIds.length === 0 || isGenerating}
              className={`w-full py-3 rounded-md transition-colors flex items-center justify-center ${
                selectedSourceIds.length === 0 || isGenerating
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-[#0A84FF] text-white hover:bg-[#0070E0]'
              }`}
            >
              {isGenerating ? (
                <>
                  <Loader className="w-5 h-5 mr-2 animate-spin" />
                  <span>正在生成简报...</span>
                </>
              ) : (
                <>
                  <Play className="w-5 h-5 mr-2" />
                  <span>生成简报</span>
                </>
              )}
            </button>
          </div>
        </div>
        
        <div className="lg:col-span-2 space-y-6">
          {isGenerating ? (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <div className="flex flex-col items-center justify-center">
                <Loader className="w-8 h-8 text-[#0A84FF] animate-spin mb-4" />
                <p className="text-gray-600">正在分析源内容并生成简报...</p>
                <p className="text-sm text-[#0A84FF] mt-2 font-medium">{generatingStatus}</p>
                <p className="text-xs text-gray-400 mt-1">这可能需要几分钟，请耐心等待</p>
              </div>
            </div>
          ) : currentBriefs.length > 0 ? (
            <div className="space-y-6">
              {/* 已生成摘要的卡片 */}
              {generatedBriefs.length > 0 && (
                <div className="grid grid-cols-1 gap-4">
                  <h2 className="text-lg font-semibold text-[#1C1C1E]">已生成摘要</h2>
                  {generatedBriefs.map((brief) => (
                    <BriefCard key={brief.id} brief={brief} />
                  ))}
                </div>
              )}
              
              {/* 分隔线 - 只有当两种类型都有内容时才显示 */}
              {generatedBriefs.length > 0 && urlOnlyBriefs.length > 0 && (
                <div className="relative py-3">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300"></div>
                  </div>
                </div>
              )}
              
              {/* URL-only卡片区域 */}
              {urlOnlyBriefs.length > 0 && (
                <div className="grid grid-cols-1 gap-4">
                  <h2 className="text-lg font-semibold text-[#1C1C1E] flex items-center">
                    <span>更多推荐</span>
                  </h2>
                  {urlOnlyBriefs.map((brief) => (
                    <BriefCard key={brief.id} brief={brief} />
                  ))}
                </div>
              )}
              
              {/* 更多历史简报 */}
              {briefs.length > currentBriefs.length && (
                <div className="mt-8">
                  <div className="relative py-3">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-200"></div>
                    </div>
                    <div className="relative flex justify-center">
                      <span className="bg-gray-100 px-4 text-sm text-gray-500 rounded-full">历史简报</span>
                    </div>
                  </div>
                  
                  <MoreSources
                    allBriefs={briefs}
                    displayedBriefIds={displayedBriefIds}
                    onSelectBrief={selectBrief}
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <p className="text-gray-500 mb-2">暂无生成的简报</p>
              <p className="text-sm text-gray-400">
                选择信息源并点击"生成简报"开始使用
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CurationPage;