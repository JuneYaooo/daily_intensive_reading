import os
import json
import traceback
import psutil
import time
import signal
import threading
import uuid
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from ..utils.json_utils import JsonUtils
from ..utils.logger import BeijingLogger

# Initialize logger
logger = BeijingLogger().get_logger()

# Load environment variables
load_dotenv()

# Initialize DeepSeek configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")

# Maximum tokens allowed by DeepSeek model
MAX_CONTEXT_TOKENS = 65536
# Reserve tokens for prompt and completion
TOKENS_RESERVE = 4000

# API request timeout in seconds
DEFAULT_API_TIMEOUT = 1200

# Directory for saving response logs
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs", "responses")
os.makedirs(LOG_DIR, exist_ok=True)

def save_response_to_file(response_text, operation_type):
    """Save the complete response to a file for debugging"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{operation_type}_{unique_id}.json"
        filepath = os.path.join(LOG_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response_text)
            
        logger.info(f"完整响应已保存至: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"保存响应内容到文件时出错: {str(e)}")
        return None

# Circuit breaker for DeepSeek API
class CircuitBreaker:
    def __init__(self, name, failure_threshold=5, reset_timeout=300):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.open_since = None
        self.lock = threading.Lock()
        
    def is_open(self):
        """Check if circuit breaker is open (API should not be called)"""
        with self.lock:
            if self.open_since is not None:
                # Check if reset timeout has elapsed
                if time.time() - self.open_since > self.reset_timeout:
                    logger.info(f"Circuit breaker {self.name}: 重置断路器状态")
                    self.reset()
                    return False
                return True
            return False
            
    def record_failure(self):
        """Record an API failure"""
        with self.lock:
            if self.open_since is None:  # Only count failures if circuit is closed
                self.failures += 1
                logger.warning(f"Circuit breaker {self.name}: 记录失败 {self.failures}/{self.failure_threshold}")
                if self.failures >= self.failure_threshold:
                    logger.error(f"Circuit breaker {self.name}: 已打开断路器，暂停API调用 {self.reset_timeout} 秒")
                    self.open_since = time.time()
    
    def record_success(self):
        """Record a successful API call"""
        with self.lock:
            if self.open_since is None and self.failures > 0:  # Only reset counter on success if circuit is closed
                self.failures = 0
                
    def reset(self):
        """Reset the circuit breaker"""
        with self.lock:
            self.failures = 0
            self.open_since = None

# Create circuit breaker for DeepSeek API
deepseek_circuit = CircuitBreaker("DeepSeek")

class APITimeout(Exception):
    """Exception raised when an API call times out"""
    pass

def estimate_tokens(text):
    """
    Estimate the number of tokens in a text based on DeepSeek's token calculation guidelines.
    
    Args:
        text (str): The text to estimate tokens for
        
    Returns:
        int: Estimated token count
    """
    if text is None:
        logger.warning("Token estimation received None text")
        return 0
        
    # Count English characters (including numbers and punctuation)
    english_chars = sum(1 for char in text if ord(char) < 128)
    
    # Count Chinese characters (and other non-ASCII)
    chinese_chars = len(text) - english_chars
    
    # Apply the conversion ratio
    estimated_tokens = int(english_chars * 0.3 + chinese_chars * 0.6)
    
    # Add a safety margin (20%)
    final_token_estimate = int(estimated_tokens * 1.2)
    
    logger.debug(f"Token estimate: {final_token_estimate} (text length: {len(text)}, English: {english_chars}, Chinese: {chinese_chars})")
    return final_token_estimate

def truncate_content(text, max_tokens=MAX_CONTEXT_TOKENS-TOKENS_RESERVE, reduction_ratio=0.1):
    """
    Truncate content to stay within token limits.
    
    Args:
        text (str): The text to truncate
        max_tokens (int): Maximum tokens allowed
        reduction_ratio (float): How much to reduce by if already truncated
        
    Returns:
        str: Truncated text
    """
    if not text:
        logger.warning("Content for truncation is empty")
        return ""
    
    estimated = estimate_tokens(text)
    logger.info(f"Estimated tokens before truncation: {estimated}, max allowed: {max_tokens}")
    
    # If already within limits, return as is
    if estimated <= max_tokens:
        logger.info("Content already within token limits, no truncation needed")
        return text
    
    # Check if the text already has a truncation note (indicating previous truncation)
    if text.endswith("[Note: Content has been truncated due to length limitations]"):
        # Further truncate by reduction_ratio
        truncate_length = int(len(text) * (1 - reduction_ratio))
        truncated_text = text[:truncate_length]
        
        # Ensure we don't cut in the middle of the truncation note
        if "[Note: Content has been truncated" not in truncated_text:
            truncated_text += "\n\n[Note: Content has been truncated due to length limitations]"
        
        logger.info(f"Further truncated already truncated content from {len(text)} to {len(truncated_text)} chars (reduction ratio: {reduction_ratio})")
    else:
        # Calculate approximate truncation ratio
        ratio = max_tokens / estimated
        
        # Truncate text - start with a conservative cut
        truncate_length = int(len(text) * ratio * 0.9)
        truncated_text = text[:truncate_length]
        
        # Add a note at the end
        truncated_text += "\n\n[Note: Content has been truncated due to length limitations]"
        
        logger.info(f"Initial truncation: reduced from {len(text)} to {len(truncated_text)} chars (ratio: {ratio})")
    
    # Verify final token count
    final_tokens = estimate_tokens(truncated_text)
    logger.info(f"Estimated tokens after truncation: {final_tokens}, target: {max_tokens}")
    
    return truncated_text

def generate_completion(prompt, content, temperature=0.7, max_tokens=4000, max_retries=5):
    """
    Generate completion using DeepSeek API with OpenAI client format
    
    Args:
        prompt (str): The prompt to use
        content (str): The content to analyze
        temperature (float): Controls randomness (0-1)
        max_tokens (int): Maximum number of tokens to generate
        max_retries (int): Maximum number of retries with progressive truncation
        
    Returns:
        str: The generated text
    """
    # Truncate content to avoid token limit issues
    truncated_content = truncate_content(content)
    
    retries = 0
    while retries <= max_retries:
        try:
            client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=f"{DEEPSEEK_BASE_URL}"
            )
            
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": truncated_content}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                print(f"Unexpected DeepSeek response format: {response}")
                return None
                
        except Exception as e:
            error_message = str(e)
            # Check if the error is related to token limit
            if "maximum context length" in error_message and "tokens" in error_message and retries < max_retries:
                print(f"Token limit exceeded (retry {retries+1}/{max_retries}). Further truncating content...")
                # Further truncate the content by 10%
                truncated_content = truncate_content(truncated_content, reduction_ratio=0.1)
                retries += 1
            else:
                print(f"Error generating DeepSeek completion: {e}")
                return None
    
    print(f"Failed to generate completion after {max_retries} truncation attempts")
    return None

def filter_content_urls(content, filter_prompt=None, num_results=10):
    """
    Filter and rank URLs from content using DeepSeek
    
    Args:
        content (str): The crawled content to analyze
        filter_prompt (str, optional): Custom prompt for URL filtering
        num_results (int): Number of top URLs to return
        
    Returns:
        list: Sorted list of dictionaries with URL and relevance score
    """
    try:
        prompt = f"""
        Based on the following crawled content, identify the {num_results} most valuable and relevant URLs of specific articles, papers or information.
        your choice should be based on: {filter_prompt}.
        
        For each URL:
        1. Extract the complete URL
        2. Determine its relevance and quality (on a scale of 1-10)
        3. Provide a brief description of what the content likely contains
        4. as for archive, like https://arxiv.org/pdf/2504.08758, you should replace the url to https://arxiv.org/html/2504.08758v1 (like this format)
        {{
            "url": "https://arxiv.org/html/2504.08758v1",
            "relevance_score": 8.5,
            "title": "Title of the article/paper",
            "description": "Brief description of the content"
        }}
        
        Format your response as a JSON array of objects with the following structure:
        [
            {{
                "url": "https://example.com/article1",
                "relevance_score": 8.5,
                "title": "Title of the article/paper",
                "description": "Brief description of the content"
            }},
            ...
        ]
        
        Rank the URLs from highest to lowest relevance.
        """
        
        response = generate_completion(prompt, content, temperature=0.3)
        
        # Parse the JSON response
        import json
        try:
            logger.info(f"Filtered URLs: {response}")
            urls_data = JsonUtils.safe_parse_json(response)
            logger.info(f"Filtered URLs parsed: {urls_data}")
            return urls_data
        except json.JSONDecodeError:
            logger.error(f"Error parsing JSON response: {response}")
            return []
            
    except Exception as e:
        logger.error(f"Error filtering content URLs: {e}")
        return []

def summarize_content(content, summary_prompt=None):
    """
    Summarize content into a card format using DeepSeek
    
    Args:
        content (str): The content to summarize
        summary_prompt (str, optional): Custom prompt for content summarization
        
    Returns:
        dict: The summarized card data
    """
    try:
        # Truncate content before generating the prompt to avoid token limit issues
        content = truncate_content(content)
        
        prompt = f"""
        Create a concise, informative reading card from the following content. The card should include:
        {summary_prompt}
        1. A clear, descriptive title (max 10 words)
        2. The key insights or information from the content (max 5 bullet points)
        3. Any important quotes or examples (if relevant)
        4. A brief conclusion or takeaway
        
        Format your response as a JSON object with the following structure, reply in Chinese:
        {{
            "title": "Title of the card",
            "key_points": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],
            "quotes": ["Quote 1", "Quote 2"],
            "conclusion": "conclusion, 200~500 words, if the content is not related to the summary_prompt, conclusion should be ''",
            "source_url": "URL of the original article/paper"
        }}

        Note: if the content is not related to the summary_prompt, conclusion should be ''.
        """
        response = generate_completion(prompt, content, temperature=0.5)
        
        # Parse the JSON response
        import json
        try:
            logger.info(f"Summarized content: {response}")
            card_data = JsonUtils.safe_parse_json(response)
            logger.info(f"Summarized content parsed: {card_data}")
            return card_data
        except json.JSONDecodeError:
            logger.error(f"Error parsing JSON response: {response}")
            # Create a basic card with the raw response
            return {
                "title": "Generated Card",
                "content": response,
                "source_url": ""
            }
            
    except Exception as e:
        logger.error(f"Error summarizing content: {e}")
        return None

def generate_poster_content(summary_card, title=None, subtitle=None):
    """
    Generate poster content from a single summary card using DeepSeek
    
    Args:
        summary_card (dict): Single summary card dictionary
        title (str, optional): Custom title for the poster
        subtitle (str, optional): Custom subtitle for the poster
        
    Returns:
        dict: Structured poster data for frontend rendering
    """
    try:
        if not summary_card:
            logger.warning("No summary card provided for poster generation")
            return {
                'success': False,
                'error': 'No summary card provided'
            }
        
        # Prepare content for DeepSeek to analyze and enhance
        card_content = f"""
        论文标题: {summary_card.get('title', '')}
        主要结论: {summary_card.get('conclusion', '')}
        """
        
        if summary_card.get('key_points'):
            card_content += f"关键要点: {', '.join(summary_card.get('key_points', []))}\n"
        if summary_card.get('quotes'):
            card_content += f"重要引用: {', '.join(summary_card.get('quotes', []))}\n"
        
        card_content += f"论文来源: {summary_card.get('source_url', '')}\n"
        
        prompt = f"""
        基于以下内容，生成一个"每日一读"主题的学术风格海报数据。

        请分析内容类型：
        1. 如果是学术论文：提取作者信息、研究背景、方法、结果等学术内容
        2. 如果是新闻文章：提取关键信息、背景、影响等新闻要素

        需要同时提供两种格式：
        1. poster_content: 纯数据内容，无样式
        2. poster_page: 带完整HTML样式的海报页面，可直接渲染

        海报要求：
        1. 采用蓝白配色方案，看起来高级专业
        2. 主题为"每日一读"，适合社交媒体分享
        3. 突出内容的核心价值和亮点
        4. 布局清晰，信息层次分明

        重要要求：
        - 标题必须保持原文标题，不要翻译或改写
        - 除标题外的所有内容（summary、background、methodology、key_findings、results、significance等）必须使用中文输出
        - 如果是论文，提取作者信息并适当缩略（最多显示前3位作者，超过时用"等"表示）
        - 如果是论文，增加研究背景、方法、结果等结构化内容
        - 如果是新闻，灵活展示重要内容和影响
        - 页脚必须使用："© 2025 Medbench | 社区驿站"
        - 海报主标题区域显示"每日一读"
        - 不要显示日期和星期几
        - 来源信息要包含具体的文章编号、DOI、期刊号等标识信息
        - JSON输出必须使用UTF-8编码，确保中文字符正常显示

        请以JSON格式回复（除title外所有字段必须使用中文）：
        {{
            "poster_content": {{
                "content_type": "论文" | "新闻" | "其他",
                "title": "保持原文标题，不要翻译或改写",
                "authors": "作者信息（论文类型时提供，适当缩略，中文表述）",
                "subtitle": "副标题或主要贡献概括（中文，不超过50字）",
                "summary": "内容亮点和价值总结（中文，200-400字）",
                "main_content": {{
                    // 如果是论文类型（所有字段使用中文）
                    "background": "研究背景和动机（中文）",
                    "methodology": "研究方法和技术路线（中文）",
                    "key_findings": ["关键发现1（中文）", "关键发现2（中文）", "关键发现3（中文）"],
                    "results": "主要结果和数据（中文）",
                    "significance": "研究意义和影响（中文）"
                    // 如果是新闻类型（所有字段使用中文）
                    "key_points": ["要点1（中文）", "要点2（中文）", "要点3（中文）"],
                    "background": "事件背景（中文）",
                    "impact": "影响和意义（中文）",
                    "details": "重要细节（中文）"
                }},
                "featured_quote": "最重要的结论或引用（中文）",
                "paper_info": {{
                    "source": "来源期刊/网站 + 具体编号/DOI（如：Nature Vol.123 | arXiv:2024.001 | 新华网202501001）",
                    "field": "领域分类（中文）",
                    "footer": "© 2025 Medbench | 社区驿站"
                }}
            }},
            "poster_page": "完整的HTML页面代码，包含CSS样式，采用蓝白配色，宽度800px，高度自适应。HTML应该是完整的，包含<!DOCTYPE html>声明。样式要现代化、专业、高级。海报顶部显示'每日一读'，不要显示日期。页脚显示来源信息和品牌标识。页脚格式：'© 2025 Medbench | 社区驿站'。根据content_type调整内容结构展示。HTML中的文字内容必须使用中文（标题除外）。"
        }}
        
        注意：
        - poster_page应该是完整可运行的HTML，包含所有必要的CSS样式
        - 使用蓝白配色：主色调#1e3a8a（深蓝）、#3b82f6（中蓝）、#dbeafe（浅蓝）、#ffffff（白色）
        - 字体使用系统字体栈：'PingFang SC', 'Helvetica Neue', Arial, sans-serif
        - 布局要响应式，高度自适应内容，避免固定高度
        - 避免使用外部资源，所有样式和内容都应该内联
        - 标题必须保持原文，不要翻译
        - 根据内容类型（论文/新闻）调整展示结构
        - 海报主题突出"每日一读"概念，但不显示具体日期
        - 页脚统一使用："© 2025 Medbench | 社区驿站"

        重要样式要求：
        - 顶部区域：使用深蓝色渐变背景（gradient从#1e3a8a到#3b82f6），包含"每日一读"标题和论文标题，文字为白色，padding适中
        - 中间主体区域：必须是纯白色背景(#ffffff)，包含主要内容（summary、背景、方法、结果等），文字为深色，这部分占海报的大部分面积
        - 底部区域：使用深蓝色渐变背景（gradient从#3b82f6到#1e3a8a），包含来源信息和页脚"© 2025 Medbench | 社区驿站"，文字为白色，padding适中
        - 整体采用卡片式设计，圆角阴影，现代感强
        - 布局结构：顶部蓝色条 + 中间白色主体内容区 + 底部蓝色条

        关键布局要求（必须严格遵守）：
        - body和html标签必须设置：margin: 0; padding: 0; background: #ffffff;
        - 海报外层容器宽度800px，margin: 0 auto; 背景色为白色
        - 只有顶部标题区和底部页脚区使用蓝色渐变背景
        - 中间内容区域必须保持白色背景，不要使用蓝色
        - 顶部和底部的渐变区域必须延伸到边缘，不留空白
        - 整体宽度固定800px，不要有额外的外边距或内边距导致右侧空白
        - 底部区域必须紧贴内容，不要留下方空白
        """
        
        response = generate_completion(prompt, card_content, temperature=0.6)
        
        if not response:
            logger.error("Failed to generate poster content from DeepSeek")
            return {
                'success': False,
                'error': 'Failed to generate poster content'
            }
        
        # Parse the JSON response
        try:
            poster_data = JsonUtils.safe_parse_json(response)

            # Check if response has correct structure with poster_content wrapper
            # If not, wrap the entire response as poster_content
            if 'poster_content' not in poster_data and 'content_type' in poster_data:
                logger.warning("DeepSeek response missing poster_content wrapper, wrapping response")
                # Extract poster_page if it exists at top level
                poster_page = poster_data.pop('poster_page', None)
                # Wrap the rest as poster_content
                wrapped_data = {
                    'poster_content': poster_data.copy()
                }
                if poster_page:
                    wrapped_data['poster_page'] = poster_page
                poster_data = wrapped_data

            logger.info(f"Generated poster content for paper: {poster_data.get('poster_content', {}).get('title', 'Unknown')}")

            # Add metadata
            poster_data['success'] = True
            poster_data['generated_at'] = datetime.now().isoformat()
            poster_data['original_card'] = summary_card  # Include original card for reference

            # Use custom title/subtitle if provided
            if title and 'poster_content' in poster_data:
                poster_data['poster_content']['title'] = title
            if subtitle and 'poster_content' in poster_data:
                poster_data['poster_content']['subtitle'] = subtitle

            return poster_data
            
        except Exception as e:
            logger.error(f"Error parsing poster JSON response: {e}")
            # Return a basic poster structure if parsing fails
            return {
                'success': True,
                'poster_content': {
                    'content_type': '其他',
                    'title': title or summary_card.get('title', '学术论文'),
                    'authors': '',  # 没有作者信息时为空
                    'subtitle': subtitle or '重要研究成果',
                    'summary': summary_card.get('conclusion', '这是一篇重要的学术研究，为相关领域提供了有价值的见解。'),
                    'main_content': {
                        'key_findings': summary_card.get('key_points', ['研究发现1', '研究发现2'])[:3],
                        'methodology': '详见原文',
                        'background': '研究背景信息',
                        'results': '主要研究结果',
                        'significance': '研究意义和影响'
                    },
                    'featured_quote': summary_card.get('quotes', [''])[0] if summary_card.get('quotes') else '',
                    'paper_info': {
                        'source': '学术论文',
                        'field': '研究领域',
                        'footer': '© 2025 Medbench | 社区驿站'
                    }
                },
                'poster_page': None,  # No fallback HTML, will use poster_content for rendering
                'original_card': summary_card,
                'generated_at': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error generating poster content: {e}")
        return {
            'success': False,
            'error': str(e)
        } 