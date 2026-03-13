import React, { useEffect, useState } from 'react';
import { useReportStore } from '../../store/stores';
import { usePromptStore } from '../../store/stores';
import { useSourceStore } from '../../store/stores';
import { ReportGenerationRequest } from '../../types';

const ReportGeneration: React.FC = () => {
  const { generateReport, generatedReport, isLoading, error, clearReport } = useReportStore();
  const { prompts, fetchPrompts } = usePromptStore();
  const { sources, fetchSources } = useSourceStore();
  
  const [content, setContent] = useState('');
  const [selectedPromptId, setSelectedPromptId] = useState<number | undefined>(undefined);
  const [selectedSourceId, setSelectedSourceId] = useState<number | undefined>(undefined);

  useEffect(() => {
    fetchPrompts();
    fetchSources();
    
    return () => {
      clearReport();
    };
  }, [fetchPrompts, fetchSources, clearReport]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!content.trim()) {
      alert('Please enter content to analyze');
      return;
    }
    
    if (!selectedPromptId) {
      alert('Please select a prompt template');
      return;
    }
    
    const reportData: ReportGenerationRequest = {
      content: content,
      prompt_id: selectedPromptId,
      source_id: selectedSourceId
    };
    
    await generateReport(reportData);
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Generate Report</h2>
      
      {/* Report Generation Form */}
      <div className="mb-6 p-4 bg-gray-50 rounded-md">
        <form onSubmit={handleSubmit}>
          <div className="flex flex-col space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Content*</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={10}
                required
                placeholder="Paste the content you want to analyze..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Prompt Template*</label>
              <select
                value={selectedPromptId || ''}
                onChange={(e) => setSelectedPromptId(e.target.value ? Number(e.target.value) : undefined)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              >
                <option value="">-- Select a prompt template --</option>
                {prompts.map((prompt) => (
                  <option key={prompt.id} value={prompt.id}>
                    {prompt.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Source (Optional)</label>
              <select
                value={selectedSourceId || ''}
                onChange={(e) => setSelectedSourceId(e.target.value ? Number(e.target.value) : undefined)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">-- Select a source --</option>
                {sources.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.name}
                  </option>
                ))}
              </select>
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300"
            >
              {isLoading ? 'Generating...' : 'Generate Report'}
            </button>
          </div>
        </form>
      </div>
      
      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-300 rounded-md text-red-700">
          <p className="font-medium">Error:</p>
          <p>{error}</p>
        </div>
      )}
      
      {/* Generated Report */}
      {generatedReport && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Generated Report</h3>
          <div className="p-4 bg-white border border-gray-200 rounded-md shadow">
            {generatedReport.source && (
              <p className="text-sm text-gray-600 mb-2">
                Source: {generatedReport.source}
              </p>
            )}
            <p className="text-sm text-gray-600 mb-4">
              Using prompt: {generatedReport.prompt}
            </p>
            
            <div className="prose max-w-none">
              <div
                dangerouslySetInnerHTML={{
                  __html: generatedReport.report.replace(/\n/g, '<br/>')
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportGeneration; 