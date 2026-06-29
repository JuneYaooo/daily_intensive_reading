import React, { useEffect } from 'react';
import { useCardStore } from '../../store/stores';

const FavoriteCards: React.FC = () => {
  const { cards, fetchCards, deleteCard, isLoading, error } = useCardStore();

  useEffect(() => {
    fetchCards();
  }, [fetchCards]);

  const handleDelete = async (cardId: number) => {
    if (window.confirm('Are you sure you want to remove this card?')) {
      await deleteCard(cardId);
    }
  };

  if (isLoading && cards.length === 0) {
    return <div className="p-4">Loading favorite cards...</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Favorite Cards</h2>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-300 rounded-md text-red-700">
          <p className="font-medium">Error:</p>
          <p>{error}</p>
        </div>
      )}

      {cards.length === 0 && !isLoading && (
        <div className="text-center p-8 bg-gray-50 rounded-md">
          <p className="text-gray-500">No favorite cards yet.</p>
        </div>
      )}

      {cards.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {cards.map((card) => {
            const cardId = card.id;
            return (
            <div key={cardId} className="p-4 bg-white border border-gray-200 rounded-md shadow">
              <div className="flex justify-between items-start">
                <h3 className="text-lg font-medium">{card.title}</h3>
                {cardId !== undefined && (
                  <button
                    onClick={() => handleDelete(cardId)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Remove
                  </button>
                )}
              </div>

              {card.author && <p className="text-sm text-gray-600">Author: {card.author}</p>}
              {card.source_url && (
                <a href={card.source_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600">
                  {card.source_url}
                </a>
              )}

              {card.conclusion && (
                <p className="mt-2 text-sm text-gray-700 line-clamp-4">{card.conclusion}</p>
              )}

              {card.key_points && card.key_points.length > 0 && (
                <ul className="mt-3 list-disc pl-5 text-sm text-gray-700">
                  {card.key_points.map((point, index) => (
                    <li key={`${cardId}-point-${index}`}>{point}</li>
                  ))}
                </ul>
              )}
            </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FavoriteCards;
