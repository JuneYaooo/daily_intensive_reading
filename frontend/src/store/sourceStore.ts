import { create } from 'zustand';
import { Source } from '../types';
import { sourceService } from '../services';

interface SourceState {
  sources: Source[];
  currentSource: Source | null;
  isLoading: boolean;
  error: string | null;
  fetchSources: () => Promise<void>;
  fetchSourceById: (id: number) => Promise<void>;
  createSource: (source: Source) => Promise<void>;
  updateSource: (id: number, source: Source) => Promise<void>;
  deleteSource: (id: number) => Promise<void>;
}

const useSourceStore = create<SourceState>((set, get) => ({
  sources: [],
  currentSource: null,
  isLoading: false,
  error: null,

  fetchSources: async () => {
    set({ isLoading: true, error: null });
    try {
      const sources = await sourceService.getAllSources();
      set({ sources, isLoading: false });
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to fetch sources' 
      });
    }
  },

  fetchSourceById: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      const source = await sourceService.getSourceById(id);
      set({ currentSource: source, isLoading: false });
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to fetch source' 
      });
    }
  },

  createSource: async (source: Source) => {
    set({ isLoading: true, error: null });
    try {
      const newSource = await sourceService.createSource(source);
      set(state => ({ 
        sources: [...state.sources, newSource],
        currentSource: newSource,
        isLoading: false 
      }));
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to create source' 
      });
    }
  },

  updateSource: async (id: number, source: Source) => {
    set({ isLoading: true, error: null });
    try {
      const updatedSource = await sourceService.updateSource(id, source);
      set(state => ({ 
        sources: state.sources.map(s => s.id === id ? updatedSource : s),
        currentSource: updatedSource,
        isLoading: false 
      }));
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to update source' 
      });
    }
  },

  deleteSource: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      await sourceService.deleteSource(id);
      set(state => ({ 
        sources: state.sources.filter(s => s.id !== id),
        currentSource: state.currentSource?.id === id ? null : state.currentSource,
        isLoading: false 
      }));
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to delete source' 
      });
    }
  }
}));

export default useSourceStore; 