import React from 'react';
import PromptSettings from '../components/settings/PromptSettings';

const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-[#FF6B6B]">设置</h1>
      </div>
      
      <PromptSettings />
    </div>
  );
};

export default SettingsPage;