import React, { useState, useEffect } from 'react';
import { Save, RefreshCw } from 'lucide-react';
import { useAppStore } from '../../store';
import { promptService } from '../../services';
import { Prompt } from '../../types';

const PromptSettings: React.FC = () => {
  const { settings, updateSettings } = useAppStore();
  const [filterPrompt, setFilterPrompt] = useState(settings.filterPrompt);
  const [summaryPrompt, setSummaryPrompt] = useState(settings.summaryPrompt);
  const [isSaved, setIsSaved] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 加载现有的提示词
  useEffect(() => {
    const loadPrompts = async () => {
      try {
        // 尝试获取默认筛选提示词
        const filterPrompt = await promptService.getDefaultPromptByType('filter').catch(() => null);
        if (filterPrompt) {
          setFilterPrompt(filterPrompt.content);
        }
        
        // 尝试获取默认总结提示词
        const summaryPrompt = await promptService.getDefaultPromptByType('summary').catch(() => null);
        if (summaryPrompt) {
          setSummaryPrompt(summaryPrompt.content);
        }
      } catch (err) {
        console.error("加载提示词失败:", err);
      }
    };
    
    loadPrompts();
  }, []);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      // 1. 更新本地状态
      updateSettings({
        filterPrompt,
        summaryPrompt
      });
      
      // 2. 保存到后端
      
      // 先尝试获取现有的提示词
      const existingFilterPrompt = await promptService.getDefaultPromptByType('filter').catch(() => null);
      const existingSummaryPrompt = await promptService.getDefaultPromptByType('summary').catch(() => null);
      
      // 保存筛选提示词
      if (existingFilterPrompt && typeof existingFilterPrompt.id === 'number') {
        // 如果存在则更新
        await promptService.updatePrompt(existingFilterPrompt.id, {
          ...existingFilterPrompt,
          content: filterPrompt
        });
      } else {
        // 如果不存在则创建
        await promptService.createPrompt({
          name: "默认筛选提示词",
          content: filterPrompt,
          description: "用于从信息源筛选内容的默认提示词",
          type: "filter",
          is_default: true
        });
      }
      
      // 保存总结提示词
      if (existingSummaryPrompt && typeof existingSummaryPrompt.id === 'number') {
        // 如果存在则更新
        await promptService.updatePrompt(existingSummaryPrompt.id, {
          ...existingSummaryPrompt,
          content: summaryPrompt
        });
      } else {
        // 如果不存在则创建
        await promptService.createPrompt({
          name: "默认总结提示词",
          content: summaryPrompt,
          description: "用于总结内容的默认提示词",
          type: "summary",
          is_default: true
        });
      }
      
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    } catch (err) {
      console.error("保存提示词失败:", err);
      setError("保存失败，请重试");
    } finally {
      setIsLoading(false);
    }
  };
  
  const resetToDefaults = () => {
    // Empty default prompts - users will fill in their own
    setFilterPrompt("");
    setSummaryPrompt("");
  };
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-[#1C1C1E]">提示词预设</h2>
        <button
          onClick={resetToDefaults}
          className="flex items-center px-4 py-2 border border-[#0A84FF] text-[#0A84FF] rounded-md hover:bg-[#0A84FF] hover:text-white transition-colors"
        >
          <RefreshCw className="w-5 h-5 mr-1" />
          <span>清空内容</span>
        </button>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label htmlFor="filterPrompt" className="block text-sm font-medium text-gray-700 mb-1">
              筛选提示词
            </label>
            <p className="text-gray-500 text-sm mb-2">
              此提示词将用于从信息源中筛选内容。
            </p>
            <textarea
              id="filterPrompt"
              value={filterPrompt}
              onChange={(e) => setFilterPrompt(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0A84FF] transition-all"
              rows={4}
              placeholder="输入筛选提示词"
            />
          </div>
          
          <div className="mb-6">
            <label htmlFor="summaryPrompt" className="block text-sm font-medium text-gray-700 mb-1">
              总结提示词
            </label>
            <p className="text-gray-500 text-sm mb-2">
              此提示词将用于总结筛选后的内容。
            </p>
            <textarea
              id="summaryPrompt"
              value={summaryPrompt}
              onChange={(e) => setSummaryPrompt(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0A84FF] transition-all"
              rows={4}
              placeholder="输入总结提示词"
            />
          </div>
          
          <div className="flex justify-end items-center">
            {error && (
              <span className="text-red-500 mr-4">
                {error}
              </span>
            )}
            
            {isSaved && (
              <span className="text-green-500 mr-4 animate-fadeIn">
                预设已保存！
              </span>
            )}
            
            <button
              type="submit"
              disabled={isLoading}
              className={`flex items-center px-4 py-2 bg-[#0A84FF] text-white rounded-md hover:bg-[#0070E0] transition-colors ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              <Save className="w-5 h-5 mr-1" />
              <span>{isLoading ? '保存中...' : '保存预设'}</span>
            </button>
          </div>
        </form>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-[#1C1C1E] mb-4">编写有效提示词的技巧</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-[#0A84FF] mb-2">筛选提示词技巧</h4>
            <ul className="list-disc pl-5 text-gray-700 space-y-1 text-sm">
              <li>明确指定要提取的信息类型</li>
              <li>设定清晰的重要性和相关性标准</li>
              <li>指定所需的信息格式</li>
              <li>包含您的兴趣或行业背景</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium text-[#0A84FF] mb-2">总结提示词技巧</h4>
            <ul className="list-disc pl-5 text-gray-700 space-y-1 text-sm">
              <li>要求清晰的章节标题以便更好组织</li>
              <li>指定所需的摘要详细程度</li>
              <li>要求突出关键见解</li>
              <li>适时要求可执行的建议或后续步骤</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromptSettings;