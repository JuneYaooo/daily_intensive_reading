import api from './api';

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

interface ApiErrorDetail {
  phase: string;
  message: string;
  details?: unknown;
}

export interface GenerateDailyReadingResponse {
  success: boolean;
  timestamp: string;
  filtered_urls: FilteredUrl[];
  summary_cards: SummaryCard[];
  errors?: ApiErrorDetail[];
}

export interface GenerateOneCardResponse {
  success: boolean;
  card: SummaryCard;
  errors?: ApiErrorDetail[];
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
  errors?: ApiErrorDetail[];
}

export interface ApiConfigOverride {
  jigsawstackKeys?: string;
  modelBaseUrl?: string;
  modelName?: string;
  modelApiKey?: string;
}

function buildOverridePayload(config?: ApiConfigOverride): Record<string, string> {
  if (!config) return {};
  const payload: Record<string, string> = {};
  if (config.jigsawstackKeys) payload.jigsawstack_keys = config.jigsawstackKeys;
  if (config.modelBaseUrl) payload.model_base_url = config.modelBaseUrl;
  if (config.modelName) payload.model_name = config.modelName;
  if (config.modelApiKey) payload.model_api_key = config.modelApiKey;
  return payload;
}

const dailyReadingService = {
  /**
   * Generate daily reading content
   * Uses global api instance
   */
  async generateDailyReading(
    sourceUrls: string[],
    filterPrompt?: string,
    summaryPrompt?: string,
    numResults?: number,
    apiConfig?: ApiConfigOverride
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
        filter_prompt: filterPrompt || '',
        summary_prompt: summaryPrompt || '',
        num_results: numResults || 10,
        ...buildOverridePayload(apiConfig)
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
    summaryPrompt: string,
    apiConfig?: ApiConfigOverride
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
        summary_prompt: summaryPrompt || '',
        ...buildOverridePayload(apiConfig)
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
    subtitle?: string,
    apiConfig?: ApiConfigOverride
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
        subtitle: subtitle,
        ...buildOverridePayload(apiConfig)
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
