import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../../store';

const PromptDialog: React.FC = () => {
  const { showPromptDialog, setShowPromptDialog } = useAppStore();
  const navigate = useNavigate();

  if (!showPromptDialog) {
    return null;
  }

  const handleCreatePrompts = () => {
    setShowPromptDialog(false);
    navigate('/settings');
  };

  const handleCancel = () => {
    setShowPromptDialog(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full shadow-lg">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">未找到提示词</h3>
        
        <p className="text-gray-600 mb-6">
          您还没有创建默认提示词。提示词用于筛选和总结内容，对于获得高质量的结果至关重要。您想现在创建提示词吗？
        </p>
        
        <div className="flex justify-end space-x-3">
          <button
            onClick={handleCancel}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
          >
            稍后再说
          </button>
          
          <button
            onClick={handleCreatePrompts}
            className="px-4 py-2 bg-[#0A84FF] text-white rounded-md hover:bg-[#0070E0] transition-colors"
          >
            前往创建
          </button>
        </div>
      </div>
    </div>
  );
};

export default PromptDialog; 