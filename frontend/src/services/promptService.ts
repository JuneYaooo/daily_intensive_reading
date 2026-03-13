import api from './api';
import { Prompt } from '../types';

const BASE_URL = '/api/prompts';

const promptService = {
  /**
   * Get all prompts
   */
  async getAllPrompts(): Promise<Prompt[]> {
    const response = await api.get(BASE_URL);
    return response.data;
  },
  
  /**
   * Get prompt by ID
   */
  async getPromptById(id: number): Promise<Prompt> {
    const response = await api.get(`${BASE_URL}/${id}`);
    return response.data;
  },
  
  /**
   * Get all default prompts
   */
  async getDefaultPrompts(): Promise<Prompt[]> {
    const response = await api.get(`${BASE_URL}/defaults`);
    return response.data;
  },
  
  /**
   * Get default prompt by type (filter, summary, general)
   */
  async getDefaultPromptByType(type: 'filter' | 'summary' | 'general'): Promise<Prompt> {
    const response = await api.get(`${BASE_URL}/defaults/${type}`);
    return response.data;
  },
  
  /**
   * Create a new prompt
   */
  async createPrompt(prompt: Prompt): Promise<Prompt> {
    const response = await api.post(BASE_URL, prompt);
    return response.data;
  },
  
  /**
   * Update an existing prompt
   */
  async updatePrompt(id: number, prompt: Prompt): Promise<Prompt> {
    // Ensure required fields are present
    if (!prompt.name || !prompt.content) {
      console.error('Validation error: Missing required fields', prompt);
      throw new Error('Name and content are required fields for a prompt');
    }
    
    // Make sure the data structure matches what the backend expects
    const promptData = {
      name: prompt.name,
      content: prompt.content,
      description: prompt.description || '',
      type: prompt.type || 'general',
      is_default: prompt.is_default !== undefined ? prompt.is_default : false
    };
    
    console.log(`Updating prompt ${id} with data:`, promptData);
    
    try {
      const response = await api.put(`${BASE_URL}/${id}`, promptData);
      return response.data;
    } catch (error) {
      console.error('Error updating prompt:', error);
      console.error('Request payload was:', promptData);
      throw error;
    }
  },
  
  /**
   * Delete a prompt
   */
  async deletePrompt(id: number): Promise<void> {
    await api.delete(`${BASE_URL}/${id}`);
  }
};

export default promptService; 