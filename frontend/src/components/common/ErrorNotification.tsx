import React from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { useAppStore } from '../../store';

const ErrorNotification: React.FC = () => {
  const { errorNotification, dismissError } = useAppStore();

  if (!errorNotification.visible) return null;

  return (
    <div className="fixed top-20 right-4 z-50 max-w-md animate-slide-in">
      <div className="bg-red-600 text-white rounded-lg shadow-lg p-4 flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div className="flex-1 text-sm whitespace-pre-line break-words">
          {errorNotification.message}
        </div>
        <button
          onClick={dismissError}
          className="flex-shrink-0 text-white hover:text-red-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default ErrorNotification;
