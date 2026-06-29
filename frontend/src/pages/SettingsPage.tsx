import React from 'react';
import PromptSettings from '../components/settings/PromptSettings';
import ApiSettings from '../components/settings/ApiSettings';

const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-[#FF6B6B]">设置</h1>
      </div>

      <ApiSettings />
      <PromptSettings />
    </div>
  );
};

export default SettingsPage;
