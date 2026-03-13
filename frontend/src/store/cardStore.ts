import { create } from 'zustand';
import { ReadingCard } from '../types';
import { cardService } from '../services';

interface CardState {
  cards: ReadingCard[];
  currentCard: ReadingCard | null;
  isLoading: boolean;
  error: string | null;
  fetchCards: () => Promise<void>;
  fetchCardById: (id: number) => Promise<void>;
  createCard: (data: {
    title: string,
    source_url?: string,
    conclusion?: string,
    key_points?: string[],
    quotes?: string[],
    author?: string
  }) => Promise<ReadingCard | null>;
  deleteCard: (id: number) => Promise<void>;
  updateCard: (id: number, data: {
    title?: string,
    source_url?: string,
    conclusion?: string,
    key_points?: string[],
    quotes?: string[],
    author?: string
  }) => Promise<void>;
}

const useCardStore = create<CardState>((set, get) => ({
  cards: [],
  currentCard: null,
  isLoading: false,
  error: null,

  fetchCards: async () => {
    set({ isLoading: true, error: null });
    try {
      const cards = await cardService.getAllCards();
      set({ cards, isLoading: false });
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to fetch cards' 
      });
    }
  },

  fetchCardById: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      const card = await cardService.getCardById(id);
      set({ currentCard: card, isLoading: false });
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to fetch card' 
      });
    }
  },

  createCard: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const newCard = await cardService.createCard(data);
      if (newCard) {
        set(state => ({ 
          cards: [...state.cards, newCard],
          currentCard: newCard,
          isLoading: false 
        }));
      }
      return newCard;
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to create card' 
      });
      return null;
    }
  },

  deleteCard: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      const success = await cardService.deleteCard(id);
      if (success) {
        set(state => ({ 
          cards: state.cards.filter(card => card.id !== id),
          currentCard: state.currentCard?.id === id ? null : state.currentCard,
          isLoading: false 
        }));
      }
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to delete card' 
      });
    }
  },

  updateCard: async (id: number, data) => {
    set({ isLoading: true, error: null });
    try {
      const updatedCard = await cardService.updateCard(id, data);
      if (updatedCard) {
        set(state => ({ 
          cards: state.cards.map(card => 
            card.id === id ? updatedCard : card
          ),
          currentCard: state.currentCard?.id === id ? updatedCard : state.currentCard,
          isLoading: false 
        }));
      }
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to update card' 
      });
    }
  }
}));

export default useCardStore; 