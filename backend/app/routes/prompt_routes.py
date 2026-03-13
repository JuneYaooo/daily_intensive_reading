from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from ..models.models import Prompt
from ..schemas.schemas import PromptSchema
from ..config.db import get_db
from ..utils.logger import BeijingLogger

def get_prompt_blueprint():
    prompt_bp = Blueprint('prompts', __name__)
    prompt_schema = PromptSchema()
    prompts_schema = PromptSchema(many=True)
    
    # 初始化日志记录器
    logger = BeijingLogger().get_logger()

    @prompt_bp.route('/', methods=['GET'])
    def get_all_prompts():
        logger.info("调用 GET /prompts/ 路由")
        db = next(get_db())
        prompts = db.query(Prompt).all()
        logger.info(f"获取到 {len(prompts)} 个提示")
        return jsonify(prompts_schema.dump(prompts))

    @prompt_bp.route('/defaults', methods=['GET'])
    def get_default_prompts():
        """Get all default prompts"""
        logger.info("调用 GET /prompts/defaults 路由")
        db = next(get_db())
        default_prompts = db.query(Prompt).filter_by(is_default=True).all()
        logger.info(f"获取到 {len(default_prompts)} 个默认提示")
        return jsonify(prompts_schema.dump(default_prompts))

    @prompt_bp.route('/defaults/<string:type>', methods=['GET'])
    def get_default_prompt_by_type(type):
        """Get default prompt by type (filter, summary, general)"""
        logger.info(f"调用 GET /prompts/defaults/{type} 路由")
        if type not in ["filter", "summary", "general"]:
            logger.warning(f"无效的提示类型: {type}")
            return jsonify({"message": "Invalid prompt type"}), 400
            
        db = next(get_db())
        prompt = db.query(Prompt).filter_by(type=type, is_default=True).first()
        
        if not prompt:
            logger.info(f"未找到默认的 {type} 提示")
            return jsonify({"message": f"No default {type} prompt found"}), 404
            
        logger.info(f"获取到默认的 {type} 提示: ID {prompt.id}, 名称 '{prompt.name}'")
        return jsonify(prompt_schema.dump(prompt))

    @prompt_bp.route('/<int:id>', methods=['GET'])
    def get_prompt(id):
        logger.info(f"调用 GET /prompts/{id} 路由")
        db = next(get_db())
        prompt = db.query(Prompt).get(id)
        if not prompt:
            logger.warning(f"提示 {id} 未找到")
            return jsonify({"message": "Prompt not found"}), 404
        logger.info(f"获取到提示 ID: {id}, 名称: '{prompt.name}'")
        return jsonify(prompt_schema.dump(prompt))

    @prompt_bp.route('/', methods=['POST'])
    def create_prompt():
        logger.info("调用 POST /prompts/ 路由")
        data = request.json
        logger.debug(f"接收到的数据: {data}")
        
        errors = prompt_schema.validate(data)
        if errors:
            logger.warning(f"验证错误: {errors}")
            return jsonify({"message": "Validation error", "errors": errors}), 400
        
        try:
            db = next(get_db())
            new_prompt = Prompt(
                name=data['name'],
                content=data['content'],
                description=data.get('description'),
                type=data.get('type', 'general'),
                is_default=data.get('is_default', False)
            )
            
            db.add(new_prompt)
            db.commit()
            db.refresh(new_prompt)
            
            logger.info(f"成功创建提示: ID {new_prompt.id}, 名称 '{new_prompt.name}'")
            return jsonify(prompt_schema.dump(new_prompt)), 201
        except Exception as e:
            logger.error(f"创建提示时出错: {str(e)}", exc_info=True)
            db.rollback()
            return jsonify({"message": f"Error creating prompt: {str(e)}"}), 500

    @prompt_bp.route('/<int:id>', methods=['PUT'])
    def update_prompt(id):
        logger.info(f"调用 PUT /prompts/{id} 路由")
        data = request.json
        db = next(get_db())
        prompt = db.query(Prompt).get(id)
        
        if not prompt:
            logger.warning(f"提示 {id} 未找到")
            return jsonify({"message": "Prompt not found"}), 404
        
        errors = prompt_schema.validate(data)
        if errors:
            logger.warning(f"验证错误: {errors}")
            return jsonify({"message": "Validation error", "errors": errors}), 400
        
        try:
            prompt.name = data['name']
            prompt.content = data['content']
            prompt.description = data.get('description', prompt.description)
            prompt.type = data.get('type', prompt.type)
            prompt.is_default = data.get('is_default', prompt.is_default)
            
            db.commit()
            db.refresh(prompt)
            
            logger.info(f"成功更新提示: ID {id}, 名称 '{prompt.name}'")
            return jsonify(prompt_schema.dump(prompt))
        except Exception as e:
            logger.error(f"更新提示时出错: {str(e)}", exc_info=True)
            db.rollback()
            return jsonify({"message": f"Error updating prompt: {str(e)}"}), 500

    @prompt_bp.route('/<int:id>', methods=['DELETE'])
    def delete_prompt(id):
        logger.info(f"调用 DELETE /prompts/{id} 路由")
        db = next(get_db())
        prompt = db.query(Prompt).get(id)
        
        if not prompt:
            logger.warning(f"提示 {id} 未找到")
            return jsonify({"message": "Prompt not found"}), 404
        
        try:
            db.delete(prompt)
            db.commit()
            
            logger.info(f"成功删除提示: ID {id}")
            return jsonify({"message": "Prompt deleted successfully"})
        except Exception as e:
            logger.error(f"删除提示时出错: {str(e)}", exc_info=True)
            db.rollback()
            return jsonify({"message": f"Error deleting prompt: {str(e)}"}), 500
        
    return prompt_bp 