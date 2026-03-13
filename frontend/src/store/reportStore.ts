import { create } from 'zustand';
import { ReportGenerationRequest, ReportGenerationResponse } from '../types';
import { reportService } from '../services';

interface ReportState {
  generatedReport: ReportGenerationResponse | null;
  isLoading: boolean;
  error: string | null;
  generateReport: (data: ReportGenerationRequest) => Promise<ReportGenerationResponse | null>;
  clearReport: () => void;
}

const useReportStore = create<ReportState>((set, get) => ({
  generatedReport: null,
  isLoading: false,
  error: null,

  generateReport: async (data: ReportGenerationRequest) => {
    set({ isLoading: true, error: null });
    try {
      const report = await reportService.generateReport(data);
      set({ generatedReport: report, isLoading: false });
      return report;
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to generate report' 
      });
      return null;
    }
  },

  clearReport: () => {
    set({ generatedReport: null, error: null });
  }
}));

export default useReportStore; 