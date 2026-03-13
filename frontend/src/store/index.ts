import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Brief, Source, UserSettings } from '../types';
import useSourceStore from './sourceStore';
import usePromptStore from './promptStore';
import useReportStore from './reportStore';
import useCardStore from './cardStore';
import { reportService, promptService, sourceService } from '../services';
import dailyReadingService, { SummaryCard, FilteredUrl } from '../services/dailyReadingService';

// Extend the Brief interface to include keyPoints and quotes if not already in types.ts
interface ExtendedBrief extends Brief {
  keyPoints?: string[];
  quotes?: string[];
  author?: string;
  databaseId?: number;
}

interface AppState {
  sources: Source[];
  briefs: Brief[];
  selectedSourceIds: number[];
  currentBriefs: Brief[];
  settings: UserSettings;
  customFilterPrompt: string;
  customSummaryPrompt: string;
  isGenerating: boolean;
  showPromptDialog: boolean;
  isLoadingSources: boolean;
  filteredUrls: FilteredUrl[];
  summaryCards: SummaryCard[];
  
  fetchSources: () => Promise<void>;
  addSource: (source: Omit<Source, 'id'>) => Promise<void>;
  updateSource: (id: number, updates: Partial<Omit<Source, 'id'>>) => Promise<void>;
  deleteSource: (id: number) => Promise<void>;
  loadDefaultSettings: () => Promise<void>;
  createDefaultPromptsIfNeeded: () => Promise<void>;
  updateSettings: (settings: Partial<UserSettings>) => void;
  toggleSourceSelection: (id: number) => void;
  setCustomFilterPrompt: (prompt: string) => void;
  setCustomSummaryPrompt: (prompt: string) => void;
  generateBriefs: () => Promise<void>;
  resetCustomPrompts: () => void;
  selectBrief: (briefId: string) => void;
  toggleFavorite: (briefId: string) => void;
  getFavorites: () => Brief[];
  setShowPromptDialog: (show: boolean) => void;
  updateBrief: (briefId: string, updates: Partial<Brief>) => void;
}

