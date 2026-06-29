import React, { useState } from 'react';
import { Key, Trash2, Info, Save } from 'lucide-react';
import { useAppStore } from '../../store';

const ApiSettings: React.FC = () => {
  const { apiConfig, setApiConfig, clearApiConfig } = useAppStore();
  const [localConfig, setLocalConfig] = useState({ ...apiConfig });
  const [isSaved, setIsSaved] = useState(false);

  const hasAnyConfig = !!(
    apiConfig.jigsawstackKeys ||
    apiConfig.modelBaseUrl ||
    apiConfig.modelName ||
    apiConfig.modelApiKey
  );

  const isDirty =
    localConfig.jigsawstackKeys !== apiConfig.jigsawstackKeys ||
    localConfig.modelBaseUrl !== apiConfig.modelBaseUrl ||
    localConfig.modelName !== apiConfig.modelName ||
    localConfig.modelApiKey !== apiConfig.modelApiKey;

  const handleSave = () => {
    setApiConfig(localConfig);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const handleClear = () => {
    clearApiConfig();
    setLocalConfig({
      jigsawstackKeys: '',
      modelBaseUrl: '',
      modelName: '',
      modelApiKey: '',
    });
    setIsSaved(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-[#1C1C1E]">API 配置</h2>
        {hasAnyConfig && (
          <button
            onClick={handleClear}
            className="flex items-center px-4 py-2 border border-red-400 text-red-500 rounded-md hover:bg-red-50 transition-colors"
          >
            <Trash2 className="w-4 h-4 mr-1" />
            <span>清除配置</span>
          </button>
        )}
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start space-x-2">
        <Info className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-amber-800">
          此处配置仅在当前浏览器标签页中生效，关闭标签页后自动清除。刷新页面不会丢失。留空的字段将使用服务器默认配置。
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-[#1C1C1E] mb-4 flex items-center">
            <Key className="w-5 h-5 mr-2 text-[#0A84FF]" />
            爬虫配置 (JigsawStack)
          </h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Keys
            </label>
            <p className="text-gray-500 text-xs mb-2">
              支持多个 Key，用英文逗号分隔。用于网页内容爬取。
            </p>
            <textarea
              value={localConfig.jigsawstackKeys}
              onChange={(e) => setLocalConfig({ ...localConfig, jigsawstackKeys: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0A84FF] transition-all font-mono text-sm"
              rows={2}
              placeholder="sk_xxx1,sk_xxx2,sk_xxx3"
            />
          </div>
        </div>

        <hr className="border-gray-200" />

        <div>
          <h3 className="text-lg font-semibold text-[#1C1C1E] mb-4 flex items-center">
            <Key className="w-5 h-5 mr-2 text-[#0A84FF]" />
            模型配置
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Base URL
              </label>
              <input
                type="text"
                value={localConfig.modelBaseUrl}
                onChange={(e) => setLocalConfig({ ...localConfig, modelBaseUrl: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0A84FF] transition-all font-mono text-sm"
                placeholder="https://api.deepseek.com/v1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                模型名称
              </label>
              <input
                type="text"
                value={localConfig.modelName}
                onChange={(e) => setLocalConfig({ ...localConfig, modelName: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0A84FF] transition-all font-mono text-sm"
                placeholder="deepseek-chat"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key
              </label>
              <input
                type="password"
                value={localConfig.modelApiKey}
                onChange={(e) => setLocalConfig({ ...localConfig, modelApiKey: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0A84FF] transition-all font-mono text-sm"
                placeholder="sk-..."
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end items-center pt-2">
          {isSaved && (
            <span className="text-green-500 mr-4 animate-fadeIn">
              配置已保存！
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={!isDirty && !isSaved}
            className={`flex items-center px-4 py-2 bg-[#0A84FF] text-white rounded-md hover:bg-[#0070E0] transition-colors ${
              !isDirty && !isSaved ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <Save className="w-5 h-5 mr-1" />
            <span>保存配置</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApiSettings;
