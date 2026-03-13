import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';
import { useAppStore } from '../../store';

interface PromptEditorProps {
  type: 'filter' | 'summary';
  defaultValue: string;
  onChange: (value: string) => void;
  onReset: () => void;
}

const PromptEditor: React.FC<PromptEditorProps> = ({
  type,
  defaultValue,
  onChange,
  onReset
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [value, setValue] = useState('');
  
  // 确保defaultValue正确设置和应用
  useEffect(() => {
    if (defaultValue) {
      setValue(defaultValue);
      // 初始化时将默认值传递给父组件
      onChange(defaultValue);
      console.log(`设置${type}默认提示:`, defaultValue);
    }
  }, [defaultValue, type, onChange]);
  
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    console.log(`${type} prompt changed to:`, newValue);
    setValue(newValue);
    onChange(newValue);
  };
  
  const handleReset = () => {
    console.log(`重置${type}提示到默认值:`, defaultValue);
    setValue(defaultValue || '');
    onChange(defaultValue || '');
    onReset();
  };
  
  const getTitle = () => {
    return type === 'filter' ? '过滤信息提示词' : '生成卡片提示词';
  };
  
  const getDescription = () => {
    return type === 'filter'
      ? '用来过滤和提取有价值的链接'
      : '用来把过滤后的内容生成摘要卡片';
  };
  
  // 确定当前值是自定义的还是默认的
  const isCustomValue = value !== defaultValue && value !== '';
  
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden transition-all duration-300">
      <div
        className="p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className="font-semibold text-[#1A365D]">
          {getTitle()} {isCustomValue ? '(自定义)' : '(默认)'}
        </h3>
        <button className="text-gray-500 p-1">
          {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>
      
      {isExpanded && (
        <div className="p-4">
          <p className="text-sm text-gray-500 mb-3">{getDescription()}</p>
          
          <div className="mb-3">
            <textarea
              value={value}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#0D9488] transition-all"
              rows={6}
              placeholder={`输入自定义${type === 'filter' ? '过滤' : '总结'}提示`}
            />
          </div>
          
          {isCustomValue && (
            <div className="flex justify-end">
              <button
                onClick={handleReset}
                className="flex items-center px-3 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                <RefreshCw className="w-4 h-4 mr-1" />
                <span>重置为默认值</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PromptEditor;