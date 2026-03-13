import api from './api';
import { ReportGenerationRequest, ReportGenerationResponse } from '../types';

const BASE_URL = '/api/reports';

const reportService = {
  /**
   * Generate a report based on content and prompt
   * Can specify prompt_id, prompt_content, or prompt_type
   */
  async generateReport(data: ReportGenerationRequest): Promise<ReportGenerationResponse> {
    const response = await api.post(`${BASE_URL}/generate`, data);
    return response.data;
  }
};

export default reportService; 