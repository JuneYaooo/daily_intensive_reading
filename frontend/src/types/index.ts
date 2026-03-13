// Source interfaces
export interface Source {
  id?: number;
  name: string;
  url?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

// Prompt interfaces
export interface Prompt {
  id?: number;
  name: string;
  content: string;
  description?: string;
  type?: 'filter' | 'summary' | 'general';
  is_default?: boolean;
  created_at?: string;
  updated_at?: string;
}

// Tag interfaces
export interface Tag {
  id?: number;
  name: string;
  created_at?: string;
}

// Reading Card interfaces
export interface ReadingCard {
  id?: number;
  title: string;
  source_url?: string;
  conclusion?: string;
  key_points?: string[];
  quotes?: string[];
  author?: string;
  created_at?: string;
  updated_at?: string;
  is_favorite?: boolean;
  favorite_id?: number;
}

// User Interaction interfaces
export interface UserInteraction {
  id?: number;
  user_id: number;
  card_id: number;
  interaction_type: 'read' | 'favorite' | 'comment';
  comment?: string;
  created_at?: string;
}

// Report Generation interfaces
export interface ReportGenerationRequest {
  content: string;
  source_id?: number;
  prompt_id?: number;
  prompt_content?: string;
  prompt_type?: 'filter' | 'summary' | 'general';
}

export interface ReportGenerationResponse {
  report: string;
  source?: string;
  prompt: string;
}

// Card Generation interfaces
export interface CardGenerationRequest {
  selected_content: string;
  prompt_id?: number;
  title?: string;
  author?: string;
  source?: string;
  tags?: string[];
}

// API Response interfaces
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export interface ApiError {
  message: string;
  errors?: Record<string, string[]>;
  status: number;
}

export interface Brief {
  id: string;
  sourceId: string;
  sourceName: string;
  sourceUrl: string;
  content: string;
  createdAt: number;
  isFavorite?: boolean;
  favoritedAt?: number;
  author?: string;
  keyPoints?: string[];
  quotes?: string[];
  databaseId?: number;
}

export interface UserSettings {
  filterPrompt: string;
  summaryPrompt: string;
}

// Daily Reading interfaces
export interface SummaryCard {
  title: string;
  content: string;
  source_url: string;
  keywords?: string[];
  key_points?: string[];
}

export interface FilteredUrl {
  url: string;
  title?: string;
  score?: number;
}

export interface DailyReadingResponse {
  success: boolean;
  timestamp: string;
  filtered_urls: FilteredUrl[];
  summary_cards: SummaryCard[];
}