import React, { useRef, useState } from 'react';
import { X, Download } from 'lucide-react';
import html2canvas from 'html2canvas';
import { PosterData } from '../../services/dailyReadingService';

interface PosterModalProps {
  isOpen: boolean;
  onClose: () => void;
  posterData: PosterData;
}

const PosterModal: React.FC<PosterModalProps> = ({ isOpen, onClose, posterData }) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const posterRef = useRef<HTMLDivElement>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  if (!isOpen) return null;

  const handleDownload = async () => {
    if (!posterRef.current) return;
    
    setIsDownloading(true);
    try {
      let element: HTMLElement;
      let elementWidth: number;
      let elementHeight: number;

      // 判断是使用iframe还是fallback渲染
      if (posterData.poster_page && iframeRef.current) {
        // 尝试从iframe获取内容
        const iframeDoc = iframeRef.current.contentDocument || iframeRef.current.contentWindow?.document;
        if (iframeDoc && iframeDoc.body) {
          element = iframeDoc.body;
          // 获取实际内容尺寸，而不是固定尺寸
          elementWidth = Math.max(
            iframeDoc.body.scrollWidth,
            iframeDoc.body.offsetWidth,
            iframeDoc.documentElement.scrollWidth,
            iframeDoc.documentElement.offsetWidth
          );
          elementHeight = Math.max(
            iframeDoc.body.scrollHeight,
            iframeDoc.body.offsetHeight,
            iframeDoc.documentElement.scrollHeight,
            iframeDoc.documentElement.offsetHeight
          );
          
          console.log('Iframe content size:', { width: elementWidth, height: elementHeight });
        } else {
          // iframe访问失败，使用posterRef
          element = posterRef.current;
          elementWidth = Math.max(element.scrollWidth, element.offsetWidth);
          elementHeight = Math.max(element.scrollHeight, element.offsetHeight);
          console.log('Fallback to posterRef size:', { width: elementWidth, height: elementHeight });
        }
      } else {
        // 使用fallback poster
        element = posterRef.current;
        elementWidth = Math.max(element.scrollWidth, element.offsetWidth);
        elementHeight = Math.max(element.scrollHeight, element.offsetHeight);
        console.log('Fallback poster size:', { width: elementWidth, height: elementHeight });
      }
      
      // 确保最小尺寸
      elementWidth = Math.max(elementWidth, 800);
      elementHeight = Math.max(elementHeight, 1000);
      
      console.log('Final canvas size:', { width: elementWidth, height: elementHeight });
      
      // 动态计算canvas尺寸，确保完整捕获内容
      const canvas = await html2canvas(element, {
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff',
        scale: 2, // 提高图像质量
        width: elementWidth,
        height: elementHeight,
        scrollX: 0,
        scrollY: 0,
        // 不设置windowWidth和windowHeight，让html2canvas自动处理
      });
      
      // 创建下载链接
      const link = document.createElement('a');
      const cleanTitle = posterData.poster_content.title.replace(/[^\w\s\u4e00-\u9fff]/g, '').slice(0, 50);
      link.download = `${cleanTitle || 'poster'}_${Date.now()}.png`;
      link.href = canvas.toDataURL('image/png', 1.0);
      link.click();
      
      console.log('海报下载成功，尺寸:', canvas.width, 'x', canvas.height);
    } catch (error) {
      console.error('下载海报失败:', error);
      alert('下载失败，请稍后重试');
    } finally {
      setIsDownloading(false);
    }
  };

  const renderFallbackPoster = () => (
    <div 
      className="bg-gradient-to-br from-blue-50 to-indigo-100 p-8 font-sans"
      style={{
        width: '800px',
        minHeight: '1000px',
        maxWidth: '100%'
      }}
    >
      {/* Daily Reading Header */}
      <div className="text-center mb-8">
        <div className="bg-blue-600 text-white px-6 py-2 rounded-full inline-block text-lg font-bold mb-4">
          每日一读
        </div>
        <div className="w-20 h-1 bg-blue-600 mx-auto"></div>
      </div>

      {/* Title and Authors */}
      <div className="text-center mb-10">
        <h1 className="text-2xl font-bold text-blue-900 mb-3 leading-tight">
          {posterData.poster_content.title}
        </h1>
        {posterData.poster_content.authors && (
          <p className="text-base text-blue-700 font-medium mb-2">
            作者：{posterData.poster_content.authors}
          </p>
        )}
        {posterData.poster_content.subtitle && (
          <p className="text-lg text-blue-700 font-medium">
            {posterData.poster_content.subtitle}
          </p>
        )}
      </div>

      {/* Summary */}
      <div className="mb-8">
        <div className="bg-white rounded-lg p-5 shadow-md border-l-4 border-blue-500">
          <h2 className="text-lg font-semibold text-blue-900 mb-3">内容概述</h2>
          <p className="text-gray-700 leading-relaxed text-sm">
            {posterData.poster_content.summary}
          </p>
        </div>
      </div>

      {/* Content based on type */}
      {posterData.poster_content.content_type === '论文' ? (
        // 论文内容结构
        <div className="space-y-6 mb-8">
          {/* Research Background */}
          {posterData.poster_content.main_content.background && (
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="text-base font-semibold text-blue-900 mb-2">研究背景</h3>
              <p className="text-blue-800 text-sm">{posterData.poster_content.main_content.background}</p>
            </div>
          )}
          
          {/* Methodology */}
          {posterData.poster_content.main_content.methodology && (
            <div className="bg-white rounded-lg p-4 border border-blue-200">
              <h3 className="text-base font-semibold text-blue-900 mb-2">研究方法</h3>
              <p className="text-gray-700 text-sm">{posterData.poster_content.main_content.methodology}</p>
            </div>
          )}
          
          {/* Key Findings */}
          {posterData.poster_content.main_content.key_findings && posterData.poster_content.main_content.key_findings.length > 0 && (
            <div>
              <h3 className="text-base font-semibold text-blue-900 mb-3">关键发现</h3>
              <div className="space-y-2">
                {posterData.poster_content.main_content.key_findings.map((finding, index) => (
                  <div key={index} className="flex items-start">
                    <div className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5">
                      {index + 1}
                    </div>
                    <p className="text-gray-700 flex-1 text-sm">{finding}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Results */}
          {posterData.poster_content.main_content.results && (
            <div className="bg-green-50 rounded-lg p-4">
              <h3 className="text-base font-semibold text-green-900 mb-2">主要结果</h3>
              <p className="text-green-800 text-sm">{posterData.poster_content.main_content.results}</p>
            </div>
          )}
          
          {/* Significance */}
          {posterData.poster_content.main_content.significance && (
            <div className="bg-indigo-50 rounded-lg p-4">
              <h3 className="text-base font-semibold text-indigo-900 mb-2">研究意义</h3>
              <p className="text-indigo-800 text-sm">{posterData.poster_content.main_content.significance}</p>
            </div>
          )}
        </div>
      ) : (
        // 新闻或其他内容结构
        <div className="space-y-6 mb-8">
          {/* Key Points */}
          {posterData.poster_content.main_content.key_points && posterData.poster_content.main_content.key_points.length > 0 && (
            <div>
              <h3 className="text-base font-semibold text-blue-900 mb-3">核心要点</h3>
              <div className="space-y-2">
                {posterData.poster_content.main_content.key_points.map((point, index) => (
                  <div key={index} className="flex items-start">
                    <div className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5">
                      {index + 1}
                    </div>
                    <p className="text-gray-700 flex-1 text-sm">{point}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Background */}
          {posterData.poster_content.main_content.background && (
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="text-base font-semibold text-blue-900 mb-2">背景信息</h3>
              <p className="text-blue-800 text-sm">{posterData.poster_content.main_content.background}</p>
            </div>
          )}
          
          {/* Impact */}
          {posterData.poster_content.main_content.impact && (
            <div className="bg-green-50 rounded-lg p-4">
              <h3 className="text-base font-semibold text-green-900 mb-2">影响和意义</h3>
              <p className="text-green-800 text-sm">{posterData.poster_content.main_content.impact}</p>
            </div>
          )}
          
          {/* Details */}
          {posterData.poster_content.main_content.details && (
            <div className="bg-white rounded-lg p-4 border border-blue-200">
              <h3 className="text-base font-semibold text-blue-900 mb-2">重要细节</h3>
              <p className="text-gray-700 text-sm">{posterData.poster_content.main_content.details}</p>
            </div>
          )}
        </div>
      )}

      {/* Featured Quote */}
      {posterData.poster_content.featured_quote && (
        <div className="mb-8">
          <div className="bg-white rounded-lg p-4 border-l-4 border-blue-300">
            <blockquote className="text-blue-800 italic text-center text-sm">
              "{posterData.poster_content.featured_quote}"
            </blockquote>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-center text-blue-600 text-xs">
        <div className="border-t border-blue-300 pt-4">
          <p className="font-medium">{posterData.poster_content.paper_info.field}</p>
          <p className="text-gray-600">{posterData.poster_content.paper_info.source}</p>
          <p className="mt-2 text-blue-500">© 2025 Medbench | 社区驿站</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-[90vw] max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b flex-shrink-0">
          <h3 className="text-lg font-semibold text-gray-900">论文海报</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className="px-3 py-1.5 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center text-sm"
            >
              <Download className="w-4 h-4 mr-1" />
              {isDownloading ? '下载中...' : '下载'}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-gray-600 rounded-md"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Poster Content */}
        <div className="flex-1 min-h-0 overflow-auto">
          <div 
            ref={posterRef}
            className="p-4 flex justify-center items-start"
          >
            {posterData.poster_page ? (
              <iframe
                srcDoc={posterData.poster_page}
                className="border-0 shadow-lg max-w-full"
                style={{ 
                  width: '800px',
                  height: '1000px',
                  transform: 'scale(1)',
                  transformOrigin: 'top center'
                }}
                title="Generated Poster"
                onLoad={(e) => {
                  const iframe = e.target as HTMLIFrameElement;
                  const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
                  if (iframeDoc && iframeDoc.body) {
                    // 获取实际内容尺寸
                    const contentWidth = Math.max(
                      iframeDoc.body.scrollWidth,
                      iframeDoc.body.offsetWidth,
                      iframeDoc.documentElement.scrollWidth,
                      iframeDoc.documentElement.offsetWidth
                    );
                    const contentHeight = Math.max(
                      iframeDoc.body.scrollHeight,
                      iframeDoc.body.offsetHeight,
                      iframeDoc.documentElement.scrollHeight,
                      iframeDoc.documentElement.offsetHeight
                    );
                    
                    // 为了预览，保持iframe固定尺寸，但确保内容不会有滚动条
                    // 通过设置iframe文档的样式来避免内部滚动条
                    if (iframeDoc.documentElement) {
                      iframeDoc.documentElement.style.overflow = 'hidden';
                    }
                    if (iframeDoc.body) {
                      iframeDoc.body.style.overflow = 'hidden';
                      iframeDoc.body.style.margin = '0';
                      iframeDoc.body.style.padding = '0';
                    }
                    
                    // 计算缩放比例以适应预览窗口
                    const containerWidth = 800;
                    const containerHeight = 1000;
                    const scaleX = containerWidth / contentWidth;
                    const scaleY = containerHeight / contentHeight;
                    const scale = Math.min(scaleX, scaleY, 1); // 不放大，只缩小
                    
                    if (scale < 1) {
                      // 需要缩放时，调整iframe尺寸和缩放
                      iframe.style.width = `${contentWidth}px`;
                      iframe.style.height = `${contentHeight}px`;
                      iframe.style.transform = `scale(${scale})`;
                      iframe.style.transformOrigin = 'top center';
                    } else {
                      // 不需要缩放时，使用实际尺寸
                      iframe.style.width = `${contentWidth}px`;
                      iframe.style.height = `${contentHeight}px`;
                      iframe.style.transform = 'scale(1)';
                    }
                    
                    console.log('Iframe preview adjusted:', { 
                      contentWidth, 
                      contentHeight, 
                      scale: scale < 1 ? scale : 1 
                    });
                  }
                }}
                ref={iframeRef}
              />
            ) : (
              <div className="max-w-full overflow-hidden">
                {renderFallbackPoster()}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PosterModal; 