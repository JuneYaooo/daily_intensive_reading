import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store';
import useCardStore from '../store/cardStore';
import BriefCard from '../components/execution/BriefCard';
import { Brief } from '../types';

const FavoritesPage: React.FC = () => {
  const { getFavorites, briefs } = useAppStore();
  const { fetchCards, cards, isLoading } = useCardStore();
  const [localFavorites, setLocalFavorites] = useState<Brief[]>([]);
  const [loading, setLoading] = useState(true);

  // Load favorites from both local store and backend
  // Now depends on briefs to refresh when favorites change
  useEffect(() => {
    const loadFavorites = async () => {
      try {
        setLoading(true);
        
        // Get local favorites from store
        const localFavs = getFavorites();
        setLocalFavorites(localFavs);
        
        // Get saved favorite cards
        await fetchCards();
        
      } catch (error) {
        console.error('Error loading favorites:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadFavorites();
  }, [getFavorites, fetchCards, briefs]); // Add briefs as dependency to refresh when favorites change
  
  // Convert saved cards to Brief format
  const savedCardsFormatted: Brief[] = cards.map(card => ({
    id: String(card.id || ''),
    sourceId: 'database',
    sourceName: card.title || '',
    sourceUrl: card.source_url || '',
    content: formatCardContent(card),
    createdAt: card.created_at ? new Date(card.created_at).getTime() : Date.now(),
    favoritedAt: card.created_at ? new Date(card.created_at).getTime() : Date.now(),
    isFavorite: true,
    databaseId: card.id || undefined,
    keyPoints: card.key_points || [],
    quotes: card.quotes || [],
    author: card.author || ''
  }));
  
  // Format card content for display
  function formatCardContent(card: any): string {
    // Only include the conclusion, no key points or quotes
    return card.conclusion || '';
  }
  
  // Combine both sources, preventing duplicates
  // If a brief exists in both sources, prefer the backend version
  const combinedFavorites = [
    ...localFavorites.filter(local =>
      !savedCardsFormatted.some(saved => saved.sourceUrl === local.sourceUrl)
    ),
    ...savedCardsFormatted
  ].sort((a, b) => {
    // Sort by favoritedAt or createdAt, newest first
    const timeA = a.favoritedAt || a.createdAt || 0;
    const timeB = b.favoritedAt || b.createdAt || 0;
    return timeB - timeA;
  });
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-[#1C1C1E]">收藏夹</h1>
      </div>
      
      {loading || isLoading ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-500">正在加载收藏...</p>
        </div>
      ) : combinedFavorites.length > 0 ? (
        <div className="grid grid-cols-1 gap-6">
          {combinedFavorites.map((brief) => (
            <BriefCard
              key={brief.id}
              brief={brief}
              showFavoritedAt={true}
            />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-500 mb-2">暂无收藏的简报</p>
          <p className="text-sm text-gray-400">
            在浏览简报时点击心形图标即可收藏
          </p>
        </div>
      )}
    </div>
  );
};

export default FavoritesPage;