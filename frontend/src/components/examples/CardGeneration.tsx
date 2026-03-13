import React, { useEffect, useState } from 'react';
import { useCardStore } from '../../store/stores';
import { usePromptStore } from '../../store/stores';
import { CardGenerationRequest, Prompt } from '../../types';

const CardGeneration: React.FC = () => {
  const { generateCard, isLoading, error } = useCardStore();
  const { prompts, fetchPrompts } = usePromptStore();
  
  const [selectedContent, setSelectedContent] = useState('');
  const [selectedPromptId, setSelectedPromptId] = useState<number | undefined>(undefined);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [source, setSource] = useState('');
  const [tags, setTags] = useState('');
  const [generatedCard, setGeneratedCard] = useState<any>(null);

  useEffect(() => {
    fetchPrompts();
  }, [fetchPrompts]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedContent.trim()) {
      alert('Please enter selected content');
      return;
    }
    
    const cardData: CardGenerationRequest = {
      selected_content: selectedContent,
      prompt_id: selectedPromptId,
      title: title || undefined,
      author: author || undefined,
      source: source || undefined,
      tags: tags ? tags.split(',').map(tag => tag.trim()) : undefined
    };
    
    const result = await generateCard(cardData);
    if (result) {
      setGeneratedCard(result);
      
      // Reset form
      setSelectedContent('');
      setSelectedPromptId(undefined);
      setTitle('');
      setAuthor('');
      setSource('');
      setTags('');
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Generate Reading Card</h2>
      
      {/* Card Generation Form */}
      <div className="mb-6 p-4 bg-gray-50 rounded-md">
        <form onSubmit={handleSubmit}>
          <div className="flex flex-col space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Selected Content*</label>
              <textarea
                value={selectedContent}
                onChange={(e) => setSelectedContent(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={8}
                required
                placeholder="Paste the content you want to generate a card from..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Prompt Template</label>
              <select
                value={selectedPromptId || ''}
                onChange={(e) => setSelectedPromptId(e.target.value ? Number(e.target.value) : undefined)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
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
              <label className="block text-sm font-medium text-gray-700">Title (Optional)</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Custom title for the card"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Author (Optional)</label>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Author of the content"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Source (Optional)</label>
              <input
                type="text"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Source of the content"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Tags (Optional)</label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Comma-separated tags (e.g., 'history, science, technology')"
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300"
            >
              {isLoading ? 'Generating...' : 'Generate Card'}
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
      
      {/* Generated Card Preview */}
      {generatedCard && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Generated Card</h3>
          <div className="p-4 bg-white border border-gray-200 rounded-md shadow">
            <h4 className="text-lg font-medium mb-2">{generatedCard.title}</h4>
            {generatedCard.author && <p className="text-sm text-gray-600">Author: {generatedCard.author}</p>}
            {generatedCard.source && <p className="text-sm text-gray-600">Source: {generatedCard.source}</p>}
            
            <div className="my-3 prose">
              <div
                dangerouslySetInnerHTML={{
                  __html: generatedCard.content.replace(/\n/g, '<br/>')
                }}
              />
            </div>
            
            {generatedCard.tags && generatedCard.tags.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1">
                {generatedCard.tags.map((tag: any, index: number) => (
                  <span
                    key={index}
                    className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded"
                  >
                    {tag.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CardGeneration; 