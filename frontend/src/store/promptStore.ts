import { create } from 'zustand';
import { Prompt } from '../types';
import { promptService } from '../services';

interface PromptState {
  prompts: Prompt[];
  currentPrompt: Prompt | null;
  isLoading: boolean;
  error: string | null;
  fetchPrompts: () => Promise<void>;
  fetchPromptById: (id: number) => Promise<void>;
  createPrompt: (prompt: Prompt) => Promise<void>;
  updatePrompt: (id: number, prompt: Prompt) => Promise<void>;
  deletePrompt: (id: number) => Promise<void>;
}

const usePromptStore = create<PromptState>((set, get) => ({
  prompts: [],
  currentPrompt: null,
  isLoading: false,
  error: null,

  fetchPrompts: async () => {
    set({ isLoading: true, error: null });
    try {
      const prompts = await promptService.getAllPrompts();
      set({ prompts, isLoading: false });
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to fetch prompts' 
      });
    }
  },

  fetchPromptById: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      const prompt = await promptService.getPromptById(id);
      set({ currentPrompt: prompt, isLoading: false });
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to fetch prompt' 
      });
    }
  },

  createPrompt: async (prompt: Prompt) => {
    set({ isLoading: true, error: null });
    try {
      const newPrompt = await promptService.createPrompt(prompt);
      set(state => ({ 
        prompts: [...state.prompts, newPrompt],
        currentPrompt: newPrompt,
        isLoading: false 
      }));
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to create prompt' 
      });
    }
  },

  updatePrompt: async (id: number, prompt: Prompt) => {
    set({ isLoading: true, error: null });
    console.log('Updating prompt in store:', id, prompt);
    
    // Validate prompt has required fields
    if (!prompt.name || !prompt.content) {
      console.error('Missing required fields for prompt update:', prompt);
      set({
        isLoading: false,
        error: 'Prompt update failed: Name and content are required'
      });
      return;
    }
    
    try {
      const updatedPrompt = await promptService.updatePrompt(id, prompt);
      console.log('Prompt updated successfully:', updatedPrompt);
      set(state => ({ 
        prompts: state.prompts.map(p => p.id === id ? updatedPrompt : p),
        currentPrompt: updatedPrompt,
        isLoading: false 
      }));
    } catch (error) {
      console.error('Error updating prompt:', error);
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to update prompt' 
      });
    }
  },

  deletePrompt: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      await promptService.deletePrompt(id);
      set(state => ({ 
        prompts: state.prompts.filter(p => p.id !== id),
        currentPrompt: state.currentPrompt?.id === id ? null : state.currentPrompt,
        isLoading: false 
      }));
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to delete prompt' 
      });
    }
  }
}));

export default usePromptStore; 