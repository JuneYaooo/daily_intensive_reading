import React, { useState } from 'react';
import { useCardStore } from '../../store/stores';
import { ReadingCard } from '../../types';

const CardGeneration: React.FC = () => {
  const { createCard, isLoading, error } = useCardStore();
  const [title, setTitle] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [author, setAuthor] = useState('');
  const [conclusion, setConclusion] = useState('');
  const [keyPoints, setKeyPoints] = useState('');
  const [quotes, setQuotes] = useState('');
  const [createdCard, setCreatedCard] = useState<ReadingCard | null>(null);

  const splitLines = (value: string): string[] =>
    value
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      alert('Please enter a title');
      return;
    }

    const card = await createCard({
      title: title.trim(),
      source_url: sourceUrl.trim() || undefined,
      author: author.trim() || undefined,
      conclusion: conclusion.trim() || undefined,
      key_points: splitLines(keyPoints),
      quotes: splitLines(quotes),
    });

    if (card) {
      setCreatedCard(card);
      setTitle('');
      setSourceUrl('');
      setAuthor('');
      setConclusion('');
      setKeyPoints('');
      setQuotes('');
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Create Favorite Card</h2>

      <div className="mb-6 p-4 bg-gray-50 rounded-md">
        <form onSubmit={handleSubmit}>
          <div className="flex flex-col space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Title*</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Source URL</label>
              <input
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="https://example.com/article"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Author</label>
              <input
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Conclusion</label>
              <textarea
                value={conclusion}
                onChange={(e) => setConclusion(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={6}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Key Points</label>
              <textarea
                value={keyPoints}
                onChange={(e) => setKeyPoints(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={4}
                placeholder="One point per line"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Quotes</label>
              <textarea
                value={quotes}
                onChange={(e) => setQuotes(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={4}
                placeholder="One quote per line"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300"
            >
              {isLoading ? 'Saving...' : 'Save Card'}
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-300 rounded-md text-red-700">
          <p className="font-medium">Error:</p>
          <p>{error}</p>
        </div>
      )}

      {createdCard && (
        <div className="p-4 bg-white border border-gray-200 rounded-md shadow">
          <h3 className="text-lg font-semibold mb-2">Saved Card</h3>
          <p className="font-medium">{createdCard.title}</p>
          {createdCard.source_url && (
            <a href={createdCard.source_url} className="text-sm text-blue-600" target="_blank" rel="noopener noreferrer">
              {createdCard.source_url}
            </a>
          )}
        </div>
      )}
    </div>
  );
};

export default CardGeneration;
