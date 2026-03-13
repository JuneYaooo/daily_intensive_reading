import React, { useState, useEffect } from 'react';
import { Copy, Check, ExternalLink, Heart, Globe, FileText, Loader, Image } from 'lucide-react';
import { Brief } from '../../types';
import { useAppStore } from '../../store';
import ReactMarkdown from 'react-markdown';
import dailyReadingService, { GeneratePosterResponse } from '../../services/dailyReadingService';
import cardService from '../../services/cardService';
import PosterModal from './PosterModal';

interface BriefCardProps {
  brief: Brief;
  showFavoritedAt?: boolean;
}

const BriefCard: React.FC<BriefCardProps> = ({ brief, showFavoritedAt = false }) => {
  const [copied, setCopied] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isTogglingFavorite, setIsTogglingFavorite] = useState(false);
  const [isGeneratingPoster, setIsGeneratingPoster] = useState(false);
  const [posterData, setPosterData] = useState<GeneratePosterResponse | null>(null);
  const [showPosterModal, setShowPosterModal] = useState(false);
  const { toggleFavorite } = useAppStore();
  
  useEffect(() => {
    // 调试日志：在组件渲染时打印brief对象
    console.log('渲染BriefCard组件，brief对象:', {
      id: brief.id,
      sourceName: brief.sourceName,
      sourceUrl: brief.sourceUrl,
      contentLength: brief.content?.length || 0,
      hasContent: !!brief.content,
      createdAt: brief.createdAt,
      isFavorite: brief.isFavorite
    });
    
    if (!brief.content) {
      console.warn('Brief对象缺少content字段:', brief);
    }
  }, [brief]);
  
  // Check if this is a URL-only brief (non-card content)
  const isUrlOnly = brief.sourceId === 'url-only';
  
  const handleCopy = () => {
    if (brief.content) {
      // Create a combined content with URL appended
      let contentToCopy = brief.content;
      
      // Add source URL if it exists
      if (brief.sourceUrl) {
        contentToCopy += `\n论文链接：${brief.sourceUrl}`;
      }
      
      // Create a temporary textarea element
      const textarea = document.createElement('textarea');
      textarea.value = contentToCopy;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'absolute';
      textarea.style.left = '-9999px';
      document.body.appendChild(textarea);
      
      // Select and copy the text
      textarea.select();
      try {
        const successful = document.execCommand('copy');
        if (successful) {
          console.log('Content copied to clipboard');
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        } else {
          console.error('Failed to copy text');
        }
      } catch (err) {
        console.error('Error copying text: ', err);
      }
      
      // Clean up
      document.body.removeChild(textarea);
    }
  };
  
  const handleToggleFavorite = async () => {
    try {
      setIsTogglingFavorite(true);
      console.log('Toggling favorite state for brief:', brief.id);
      
      // Get the current isFavorite state before toggling
      const currentIsFavorite = brief.isFavorite;
      
      // Important: Update local state first for immediate UI feedback
      toggleFavorite(brief.id);
      
      // Sync with backend
      try {
        if (!currentIsFavorite) {
          // Just toggled to favorite - create a new card in the backend
          const newCard = await cardService.createCard({
            title: brief.sourceName,
            source_url: brief.sourceUrl,
            conclusion: brief.content,
            author: brief.author || '',
            key_points: brief.keyPoints || [],
            quotes: brief.quotes || []
          });
          
          if (newCard && newCard.id) {
            // Save the database ID for future reference
            const appStore = useAppStore.getState();
            appStore.updateBrief(brief.id, { 
              databaseId: newCard.id,
              isFavorite: true
            });
            
            console.log('Card created in database - Favorited with ID:', newCard.id);
          }
        } else {
          // Just toggled to unfavorite - delete the card from the backend
          if (brief.databaseId) {
            await cardService.deleteCard(brief.databaseId);
            
            // Force update on all briefs to ensure everything is in sync
            const appStore = useAppStore.getState();
            appStore.updateBrief(brief.id, { 
              isFavorite: false,
              databaseId: undefined,
              favoritedAt: undefined
            });
            
            // Also force refresh for any current briefs with the same URL
            const allBriefs = appStore.briefs;
            const sameUrlBriefs = allBriefs.filter(b => 
              b.sourceUrl === brief.sourceUrl && b.id !== brief.id
            );
            
            // Update all briefs with the same URL
            for (const similarBrief of sameUrlBriefs) {
              appStore.updateBrief(similarBrief.id, {
                isFavorite: false,
                databaseId: undefined,
                favoritedAt: undefined
              });
            }
            
            console.log('Card deleted from database - Unfavorited');
          } else {
            console.log('No database ID available, only removed from local favorites');
          }
        }
      } catch (apiError) {
        console.error('Error syncing with backend API:', apiError);
        console.log('Continuing with local state only');
        // In case of API error, revert the local state change
        toggleFavorite(brief.id);
      }
    } catch (error) {
      console.error('Error in handleToggleFavorite:', error);
      // Revert the local state change on critical error
      toggleFavorite(brief.id);
    } finally {
      setIsTogglingFavorite(false);
    }
  };
  
  // 生成卡片摘要的处理函数
  const handleGenerateCard = async () => {
    if (!brief.sourceUrl) return;
    
    setIsGenerating(true);
    try {
      console.log('正在为URL生成卡片:', brief.sourceUrl);
      
      // 获取当前应用状态中的摘要提示词
      const appStore = useAppStore.getState();
      const summaryPrompt = appStore.customSummaryPrompt || appStore.settings.summaryPrompt;
      
      // 调用新的API生成单个卡片
      const result = await dailyReadingService.generateOneCard(
        brief.sourceUrl,
        brief.sourceName || '', 
        summaryPrompt
      );
      
      console.log('单卡生成结果:', result);
      
      if (result.success && result.card) {
        // 生成成功，更新当前brief对象
        const summaryCard = result.card;
        
        // 获取应用状态更新函数
        const appStore = useAppStore.getState();
        
        // 创建新的卡片brief
        const newBrief: Brief = {
          ...brief,
          sourceId: 'generated', // 更改为生成的卡片类型
          sourceName: summaryCard.title || brief.sourceName,
          content: summaryCard.conclusion || '',
          keyPoints: summaryCard.key_points || [],
          quotes: summaryCard.quotes || []
        };
        
        // 更新store中的brief
        appStore.updateBrief(brief.id, newBrief);
        
        console.log('卡片生成成功，已更新:', newBrief);
      } else {
        console.error('卡片生成失败或没有返回结果');
        alert('摘要生成失败，请稍后重试');
      }
    } catch (error) {
      console.error('生成卡片时出错:', error);
      alert('摘要生成失败，请稍后重试');
    } finally {
      setIsGenerating(false);
    }
  };
  
  // 生成海报的处理函数
  const handleGeneratePoster = async () => {
    if (!brief.content || brief.sourceId === 'url-only' || !brief.sourceUrl) {
      console.warn('只有生成的摘要卡片且有URL才能生成海报');
      return;
    }
    
    setIsGeneratingPoster(true);
    try {
      console.log('开始为论文生成海报:', brief.sourceName, 'URL:', brief.sourceUrl);
      
      const response = await dailyReadingService.generatePoster(
        brief.sourceUrl,
        brief.sourceName,
        undefined // subtitle
      );
      setPosterData(response);
      
      if (response.success) {
        console.log('论文海报生成成功:', response.poster?.poster_content.title);
        setShowPosterModal(true);
      } else {
        console.error('论文海报生成失败:', response.errors);
        // Show error message to user
        alert(`海报生成失败: ${response.errors?.[0]?.message || '未知错误'}`);
      }
    } catch (error) {
      console.error('生成海报时出错:', error);
      alert('生成海报时出错，请稍后重试');
    } finally {
      setIsGeneratingPoster(false);
    }
  };
  
  // 处理海报按钮点击
  const handlePosterClick = () => {
    if (posterData?.success && posterData.poster) {
      setShowPosterModal(true);
    } else {
      handleGeneratePoster();
    }
  };
  
  // 渲染Markdown内容
  const renderMarkdown = (content: string) => {
    try {
      if (!content || content.trim() === '') {
        console.log('内容为空');
        return <div className="text-gray-500">暂无内容</div>;
      }
      
      let displayContent = content;
      
      // Don't add URL to displayed content - we'll only add it when copying
      console.log('渲染内容:', displayContent.substring(0, 50) + '...');
      return (
        <>
          <ReactMarkdown>{displayContent}</ReactMarkdown>
          {brief.sourceUrl && (
            <div className="mt-4 text-sm text-gray-500">
              论文链接：<a href={brief.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">{brief.sourceUrl}</a>
            </div>
          )}
        </>
      );
    } catch (error) {
      console.error('渲染Markdown出错:', error);
      return <div className="text-red-500">内容格式错误，无法显示</div>;
    }
  };
  
  return (
    <div className={`bg-white rounded-lg overflow-hidden ${isUrlOnly ? 'border border-gray-200' : 'shadow-lg'}`}>
      <div className={`px-4 py-3 border-b border-gray-200 ${isUrlOnly ? 'bg-gray-50' : 'bg-[#F8F8F8]'}`}>
        <div className="flex justify-between items-start">
          <div className="flex items-center space-x-2">
            {isUrlOnly ? (
              <Globe className="w-5 h-5 text-gray-500" />
            ) : (
              <div className="w-2 h-5 bg-[#0A84FF] rounded"></div>
            )}
            <h3 className="font-medium text-[#1C1C1E] line-clamp-1">{brief.sourceName}</h3>
          </div>
          
          <div className="flex items-center space-x-2">
            {!isUrlOnly && (
              <button
                onClick={handleToggleFavorite}
                disabled={isTogglingFavorite}
                className={`p-1.5 rounded-full transition-colors ${
                  brief.isFavorite
                    ? 'text-[#FF3B30] hover:bg-[#FFF1F0]'
                    : 'text-gray-400 hover:bg-gray-100'
                }`}
              >
                <Heart
                  className={`w-4 h-4 ${isTogglingFavorite ? 'opacity-50' : ''}`}
                  fill={brief.isFavorite ? "#FF3B30" : "none"}
                />
              </button>
            )}
            
            {!isUrlOnly && brief.content && (
              <button
                onClick={handlePosterClick}
                disabled={isGeneratingPoster}
                className={`p-1.5 rounded-full transition-colors ${
                  isGeneratingPoster 
                    ? 'text-gray-300 cursor-not-allowed' 
                    : 'text-gray-400 hover:bg-gray-100'
                }`}
                title="生成论文海报"
              >
                {isGeneratingPoster ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <Image className="w-4 h-4" />
                )}
              </button>
            )}
            
            {!isUrlOnly && (
              <button
                onClick={handleCopy}
                className="p-1.5 text-gray-400 hover:bg-gray-100 rounded-full transition-colors"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-green-500" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            )}
            
            {brief.sourceUrl && (
              <a
                href={brief.sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1.5 text-gray-400 hover:bg-gray-100 rounded-full transition-colors"
                title="访问原文"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        </div>
        
        {showFavoritedAt && brief.favoritedAt && (
          <div className="text-xs text-gray-500 mt-1">
            收藏于 {new Date(brief.favoritedAt).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}
          </div>
        )}
      </div>
      
      {isUrlOnly ? (
        <div className="p-4">
          <div className="flex items-center text-sm text-gray-500 mb-3">
            <Globe className="w-4 h-4 mr-2 flex-shrink-0" />
            <a 
              href={brief.sourceUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline truncate"
            >
              {brief.sourceUrl}
            </a>
          </div>
          
          <button
            onClick={handleGenerateCard}
            disabled={isGenerating}
            className={`w-full py-2 px-4 rounded flex items-center justify-center transition-colors ${
              isGenerating 
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
            }`}
          >
            {isGenerating ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                <span>生成摘要中...</span>
              </>
            ) : (
              <>
                <FileText className="w-4 h-4 mr-2" />
                <span>生成内容摘要</span>
              </>
            )}
          </button>
        </div>
      ) : (
        <div className="p-4">
          <div className="prose prose-sm max-w-none markdown-content">
            {brief.content ? (
              renderMarkdown(brief.content)
            ) : (
              <div className="text-gray-500">暂无内容摘要</div>
            )}
          </div>
        </div>
      )}
      
      {/* 海报弹窗 */}
      {posterData?.success && posterData.poster && (
        <PosterModal
          isOpen={showPosterModal}
          onClose={() => setShowPosterModal(false)}
          posterData={posterData.poster}
        />
      )}
    </div>
  );
};

export default BriefCard;