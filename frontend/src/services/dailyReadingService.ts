import api from './api';
import { ReadingCard } from '../types';
import axios from 'axios';

// 确保BASE_URL与API配置一致
const BASE_URL = '/api/daily-reading';

export interface SummaryCard {
  title: string;
  conclusion: string;
  source_url: string;
  key_points?: string[];
  quotes?: string[];
}

export interface FilteredUrl {
  url: string;
  title?: string;
  description?: string;
  relevance_score?: number;
}

export interface GenerateDailyReadingResponse {
  success: boolean;
  timestamp: string;
  filtered_urls: FilteredUrl[];
  summary_cards: SummaryCard[];
}

export interface GenerateOneCardResponse {
  success: boolean;
  card: SummaryCard;
}

export interface PosterTheme {
  primary_color: string;
  accent_color: string;
  background: string;
  style: string;
}

export interface PosterContent {
  content_type: '论文' | '新闻' | '其他';
  title: string;
  authors?: string;
  subtitle: string;
  summary: string;
  main_content: {
    // 论文类型字段
    background?: string;
    methodology?: string;
    key_findings?: string[];
    results?: string;
    significance?: string;
    // 新闻类型字段
    key_points?: string[];
    impact?: string;
    details?: string;
  };
  featured_quote: string;
  paper_info: {
    source: string;
    field: string;
    footer?: string;
  };
}

export interface PosterData {
  success: boolean;
  poster_content: PosterContent;
  poster_page: string | null; // HTML content or null
  original_card: SummaryCard;
  generated_at: string;
}

export interface GeneratePosterResponse {
  success: boolean;
  poster?: PosterData;
  errors?: Array<{
    phase: string;
    message: string;
    details?: any;
  }>;
}

const dailyReadingService = {
  /**
   * Get today's reading
   */
  async getTodayReading(): Promise<ReadingCard> {
    const response = await api.get(`${BASE_URL}/today`);
    return response.data;
  },
  
  /**
   * Get reading history
   */
  async getReadingHistory(userId: number): Promise<ReadingCard[]> {
    const response = await api.get(`${BASE_URL}/history/${userId}`);
    return response.data;
  },
  
  /**
   * Mark reading as completed
   */
  async markAsCompleted(cardId: number, userId: number): Promise<void> {
    await api.post(`${BASE_URL}/complete`, { card_id: cardId, user_id: userId });
  },

  /**
   * Generate daily reading content
   * Uses global api instance
   */
  async generateDailyReading(
    sourceUrls: string[],
    filterPrompt?: string,
    summaryPrompt?: string,
    numResults?: number
  ): Promise<GenerateDailyReadingResponse> {
    console.log('Generating daily reading with params:', {
      source_urls: sourceUrls,
      filter_prompt: filterPrompt,
      summary_prompt: summaryPrompt,
      num_results: numResults
    });

    // Always send both prompts, even if they're empty strings
    // This ensures they're always in the payload
    try {
      console.log('发送API请求...');
      const response = await api.post(`${BASE_URL}/generate`, {
        source_urls: sourceUrls,
        filter_prompt: filterPrompt || '',  // 确保不会传undefined
        summary_prompt: summaryPrompt || '', // 确保不会传undefined
        num_results: numResults || 10
      });
      
      console.log('API请求成功. 响应状态:', response.status);
      console.log('响应数据结构:', {
        success: response.data.success,
        timestamp: response.data.timestamp,
        filtered_urls_length: response.data.filtered_urls?.length,
        summary_cards_length: response.data.summary_cards?.length,
      });
      
      // 检查响应数据中必需的字段
      if (!response.data.filtered_urls || !Array.isArray(response.data.filtered_urls)) {
        console.error('响应中filtered_urls字段缺失或格式不正确');
      }
      
      if (!response.data.summary_cards || !Array.isArray(response.data.summary_cards)) {
        console.error('响应中summary_cards字段缺失或格式不正确');
      }
      
      // 检查第一个summary_card的结构
      if (response.data.summary_cards && response.data.summary_cards.length > 0) {
        const firstCard = response.data.summary_cards[0];
        console.log('第一个summary_card字段:', Object.keys(firstCard));
        console.log('第一个summary_card是否有title:', !!firstCard.title);
        console.log('第一个summary_card是否有conclusion:', !!firstCard.conclusion);
        console.log('第一个summary_card是否有source_url:', !!firstCard.source_url);
      }
      
      return response.data;
    } catch (error) {
      console.error('生成每日阅读内容API请求失败:', error);
      throw error;
    }
  },
  
  /**
   * Generate a single card from a URL
   * Uses global api instance
   */
  async generateOneCard(
    url: string,
    title: string,
    summaryPrompt: string
  ): Promise<GenerateOneCardResponse> {
    console.log('Generating single card with params:', {
      url,
      title,
      summary_prompt: summaryPrompt
    });

    try {
      console.log('发送生成单个卡片API请求...');
      const response = await api.post(`${BASE_URL}/generate-one-card`, {
        url,
        title,
        summary_prompt: summaryPrompt || ''  // 确保不会传undefined
      });
      
      console.log('单卡生成API请求成功. 响应状态:', response.status);
      console.log('响应数据:', {
        success: response.data.success,
        cardData: response.data.card,
      });
      
      // 检查响应数据中必需的字段
      if (!response.data.card) {
        console.error('响应中card字段缺失或格式不正确');
      }
      
      return response.data;
    } catch (error) {
      console.error('生成单个卡片API请求失败:', error);
      throw error;
    }
  },

  /**
   * Generate poster content from URL (uses cached original content)
   * Uses global api instance
   */
  async generatePoster(
    url: string,
    title?: string,
    subtitle?: string
  ): Promise<GeneratePosterResponse> {
    console.log('Generating poster for URL:', {
      url,
      title,
      subtitle
    });

    try {
      console.log('发送生成论文海报API请求...');
      const response = await api.post(`${BASE_URL}/generate-poster`, {
        url: url,
        title: title,
        subtitle: subtitle
      });
      
      console.log('论文海报生成API请求成功. 响应状态:', response.status);
      console.log('响应数据:', {
        success: response.data.success,
        poster_title: response.data.poster?.poster_content.title,
        errors_count: response.data.errors?.length || 0
      });
      
      // 检查响应数据中必需的字段
      if (!response.data.poster && response.data.success) {
        console.error('响应中poster字段缺失但success为true');
      }
      
      return response.data;
    } catch (error) {
      console.error('生成论文海报API请求失败:', error);
      throw error;
    }
  }
};

export default dailyReadingService; 