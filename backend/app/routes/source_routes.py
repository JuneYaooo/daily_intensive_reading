from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from ..models.models import Source
from ..schemas.schemas import SourceSchema
from ..config.db import get_db
from ..utils.logger import BeijingLogger

# 创建一个函数来获取blueprint，而不是直接在模块级别创建
def get_source_blueprint():
    source_bp = Blueprint('sources', __name__)
    source_schema = SourceSchema()
    sources_schema = SourceSchema(many=True)
    
    # 初始化日志记录器
    logger = BeijingLogger().get_logger()

    @source_bp.route('/', methods=['GET'])
    def get_all_sources():
        logger.info("调用 GET /sources/ 路由")
        db = next(get_db())
        sources = db.query(Source).all()
        logger.info(f"获取到 {len(sources)} 个信息源")
        return jsonify(sources_schema.dump(sources))

    @source_bp.route('/<int:id>', methods=['GET'])
    def get_source(id):
        logger.info(f"调用 GET /sources/{id} 路由")
        db = next(get_db())
        source = db.query(Source).get(id)
        if not source:
            logger.warning(f"信息源 {id} 未找到")
            return jsonify({"message": "Source not found"}), 404
        logger.info(f"获取到信息源 ID: {id}, 名称: '{source.name}'")
        return jsonify(source_schema.dump(source))

    @source_bp.route('/', methods=['POST'])
    def create_source():
        logger.info("调用 POST /sources/ 路由")
        data = request.json
        errors = source_schema.validate(data)
        if errors:
            logger.warning(f"验证错误: {errors}")
            return jsonify({"message": "Validation error", "errors": errors}), 400
        
        try:
            db = next(get_db())
            new_source = Source(
                name=data['name'],
                url=data.get('url'),
                description=data.get('description')
            )
            
            db.add(new_source)
            db.commit()
            db.refresh(new_source)
            
            logger.info(f"成功创建信息源: ID {new_source.id}, 名称 '{new_source.name}'")
            return jsonify(source_schema.dump(new_source)), 201
        except Exception as e:
            logger.error(f"创建信息源时出错: {str(e)}", exc_info=True)
            db.rollback()
            return jsonify({"message": f"Error creating source: {str(e)}"}), 500

    @source_bp.route('/<int:id>', methods=['PUT'])
    def update_source(id):
        logger.info(f"调用 PUT /sources/{id} 路由")
        data = request.json
        db = next(get_db())
        source = db.query(Source).get(id)
        
        if not source:
            logger.warning(f"信息源 {id} 未找到")
            return jsonify({"message": "Source not found"}), 404
        
        # Remove read-only fields before validation
        if 'id' in data:
            data.pop('id')
        if 'created_at' in data:
            data.pop('created_at')
        if 'updated_at' in data:
            data.pop('updated_at')
        
        errors = source_schema.validate(data)
        if errors:
            logger.warning(f"验证错误: {errors}")
            return jsonify({"message": "Validation error", "errors": errors}), 400
        
        try:
            source.name = data['name']
            source.url = data.get('url', source.url)
            source.description = data.get('description', source.description)
            
            db.commit()
            db.refresh(source)
            
            logger.info(f"成功更新信息源: ID {id}, 名称 '{source.name}'")
            return jsonify(source_schema.dump(source))
        except Exception as e:
            logger.error(f"更新信息源时出错: {str(e)}", exc_info=True)
            db.rollback()
            return jsonify({"message": f"Error updating source: {str(e)}"}), 500

    @source_bp.route('/<int:id>', methods=['DELETE'])
    def delete_source(id):
        logger.info(f"调用 DELETE /sources/{id} 路由")
        db = next(get_db())
        source = db.query(Source).get(id)
        
        if not source:
            logger.warning(f"信息源 {id} 未找到")
            return jsonify({"message": "Source not found"}), 404
        
        try:
            db.delete(source)
            db.commit()
            
            logger.info(f"成功删除信息源: ID {id}")
            return jsonify({"message": "Source deleted successfully"})
        except Exception as e:
            logger.error(f"删除信息源时出错: {str(e)}", exc_info=True)
            db.rollback()
            return jsonify({"message": f"Error deleting source: {str(e)}"}), 500
        
    return source_bp