// Fallback default prompts when database is empty
const DEFAULT_FILTER_PROMPT = "您的任务是从提供的源文本中找到最相关和最有价值的内容URL链接。\n这些链接应该指向有深度、信息丰富且值得进一步阅读的文章或资源。\n请提取所有的URL链接，并根据内容的质量、相关性和信息价值对它们进行排名。\n对于每个URL，给出一个简短的标题和一个1-10的相关性评分。";
const DEFAULT_SUMMARY_PROMPT = "请对以下内容进行总结，生成一个有信息价值的摘要卡片。卡片应该包括：\n1. 一个简洁明了的标题\n2. 核心内容的精炼摘要（markdown格式）\n3. 2-3个关键点（用列表标记）\n4. 如果有，请包括最重要的结论或见解\n\n请确保摘要保留原始内容的核心价值，同时使信息更容易消化。";

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => {
      // Immediately create a store instance
      const store = {
        sources: [],
        briefs: [],
        selectedSourceIds: [],
        currentBriefs: [],
        settings: {
          filterPrompt: DEFAULT_FILTER_PROMPT,
          summaryPrompt: DEFAULT_SUMMARY_PROMPT
        },
        customFilterPrompt: "",
        customSummaryPrompt: "",
        isGenerating: false,
        showPromptDialog: false,
        isLoadingSources: false,
        filteredUrls: [],
        summaryCards: [],
        
        fetchSources: async () => {
          set({ isLoadingSources: true });
          try {
            const sources = await sourceService.getAllSources();
            set({ sources, isLoadingSources: false });
          } catch (error) {
            console.error("Error fetching sources:", error);
            set({ isLoadingSources: false });
          }
        },
        
        addSource: async (source) => {
          try {
            const newSource = await sourceService.createSource(source);
            set((state) => ({ 
              sources: [...state.sources, newSource] 
            }));
            return Promise.resolve();
          } catch (error) {
            console.error("Error adding source:", error);
            return Promise.reject(error);
          }
        },
        
        updateSource: async (id, updates) => {
          try {
            // Find the current source to get required fields
            const currentSource = get().sources.find(source => source.id === id);
            if (!currentSource) {
              throw new Error(`Source with id ${id} not found`);
            }
            
            // Merge current source with updates to ensure all required fields are present
            const sourceToUpdate: Source = {
              ...currentSource,
              ...updates,
              id // Make sure id is included
            };
            
            const updatedSource = await sourceService.updateSource(id, sourceToUpdate);
            set((state) => ({
              sources: state.sources.map(source => 
                source.id === id ? updatedSource : source
              )
            }));
            return Promise.resolve();
          } catch (error) {
            console.error("Error updating source:", error);
            return Promise.reject(error);
          }
        },
        
        deleteSource: async (id) => {
          try {
            await sourceService.deleteSource(id);
            set((state) => ({
              sources: state.sources.filter(source => source.id !== id),
              selectedSourceIds: state.selectedSourceIds.filter(sourceId => sourceId !== id)
            }));
            return Promise.resolve();
          } catch (error) {
            console.error("Error deleting source:", error);
            return Promise.reject(error);
          }
        },
        
        loadDefaultSettings: async () => {
          try {
            // Try to get default prompts
            const promptStore = usePromptStore.getState();
            
            // First check if any prompts exist
            const allPrompts = await promptService.getAllPrompts();
            
            // If no prompts exist at all, show the dialog
            if (allPrompts.length === 0) {
              set({ showPromptDialog: true });
              return;
            }
            
            // Try to get default filter and summary prompts
            try {
              const filterPrompt = await promptService.getDefaultPromptByType('filter');
              if (filterPrompt) {
                set(state => ({
                  settings: {
                    ...state.settings,
                    filterPrompt: filterPrompt.content
                  }
                }));
                console.log('Loaded default filter prompt:', filterPrompt.content);
              }
            } catch (error) {
              console.log('No default filter prompt found');
            }
            
            try {
              const summaryPrompt = await promptService.getDefaultPromptByType('summary');
              if (summaryPrompt) {
                set(state => ({
                  settings: {
                    ...state.settings,
                    summaryPrompt: summaryPrompt.content
                  }
                }));
                console.log('Loaded default summary prompt:', summaryPrompt.content);
              }
            } catch (error) {
              console.log('No default summary prompt found');
            }
          } catch (error) {
            console.error("Error loading prompts:", error);
            set({ showPromptDialog: true });
          }
        },
        
        createDefaultPromptsIfNeeded: async () => {
          // We're no longer automatically creating default prompts
          // Instead we'll show a dialog and let the user create them
          const allPrompts = await promptService.getAllPrompts().catch(() => []);
          if (allPrompts.length === 0) {
            set({ showPromptDialog: true });
          }
        },
        
        updateSettings: (newSettings) => set((state) => ({
          settings: { ...state.settings, ...newSettings }
        })),
        
        toggleSourceSelection: (id) => set((state) => {
          if (state.selectedSourceIds.includes(id)) {
            return { selectedSourceIds: state.selectedSourceIds.filter(sourceId => sourceId !== id) };
          } else {
            return { selectedSourceIds: [...state.selectedSourceIds, id] };
          }
        }),
        
        setCustomFilterPrompt: (prompt) => set({ customFilterPrompt: prompt }),
        
        setCustomSummaryPrompt: (prompt) => set({ customSummaryPrompt: prompt }),
        
        generateBriefs: async () => {
          const state = get();
          set({ isGenerating: true });
          
          try {
            const selectedSources = state.sources.filter(source => 
              source.id !== undefined && state.selectedSourceIds.includes(source.id)
            );
            
            // 使用customPrompt如果有提供，否则使用settings中的提示
            // 确保始终有值
            const filterPrompt = state.customFilterPrompt || state.settings.filterPrompt;
            const summaryPrompt = state.customSummaryPrompt || state.settings.summaryPrompt;
            
            console.log('生成简报使用的提示:', {
              filterPrompt,
              summaryPrompt
            });
            
            // 获取选中来源的URLs
            const sourceUrls = selectedSources.map(source => source.url || '').filter(url => url !== '');
            
            if (sourceUrls.length === 0) {
              console.error('没有有效的来源URL');
              set({ isGenerating: false });
              return;
            }
            
            // 生成每日阅读内容
            const dailyReadingResponse = await dailyReadingService.generateDailyReading(
              sourceUrls,
              filterPrompt,
              summaryPrompt
            );
            
            // 调试日志: 记录API响应结构
            console.log('API响应结构:', {
              success: dailyReadingResponse.success,
              timestamp: dailyReadingResponse.timestamp,
              filtered_urls_count: dailyReadingResponse.filtered_urls?.length || 0,
              summary_cards_count: dailyReadingResponse.summary_cards?.length || 0
            });
            
            console.log('第一个过滤URL样例:', dailyReadingResponse.filtered_urls?.[0]);
            console.log('第一个摘要卡片样例:', dailyReadingResponse.summary_cards?.[0]);
            
            // 检查响应结构是否按预期
            if (!dailyReadingResponse.filtered_urls || !Array.isArray(dailyReadingResponse.filtered_urls)) {
              console.error('API响应中filtered_urls结构不正确:', dailyReadingResponse.filtered_urls);
              set({ isGenerating: false });
              return;
            }
            
            if (!dailyReadingResponse.summary_cards || !Array.isArray(dailyReadingResponse.summary_cards)) {
              console.error('API响应中summary_cards结构不正确:', dailyReadingResponse.summary_cards);
              set({ isGenerating: false });
              return;
            }
            
            // 存储过滤的URLs和总结卡片
            set({
              filteredUrls: dailyReadingResponse.filtered_urls,
              summaryCards: dailyReadingResponse.summary_cards
            });
            
            // Create Brief objects from the summary cards
            try {
              const cardsAsBriefs = dailyReadingResponse.summary_cards.map(card => {
                console.log('处理摘要卡片:', card);
                
                if (!card.title || !card.conclusion) {
                  console.warn('摘要卡片缺少必要字段:', card);
                }
                
                // Add source URL to the content when it exists
                let content = card.conclusion || '';
                
                return {
                  id: `brief-card-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
                  sourceId: 'generated',
                  sourceName: card.title,
                  sourceUrl: card.source_url,
                  content: content,
                  createdAt: Date.now(),
                  isFavorite: false
                };
              });
              
              // Create Brief objects for the filtered URLs that don't have cards
              const urlsWithoutCards = dailyReadingResponse.filtered_urls.filter(
                url => !dailyReadingResponse.summary_cards.some(card => card.source_url === url.url)
              );
              
              console.log('未生成摘要卡片的URL数量:', urlsWithoutCards.length);
              
              const urlsAsBriefs = urlsWithoutCards.map(url => {
                console.log('处理过滤URL:', url);
                
                if (!url.url) {
                  console.warn('过滤URL缺少必要字段:', url);
                }
                
                return {
                  id: `brief-url-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
                  sourceId: 'url-only',
                  sourceName: url.title || url.url,
                  sourceUrl: url.url,
                  content: `Source URL: ${url.url}\n\nDescription: ${url.description || 'N/A'}\n\nScore: ${url.relevance_score || 'N/A'}`,
                  createdAt: Date.now(),
                  isFavorite: false
                };
              });
              
              const allGeneratedBriefs = [...cardsAsBriefs, ...urlsAsBriefs];
              console.log('生成的简报总数:', allGeneratedBriefs.length);
              
              // Update store with new briefs after everything is processed
              set({ 
                currentBriefs: allGeneratedBriefs,
                briefs: [...get().briefs, ...allGeneratedBriefs],
                isGenerating: false
              });
              
              console.log('状态更新完成. 当前简报数量:', allGeneratedBriefs.length);
            } catch (processError) {
              console.error('处理API响应数据时出错:', processError);
              set({ isGenerating: false });
            }
          } catch (error) {
            console.error("Error generating briefs:", error);
            set({ isGenerating: false });
          }
        },
        
        resetCustomPrompts: () => set({ 
          customFilterPrompt: "",
          customSummaryPrompt: ""
        }),
        
        selectBrief: (briefId) => {
          const state = get();
          const brief = state.briefs.find(b => b.id === briefId);
          if (brief) {
            set({
              currentBriefs: [
                ...state.currentBriefs.slice(0, 5),
                brief
              ].slice(0, 5)
            });
          }
        },
        
        toggleFavorite: (briefId: string) => set((state) => {
          console.log('Toggling favorite for brief:', briefId);
          
          // Find the brief to check if we're favoriting or unfavoriting
          const brief = state.briefs.find(b => b.id === briefId);
          if (!brief) {
            console.error('Brief not found:', briefId);
            return state; // No changes if brief not found
          }
          
          const isUnfavoriting = brief.isFavorite;
          
          // When unfavoriting, find all briefs with the same URL and update them too
          // This ensures consistency across the UI
          const briefsToUpdate = isUnfavoriting 
            ? state.briefs.filter(b => b.sourceUrl === brief.sourceUrl)
            : state.briefs.filter(b => b.id === briefId);
          
          const briefIds = briefsToUpdate.map(b => b.id);
          console.log(`${isUnfavoriting ? 'Unfavoriting' : 'Favoriting'} briefs:`, briefIds);
          
          // Update all briefs array
          const updatedBriefs = state.briefs.map(b => {
            if (briefIds.includes(b.id)) {
              // For unfavoriting, clear related fields
              if (isUnfavoriting) {
                return {
                  ...b,
                  isFavorite: false,
                  favoritedAt: undefined,
                  databaseId: undefined
                };
              } else {
                // For favoriting
                return {
                  ...b,
                  isFavorite: true,
                  favoritedAt: Date.now()
                };
              }
            }
            return b;
          });
          
          // Update currentBriefs array
          let updatedCurrentBriefs;
          if (isUnfavoriting && window.location.pathname === '/favorites') {
            // On favorites page, remove completely when unfavorited
            updatedCurrentBriefs = state.currentBriefs.filter(b => !briefIds.includes(b.id));
          } else {
            // Otherwise just update the status
            updatedCurrentBriefs = state.currentBriefs.map(b => {
              if (briefIds.includes(b.id)) {
                if (isUnfavoriting) {
                  return {
                    ...b,
                    isFavorite: false,
                    favoritedAt: undefined,
                    databaseId: undefined
                  };
                } else {
                  return {
                    ...b,
                    isFavorite: true,
                    favoritedAt: Date.now()
                  };
                }
              }
              return b;
            });
          }
          
          return {
            briefs: updatedBriefs,
            currentBriefs: updatedCurrentBriefs
          };
        }),
        
        setShowPromptDialog: (show) => set({ showPromptDialog: show }),
        
        getFavorites: () => {
          const state = get();
          return state.briefs.filter(brief => brief.isFavorite)
            .sort((a, b) => (b.favoritedAt || 0) - (a.favoritedAt || 0));
        },
        
        updateBrief: (briefId: string, updates: Partial<Brief>) => {
          console.log('更新Brief:', briefId, updates);
          set((state) => ({
            briefs: state.briefs.map(brief => 
              brief.id === briefId ? { ...brief, ...updates } : brief
            ),
            currentBriefs: state.currentBriefs.map(brief =>
              brief.id === briefId ? { ...brief, ...updates } : brief
            )
          }));
        }
      };
      
      return store;
    },
    {
      name: 'app-store',
      partialize: (state) => ({
        settings: state.settings
      })
    }
  )
);

export { default as useSourceStore } from './sourceStore';
export { default as usePromptStore } from './promptStore';
export { default as useReportStore } from './reportStore';
export { default as useCardStore } from './cardStore';