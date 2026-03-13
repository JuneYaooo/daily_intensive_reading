from flask import Blueprint, jsonify, request
from ..services.scraper_service import batch_scrape_urls, scrape_single_url, get_cached_content
from ..services.deepseek_service import filter_content_urls, summarize_content, generate_poster_content
from ..utils.logger import BeijingLogger
import json
import os
import traceback
from datetime import datetime

def get_daily_reading_blueprint():
    daily_reading_bp = Blueprint('daily_reading', __name__)
    
    # 初始化日志记录器
    logger = BeijingLogger().get_logger()

    @daily_reading_bp.route('/generate', methods=['POST'])
    def generate_daily_reading():
        """
        Generate a daily intensive reading by:
        1. Batch crawling initial source URLs
        2. Filtering and ranking content URLs
        3. Crawling top content URLs
        4. Generating summary cards
        """
        logger.info("调用 POST /daily_reading/generate 路由")
        response = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'filtered_urls': [],
            'summary_cards': [],
            'errors': []  # New field to collect all errors
        }
        
        try:
            # Get request data (source URLs and optional prompts)
            data = request.get_json()
            source_urls = data.get('source_urls', [
                "https://github.com/dair-ai/ML-Papers-of-the-Week"
            ])
            filter_prompt = data.get('filter_prompt')
            summary_prompt = data.get('summary_prompt')
            num_results = data.get('num_results', 10)
            
            logger.info(f"生成日报，源URL数量: {len(source_urls)}, 请求结果数: {num_results}")
            
            # Step 1: Batch crawl initial source URLs
            logger.info("批量爬取源URL")
            initial_crawl_result = batch_scrape_urls(source_urls)
            
            if not initial_crawl_result.get('success'):
                error_msg = f"Initial crawl failed: {initial_crawl_result.get('error')}"
                logger.error(error_msg)
                response['errors'].append({
                    'phase': 'initial_crawl',
                    'message': error_msg,
                    'details': initial_crawl_result.get('error')
                })
                # Continue execution with partial data, if any
            
            # Process crawl results even if some failed
            combined_content = ""
            successful_urls = []
            
            for result in initial_crawl_result.get('results', []):
                if result.get('success') and result.get('content'):
                    combined_content += f"\nSource URL: {result.get('url')}\n"
                    combined_content += result.get('content')
                    successful_urls.append(result.get('url'))
                else:
                    error_msg = f"Failed to crawl URL: {result.get('url')}"
                    logger.warning(error_msg)
                    response['errors'].append({
                        'phase': 'url_crawl',
                        'url': result.get('url'),
                        'message': error_msg,
                        'details': result.get('error', 'Unknown error')
                    })
            
            if not combined_content:
                error_msg = "Failed to crawl any content from source URLs"
                logger.error(error_msg)
                response['errors'].append({
                    'phase': 'content_collection',
                    'message': error_msg
                })
                return jsonify(response), 500
            
            # Step 2: Filter and rank content URLs
            logger.info("过滤和排序内容URL")
            filtered_urls = filter_content_urls(combined_content, filter_prompt, num_results)
            
            if not filtered_urls or len(filtered_urls) == 0:
                error_msg = "Failed to extract any URLs from the crawled content"
                logger.error(error_msg)
                response['errors'].append({
                    'phase': 'url_filtering',
                    'message': error_msg
                })
                return jsonify(response), 500
            
            logger.info(f"提取到 {len(filtered_urls)} 个内容URL")
            response['filtered_urls'] = filtered_urls
            
            # Step 3 & 4: Crawl content URLs and generate summary cards
            content_crawl_results = []
            summary_cards = []
            successful_count = 0
            max_successful = min(2, len(filtered_urls))  # Limit to 2 successful cards or fewer if less URLs
            
            for item in filtered_urls:
                # Stop if we already have enough successful results
                if successful_count >= max_successful:
                    break
                    
                url = item.get('url')
                if not url:
                    response['errors'].append({
                        'phase': 'content_processing',
                        'message': "Missing URL in filtered result",
                        'item': item
                    })
                    continue
                    
                logger.info(f"尝试爬取URL: {url}")
                result = scrape_single_url(url)
                
                if result.get('success') and len(result.get('results', [])) > 0:
                    content_item = result.get('results')[0]
                    
                    if content_item.get('success') and content_item.get('content'):
                        logger.info(f"成功爬取内容: {url}，正在生成摘要卡片...")
                        
                        # Try to generate summary card
                        try:
                            card_data = summarize_content(content_item.get('content'), summary_prompt)
                            
                            # Summarize_content now always returns a dictionary
                            # Check if it has an error flag
                            if card_data.get('error'):
                                logger.warning(f"摘要生成返回错误: {url} - {card_data.get('conclusion')}")
                                response['errors'].append({
                                    'phase': 'summary_generation',
                                    'url': url,
                                    'message': "Error generating summary",
                                    'details': card_data.get('error_details', {})
                                })
                                # Still include the card with error information
                            
                            # Add source URL to the card
                            card_data['source_url'] = content_item.get('url') or url
                            summary_cards.append(card_data)
                            content_crawl_results.append(content_item)
                            successful_count += 1
                            logger.info(f"成功生成摘要卡片: {url}")
                        except Exception as e:
                            error_msg = f"摘要生成异常: {str(e)}"
                            logger.error(error_msg, exc_info=True)
                            response['errors'].append({
                                'phase': 'summary_generation_exception',
                                'url': url,
                                'message': error_msg,
                                'traceback': traceback.format_exc()
                            })
                    else:
                        error_msg = f"爬取结果无效: {url}"
                        logger.warning(error_msg)
                        response['errors'].append({
                            'phase': 'content_crawl',
                            'url': url,
                            'message': error_msg,
                            'details': content_item.get('error', 'No content found')
                        })
                else:
                    error_msg = f"爬取失败或无内容: {url}"
                    logger.warning(error_msg)
                    response['errors'].append({
                        'phase': 'url_crawl',
                        'url': url,
                        'message': error_msg,
                        'details': result.get('error', 'Unknown error')
                    })
            
            # Update response with summary cards
            response['summary_cards'] = summary_cards
            
            # Set success based on whether we have any summary cards
            response['success'] = len(summary_cards) > 0
            
            # Filter out URLs from filtered_urls that are already in summary_cards
            summary_card_urls = [card.get('source_url') for card in summary_cards]
            response['filtered_urls'] = [url_item for url_item in filtered_urls if url_item.get('url') not in summary_card_urls]
            
            # Save the results to output directory (optional)
            try:
                output_dir = os.path.join(os.getcwd(), "output", "daily_reading")
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                output_file = os.path.join(output_dir, f"{timestamp}_daily_reading.json")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(response, f, ensure_ascii=False, indent=2)
                
                logger.info(f"结果已保存到: {output_file}")
            except Exception as e:
                error_msg = f"保存结果到文件失败: {str(e)}"
                logger.warning(error_msg)
                response['errors'].append({
                    'phase': 'saving_results',
                    'message': error_msg,
                    'traceback': traceback.format_exc()
                })
            
            logger.info(f"日报生成{' 成功' if response['success'] else ' 部分成功'}, 获取到 {len(summary_cards)} 张摘要卡片, 错误数: {len(response['errors'])}")
            
            # Determine status code based on overall success
            status_code = 200 if response['success'] else 500 if len(summary_cards) == 0 else 206  # Partial content
            return jsonify(response), status_code
        
        except Exception as e:
            error_msg = f"Failed to generate daily reading: {str(e)}"
            logger.error(error_msg, exc_info=True)
            response['errors'].append({
                'phase': 'general_exception',
                'message': error_msg,
                'traceback': traceback.format_exc()
            })
            return jsonify(response), 500

    @daily_reading_bp.route('/history', methods=['GET'])
    def get_reading_history():
        """
        Get history of past daily readings
        """
        logger.info("调用 GET /daily_reading/history 路由")
        try:
            output_dir = os.path.join(os.getcwd(), "output", "daily_reading")
            
            if not os.path.exists(output_dir):
                logger.info("历史记录目录不存在")
                return jsonify({
                    'success': True,
                    'history': []
                })
            
            # Get list of reading files
            reading_files = [f for f in os.listdir(output_dir) if f.endswith('_daily_reading.json')]
            reading_files.sort(reverse=True)  # Sort by newest first
            
            logger.info(f"找到 {len(reading_files)} 条历史记录")
            
            history = []
            errors = []
            
            for file_name in reading_files:
                try:
                    file_path = os.path.join(output_dir, file_name)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reading_data = json.load(f)
                    
                    # Extract timestamp from filename
                    date_str = file_name.split('_daily_reading.json')[0]
                    
                    # Create summary
                    summary = {
                        'timestamp': reading_data.get('timestamp'),
                        'filename': file_name,
                        'url_count': len(reading_data.get('filtered_urls', [])),
                        'card_count': len(reading_data.get('summary_cards', [])),
                        'error_count': len(reading_data.get('errors', []))
                    }
                    history.append(summary)
                except Exception as e:
                    error_msg = f"读取历史文件 {file_name} 出错: {str(e)}"
                    logger.error(error_msg)
                    errors.append({
                        'filename': file_name,
                        'message': error_msg
                    })
            
            return jsonify({
                'success': True,
                'history': history,
                'errors': errors
            })
        
        except Exception as e:
            error_msg = f"Failed to get reading history: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return jsonify({
                'success': False,
                'error': error_msg,
                'traceback': traceback.format_exc()
            }), 500

    @daily_reading_bp.route('/history/<filename>', methods=['GET'])
    def get_reading_detail(filename):
        """
        Get details of a specific daily reading by filename
        """
        logger.info(f"调用 GET /daily_reading/history/{filename} 路由")
        try:
            output_dir = os.path.join(os.getcwd(), "output", "daily_reading")
            file_path = os.path.join(output_dir, filename)
            
            if not os.path.exists(file_path):
                logger.warning(f"历史记录文件不存在: {filename}")
                return jsonify({
                    'success': False,
                    'error': f"Reading file not found: {filename}"
                }), 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reading_data = json.load(f)
            
            logger.info(f"成功获取历史记录详情: {filename}")
            return jsonify(reading_data)
        
        except Exception as e:
            error_msg = f"Failed to get reading detail: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return jsonify({
                'success': False,
                'error': error_msg,
                'traceback': traceback.format_exc()
            }), 500
            
    @daily_reading_bp.route('/generate-one-card', methods=['POST'])
    def generate_one_card():
        """
        Generate a single card from a URL
        """
        logger.info("调用 POST /daily_reading/generate-one-card 路由")
        response = {
            'success': False,
            'errors': []
        }
        
        try:
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                error_msg = "URL is required"
                logger.warning(error_msg)
                response['errors'].append({
                    'phase': 'input_validation',
                    'message': error_msg
                })
                return jsonify(response), 400
                
            summary_prompt = data.get('summary_prompt')
            
            logger.info(f"尝试从URL生成卡片: {url}")
            
            # Scrape the URL
            result = scrape_single_url(url)
            
            if not result.get('success') or len(result.get('results', [])) == 0:
                error_msg = f"Failed to scrape URL: {url}"
                logger.error(error_msg)
                response['errors'].append({
                    'phase': 'url_crawl',
                    'url': url,
                    'message': error_msg,
                    'details': result.get('error', 'Unknown error')
                })
                return jsonify(response), 500
                
            content_item = result.get('results')[0]
            
            if not content_item.get('success') or not content_item.get('content'):
                error_msg = "No valid content found in the scraped page"
                logger.error(error_msg)
                response['errors'].append({
                    'phase': 'content_validation',
                    'url': url,
                    'message': error_msg,
                    'details': content_item.get('error', 'No content available')
                })
                return jsonify(response), 500
                
            # Generate summary card
            logger.info("生成摘要卡片")
            try:
                card_data = summarize_content(content_item.get('content'), summary_prompt)
                
                # Summarize_content now always returns a dictionary
                # Check if it has error information
                if card_data.get('error'):
                    logger.warning(f"摘要生成返回错误: {url} - {card_data.get('conclusion')}")
                    response['errors'].append({
                        'phase': 'summary_generation',
                        'url': url,
                        'message': "Summary generation returned an error",
                        'details': card_data.get('error_details', {})
                    })
                    
                    # We'll still return this with the error card
                    response['success'] = False  
                    card_data['source_url'] = content_item.get('url') or url
                    response['card'] = card_data
                    return jsonify(response), 206  # Partial content
                
                # Add source URL to the card
                card_data['source_url'] = content_item.get('url') or url
                
                logger.info(f"成功生成卡片: {card_data.get('title', '无标题')}")
                response['success'] = True
                response['card'] = card_data
                return jsonify(response)
                
            except Exception as e:
                error_msg = f"Exception during summary generation: {str(e)}"
                logger.error(error_msg, exc_info=True)
                response['errors'].append({
                    'phase': 'summary_generation_exception',
                    'url': url, 
                    'message': error_msg,
                    'traceback': traceback.format_exc()
                })
                return jsonify(response), 500
            
        except Exception as e:
            error_msg = f"Failed to generate card: {str(e)}"
            logger.error(error_msg, exc_info=True)
            response['errors'].append({
                'phase': 'general_exception',
                'message': error_msg,
                'traceback': traceback.format_exc()
            })
            return jsonify(response), 500

    @daily_reading_bp.route('/generate-poster', methods=['POST'])
    def generate_poster():
        """
        Generate poster content from URL (gets original content from Redis cache)
        """
        logger.info("调用 POST /daily_reading/generate-poster 路由")
        response = {
            'success': False,
            'errors': []
        }
        
        try:
            data = request.get_json()
            url = data.get('url')
            title = data.get('title')
            subtitle = data.get('subtitle')
            
            if not url:
                error_msg = "URL is required"
                logger.warning(error_msg)
                response['errors'].append({
                    'phase': 'input_validation',
                    'message': error_msg
                })
                return jsonify(response), 400
            
            logger.info(f"生成论文海报，URL: {url}")
            
            # Get original content from Redis cache
            original_content = get_cached_content(url)

            if not original_content:
                logger.warning(f"No cached content found for URL: {url}. Attempting to scrape...")

                # Attempt to scrape the URL
                scrape_result = scrape_single_url(url, use_cache=False)

                if not scrape_result.get('success') or not scrape_result.get('results'):
                    error_msg = f"Failed to scrape URL: {url}. {scrape_result.get('error', 'Unknown error')}"
                    logger.error(error_msg)
                    response['errors'].append({
                        'phase': 'content_retrieval',
                        'message': error_msg,
                        'url': url,
                        'scrape_error': scrape_result.get('error_details')
                    })
                    return jsonify(response), 404

                # Extract content from scrape result
                content_item = scrape_result['results'][0]
                if not content_item.get('content'):
                    error_msg = f"Scraped content is empty for URL: {url}"
                    logger.error(error_msg)
                    response['errors'].append({
                        'phase': 'content_retrieval',
                        'message': error_msg,
                        'url': url
                    })
                    return jsonify(response), 404

                original_content = content_item['content']
                logger.info(f"成功爬取URL内容，长度: {len(original_content)} 字符")
            else:
                logger.info(f"从Redis缓存获取到原文内容，长度: {len(original_content)} 字符")

            # Try to extract title from cached content if not provided
            extracted_title = title
            if not extracted_title:
                try:
                    # Try to parse cached content as JSON (from JigsawStack)
                    cached_data = json.loads(original_content)
                    # Try different possible title locations
                    if isinstance(cached_data, dict):
                        extracted_title = (
                            cached_data.get('meta', {}).get('title') or
                            cached_data.get('data', [{}])[0].get('title') if cached_data.get('data') else None
                        )
                except:
                    pass

            # Create a summary card from URL and cached content for poster generation
            summary_card = {
                'title': extracted_title or '学术论文',
                'conclusion': original_content,  # Use original content instead of summary
                'source_url': url,
                'key_points': [],
                'quotes': []
            }
            
            # Generate poster content using original content
            poster_data = generate_poster_content(summary_card, title, subtitle)
            
            if not poster_data.get('success'):
                error_msg = f"Failed to generate poster content: {poster_data.get('error', 'Unknown error')}"
                logger.error(error_msg)
                response['errors'].append({
                    'phase': 'poster_generation',
                    'message': error_msg,
                    'details': poster_data
                })
                return jsonify(response), 500
            
            logger.info(f"成功生成论文海报: {poster_data.get('poster_content', {}).get('title', '无标题')}")
            response['success'] = True
            response['poster'] = poster_data
            
            # Optional: Save poster data to file
            try:
                output_dir = os.path.join(os.getcwd(), "output", "posters")
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                paper_title = poster_data.get('poster_content', {}).get('title', 'unknown_paper')[:50]
                # Clean filename
                import re
                clean_title = re.sub(r'[^\w\s-]', '', paper_title).strip()
                clean_title = re.sub(r'[-\s]+', '-', clean_title)
                
                output_file = os.path.join(output_dir, f"{timestamp}_{clean_title}_poster.json")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(poster_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"论文海报数据已保存到: {output_file}")
            except Exception as e:
                error_msg = f"保存海报数据到文件失败: {str(e)}"
                logger.warning(error_msg)
                response['errors'].append({
                    'phase': 'saving_poster',
                    'message': error_msg,
                    'traceback': traceback.format_exc()
                })
            
            return jsonify(response)
            
        except Exception as e:
            error_msg = f"Failed to generate poster: {str(e)}"
            logger.error(error_msg, exc_info=True)
            response['errors'].append({
                'phase': 'general_exception',
                'message': error_msg,
                'traceback': traceback.format_exc()
            })
            return jsonify(response), 500
    
    return daily_reading_bp 