from flask import Blueprint, request, jsonify
from ..schemas.schemas import ReportGenerationSchema
from ..models.models import Prompt, Source
from ..services.deepseek_service import generate_completion
from ..config.db import get_db
from ..utils.logger import BeijingLogger

def get_report_blueprint():
    report_bp = Blueprint('reports', __name__)
    report_schema = ReportGenerationSchema()
    
    # 初始化日志记录器
    logger = BeijingLogger().get_logger()

    @report_bp.route('/generate', methods=['POST'])
    def generate():
        logger.info("调用 POST /reports/generate 路由")
        data = request.json
        errors = report_schema.validate(data)
        if errors:
            logger.warning(f"验证错误: {errors}")
            return jsonify({"message": "Validation error", "errors": errors}), 400
        
        db = next(get_db())
        
        # The content to process
        content = data['content']
        logger.info(f"生成报告，内容长度: {len(content)} 字符")
        
        # Get the prompt - several ways to specify:
        # 1. Direct prompt_content in the request (preferred)
        # 2. prompt_id to reference an existing prompt
        # 3. prompt_type to use a default prompt of a specific type
        # 4. If none provided, use a simple generic prompt
        prompt_content = None
        prompt_name = "Custom Prompt"
        
        if 'prompt_content' in data and data['prompt_content']:
            # Use direct prompt content from the request
            prompt_content = data['prompt_content']
            logger.info("使用请求中的提示内容")
        elif 'prompt_id' in data and data['prompt_id']:
            # Get the prompt by ID
            prompt_id = data['prompt_id']
            logger.info(f"使用提示 ID: {prompt_id}")
            prompt = db.query(Prompt).get(prompt_id)
            if not prompt:
                logger.warning(f"提示 {prompt_id} 未找到")
                return jsonify({"message": "Prompt not found"}), 404
            prompt_content = prompt.content
            prompt_name = prompt.name
            logger.info(f"获取到提示: '{prompt.name}'")
        elif 'prompt_type' in data and data['prompt_type']:
            # Get the default prompt of the specified type
            prompt_type = data['prompt_type']
            logger.info(f"使用默认 {prompt_type} 类型提示")
            if prompt_type not in ["filter", "summary", "general"]:
                logger.warning(f"无效的提示类型: {prompt_type}")
                return jsonify({"message": "Invalid prompt type"}), 400
                
            prompt = db.query(Prompt).filter_by(type=prompt_type, is_default=True).first()
            if not prompt:
                # No default prompt found for this type
                logger.warning(f"未找到默认的 {prompt_type} 提示，使用简单提示")
                prompt_content = "请分析并总结以下内容的要点。"  # Simple fallback
            else:
                prompt_content = prompt.content
                prompt_name = prompt.name
                logger.info(f"获取到默认 {prompt_type} 提示: '{prompt.name}'")
        else:
            # Use a simple default prompt if nothing specified
            logger.info("未指定提示，使用简单提示")
            prompt_content = "请分析并总结以下内容的要点。"
        
        # Get the source if provided
        source = None
        if 'source_id' in data and data['source_id']:
            source_id = data['source_id']
            logger.info(f"使用来源 ID: {source_id}")
            source = db.query(Source).get(source_id)
            if not source:
                logger.warning(f"来源 {source_id} 未找到")
                return jsonify({"message": "Source not found"}), 404
            logger.info(f"获取到来源: '{source.name}'")
        
        # Generate the report using DeepSeek
        logger.info("正在使用 DeepSeek 生成报告")
        try:
            report = generate_completion(prompt_content, content)
            
            if not report:
                logger.error("生成报告失败")
                return jsonify({"message": "Failed to generate report"}), 500
            
            logger.info(f"成功生成报告，长度: {len(report)} 字符")
            # Return the generated report
            return jsonify({
                "report": report,
                "source": source.name if source else None,
                "prompt": prompt_name
            })
        except Exception as e:
            error_msg = f"生成报告时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return jsonify({"message": error_msg}), 500
        
    return report_bp 