import api from './api';
import { ReadingCard } from '../types';

const BASE_URL = '/api/cards';

const cardService = {
  /**
   * Get all cards (favorites)
   */
  async getAllCards(): Promise<ReadingCard[]> {
    try {
      const response = await api.get(`${BASE_URL}/`);
      return response.data;
    } catch (error) {
      console.error('Error getting cards:', error);
      return [];
    }
  },
  
  /**
   * Get card by ID
   */
  async getCardById(id: number): Promise<ReadingCard | null> {
    try {
      const response = await api.get(`${BASE_URL}/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error getting card ${id}:`, error);
      return null;
    }
  },
  
  /**
   * Create a new favorite card
   */
  async createCard(data: {
    title: string,
    source_url?: string,
    conclusion?: string,
    key_points?: string[],
    quotes?: string[],
    author?: string
  }): Promise<ReadingCard | null> {
    try {
      const response = await api.post(`${BASE_URL}/create`, data);
      return response.data;
    } catch (error) {
      console.error('Error creating card:', error);
      return null;
    }
  },
  
  /**
   * Delete a card (unfavorite)
   */
  async deleteCard(id: number): Promise<boolean> {
    try {
      await api.delete(`${BASE_URL}/${id}`);
      return true;
    } catch (error) {
      console.error(`Error deleting card ${id}:`, error);
      return false;
    }
  },
  
  /**
   * Update a card
   */
  async updateCard(id: number, data: {
    title?: string,
    source_url?: string,
    conclusion?: string,
    key_points?: string[],
    quotes?: string[],
    author?: string
  }): Promise<ReadingCard | null> {
    try {
      const response = await api.put(`${BASE_URL}/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating card ${id}:`, error);
      return null;
    }
  },

  /**
   * Favorite a card (creates a new card if it doesn't exist)
   */
  async favoriteCard(id: number, userId: number): Promise<ReadingCard | null> {
    try {
      // If the brief doesn't have an ID in the database yet,
      // we need to create a new favorite card
      const data = {
        title: `Favorited Item ${id}`,
        source_url: `https://source-url.com/${id}`
      };
      const response = await api.post(`${BASE_URL}/create`, data);
      return response.data;
    } catch (error) {
      console.error(`Error favoriting card ${id}:`, error);
      return null;
    }
  },

  /**
   * Unfavorite a card (deletes the card from favorites)
   */
  async unfavoriteCard(id: number, userId: number): Promise<boolean> {
    try {
      await api.delete(`${BASE_URL}/${id}`);
      return true;
    } catch (error) {
      console.error(`Error unfavoriting card ${id}:`, error);
      return false;
    }
  }
};

export default cardService; 