import React, { useEffect, useState } from 'react';
import { useCardStore } from '../../store/stores';
import { ReadingCard } from '../../types';

const FavoriteCards: React.FC = () => {
  const { favoriteCards, fetchFavoriteCards, unfavoriteCard, isLoading, error } = useCardStore();
  const [userId, setUserId] = useState<number>(1); // Default user ID, replace with actual user ID from auth system
  
  useEffect(() => {
    if (userId) {
      fetchFavoriteCards(userId);
    }
  }, [userId, fetchFavoriteCards]);

  const handleUnfavorite = async (cardId: number) => {
    if (window.confirm('Are you sure you want to remove this card from favorites?')) {
      await unfavoriteCard(cardId, userId);
    }
  };

  if (isLoading && favoriteCards.length === 0) {
    return <div className="p-4">Loading favorite cards...</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Your Favorite Cards</h2>
      
      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-300 rounded-md text-red-700">
          <p className="font-medium">Error:</p>
          <p>{error}</p>
        </div>
      )}
      
      {/* No Favorites Message */}
      {favoriteCards.length === 0 && !isLoading && (
        <div className="text-center p-8 bg-gray-50 rounded-md">
          <p className="text-gray-500">You don't have any favorite cards yet.</p>
        </div>
      )}
      
      {/* Favorites List */}
      {favoriteCards.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {favoriteCards.map((card) => (
            <div key={card.id} className="p-4 bg-white border border-gray-200 rounded-md shadow">
              <div className="flex justify-between items-start">
                <h3 className="text-lg font-medium">{card.title}</h3>
                <button
                  onClick={() => card.id && handleUnfavorite(card.id)}
                  className="text-red-600 hover:text-red-900"
                >
                  Remove
                </button>
              </div>
              
              {card.author && <p className="text-sm text-gray-600">Author: {card.author}</p>}
              {card.source && <p className="text-sm text-gray-600">Source: {card.source}</p>}
              
              <div className="mt-2 prose prose-sm max-h-40 overflow-y-auto">
                <div
                  dangerouslySetInnerHTML={{
                    __html: card.content.substring(0, 200) + (card.content.length > 200 ? '...' : '')
                  }}
                />
              </div>
              
              {card.tags && card.tags.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {card.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded"
                    >
                      {tag.name}
                    </span>
                  ))}
                </div>
              )}
              
              <div className="mt-3 text-right">
                <a href={`/cards/${card.id}`} className="text-blue-600 hover:text-blue-800 text-sm">
                  View Details
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FavoriteCards; 