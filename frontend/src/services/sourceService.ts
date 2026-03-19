import api from './api';
import { Source } from '../types';

const BASE_URL = '/api/sources/';

const sourceService = {
  /**
   * Get all sources
   */
  async getAllSources(): Promise<Source[]> {
    const response = await api.get(BASE_URL);
    return response.data;
  },
  
  /**
   * Get source by ID
   */
  async getSourceById(id: number): Promise<Source> {
    const response = await api.get(`${BASE_URL}/${id}`);
    return response.data;
  },
  
  /**
   * Create a new source
   */
  async createSource(source: Source): Promise<Source> {
    const response = await api.post(BASE_URL, source);
    return response.data;
  },
  
  /**
   * Update an existing source
   */
  async updateSource(id: number, source: Source): Promise<Source> {
    const response = await api.put(`${BASE_URL}/${id}`, source);
    return response.data;
  },
  
  /**
   * Delete a source
   */
  async deleteSource(id: number): Promise<void> {
    await api.delete(`${BASE_URL}/${id}`);
  }
};

export default sourceService; 