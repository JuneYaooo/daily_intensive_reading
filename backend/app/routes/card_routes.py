from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from ..models.models import FavoriteCard, Prompt
from ..schemas.schemas import FavoriteCardSchema, CardGenerationSchema
from ..services.deepseek_service import summarize_content
from ..config.db import get_db
from sqlalchemy import or_, func, desc
from ..utils.logger import BeijingLogger
import json

def get_card_blueprint():
    card_bp = Blueprint('cards', __name__)
    card_schema = FavoriteCardSchema()
    cards_schema = FavoriteCardSchema(many=True)
    card_generation_schema = CardGenerationSchema()
    
    # 初始化日志记录器
    logger = BeijingLogger().get_logger()

    @card_bp.route('/', methods=['GET'])
    def get_all_cards():
        logger.info("调用 GET /cards/ 路由")
        db = next(get_db())
        cards = db.query(FavoriteCard).all()
        logger.info(f"获取到 {len(cards)} 张卡片")
        return jsonify(cards_schema.dump(cards))

    @card_bp.route('/<int:id>', methods=['GET'])
    def get_card(id):
        logger.info(f"调用 GET /cards/{id} 路由")
        db = next(get_db())
        card = db.query(FavoriteCard).get(id)
        if not card:
            logger.warning(f"卡片 {id} 未找到")
            return jsonify({"message": "Card not found"}), 404
        logger.info(f"成功获取卡片 {id}")
        return jsonify(card_schema.dump(card))

    @card_bp.route('/search', methods=['GET'])
    def search_cards():
        """Search cards by title, conclusion, quotes, or author"""
        query = request.args.get('q', '')
        logger.info(f"调用 GET /cards/search 路由，搜索关键字: {query}")
        
        if not query or len(query) < 2:
            logger.warning("搜索查询必须至少包含2个字符")
            return jsonify({"message": "Search query must be at least 2 characters"}), 400
            
        db = next(get_db())
        search_query = f"%{query}%"  # For LIKE operator
        
        cards = db.query(FavoriteCard).filter(
            or_(
                FavoriteCard.title.ilike(search_query),
                FavoriteCard.conclusion.ilike(search_query),
                FavoriteCard.key_points.ilike(search_query),
                FavoriteCard.quotes.ilike(search_query),
                FavoriteCard.author.ilike(search_query)
            )
        ).all()
        
        logger.info(f"搜索 '{query}' 找到 {len(cards)} 张卡片")
        return jsonify(cards_schema.dump(cards))
       
    @card_bp.route('/popular', methods=['GET'])
    def get_popular_cards():
        """Get most recent cards"""
        limit = request.args.get('limit', 10, type=int)
        logger.info(f"调用 GET /cards/popular 路由，限制: {limit}")
        
        db = next(get_db())
        
        # Return the most recent cards
        popular_cards = db.query(FavoriteCard).order_by(desc(FavoriteCard.created_at)).limit(limit).all()
        
        logger.info(f"获取到 {len(popular_cards)} 张最新卡片")
        return jsonify(cards_schema.dump(popular_cards))

    @card_bp.route('/create', methods=['POST'])
    def create_card():
        logger.info("调用 POST /cards/create 路由")
        data = request.json
        if 'title' not in data:
            logger.warning("创建卡片缺少必填字段")
            return jsonify({"message": "Missing required fields"}), 400
        
        db = next(get_db())
            
        # Create new favorite card
        new_card = FavoriteCard(
            title=data['title'],
            source_url=data.get('source_url', ''),
            conclusion=data.get('conclusion', ''),
            key_points=json.dumps(data.get('key_points', [])),
            quotes=json.dumps(data.get('quotes', [])),
            author=data.get('author', '')
        )
        
        try:
            db.add(new_card)
            db.commit()
            db.refresh(new_card)
            
            # Convert JSON string fields back to lists for response
            result = card_schema.dump(new_card)
            try:
                result['key_points'] = json.loads(new_card.key_points) if new_card.key_points else []
                result['quotes'] = json.loads(new_card.quotes) if new_card.quotes else []
            except Exception as e:
                # Fallback to original string if JSON parsing fails
                logger.error(f"解析JSON字段失败: {str(e)}")
                result['key_points'] = []
                result['quotes'] = []
            
            logger.info(f"成功创建卡片 ID: {new_card.id}")
            return jsonify(result), 201
        except Exception as e:
            logger.error(f"创建卡片时发生错误: {str(e)}")
            db.rollback()
            return jsonify({"message": f"Error creating card: {str(e)}"}), 500
        
    @card_bp.route('/<int:id>', methods=['PUT'])
    def update_card(id):
        """Update an existing card"""
        logger.info(f"调用 PUT /cards/{id} 路由")
        data = request.json
        db = next(get_db())
        
        # Find the card
        card = db.query(FavoriteCard).get(id)
        if not card:
            logger.warning(f"卡片 {id} 未找到")
            return jsonify({"message": "Card not found"}), 404
            
        # Update fields
        if 'title' in data:
            card.title = data['title']
        if 'conclusion' in data:
            card.conclusion = data['conclusion']
        if 'key_points' in data:
            card.key_points = json.dumps(data['key_points'])
        if 'quotes' in data:
            card.quotes = json.dumps(data['quotes'])
        if 'author' in data:
            card.author = data['author']
        if 'source_url' in data:
            card.source_url = data['source_url']
        
        try:        
            db.commit()
            db.refresh(card)
            
            # Convert JSON string fields back to lists for response
            result = card_schema.dump(card)
            try:
                result['key_points'] = json.loads(card.key_points) if card.key_points else []
                result['quotes'] = json.loads(card.quotes) if card.quotes else []
            except Exception as e:
                # Fallback to original string if JSON parsing fails
                logger.error(f"解析JSON字段失败: {str(e)}")
                result['key_points'] = []
                result['quotes'] = []
            
            logger.info(f"成功更新卡片 ID: {id}")
            return jsonify(result)
        except Exception as e:
            logger.error(f"更新卡片时发生错误: {str(e)}")
            db.rollback()
            return jsonify({"message": f"Error updating card: {str(e)}"}), 500

    @card_bp.route('/<int:id>', methods=['DELETE'])
    def delete_card(id):
        """Delete a card"""
        logger.info(f"调用 DELETE /cards/{id} 路由")
        db = next(get_db())
        
        # Find the card
        card = db.query(FavoriteCard).get(id)
        if not card:
            logger.warning(f"卡片 {id} 未找到")
            return jsonify({"message": "Card not found"}), 404
        
        try:    
            # Delete the card
            db.delete(card)
            db.commit()
            
            logger.info(f"成功删除卡片 ID: {id}")
            return jsonify({"message": "Card deleted successfully"})
        except Exception as e:
            logger.error(f"删除卡片时发生错误: {str(e)}")
            db.rollback()
            return jsonify({"message": f"Error deleting card: {str(e)}"}), 500
        
    @card_bp.route('/stats', methods=['GET'])
    def get_card_stats():
        """Get general statistics about cards"""
        logger.info("调用 GET /cards/stats 路由")
        db = next(get_db())
        
        # Total number of cards
        total_cards = db.query(func.count(FavoriteCard.id)).scalar()
        
        # Most recent cards
        recent_cards = db.query(FavoriteCard).order_by(
            desc(FavoriteCard.created_at)
        ).limit(5).all()
        
        # Process recent cards to convert JSON strings to lists
        results = cards_schema.dump(recent_cards)
        for i, card in enumerate(recent_cards):
            try:
                results[i]['key_points'] = json.loads(card.key_points) if card.key_points else []
                results[i]['quotes'] = json.loads(card.quotes) if card.quotes else []
            except Exception as e:
                logger.error(f"解析JSON字段失败: {str(e)}")
                results[i]['key_points'] = []
                results[i]['quotes'] = []
        
        logger.info(f"统计信息: 总卡片数 {total_cards}, 最新卡片数 {len(recent_cards)}")
        return jsonify({
            "total_cards": total_cards,
            "recent_cards": results
        })
        
    return card_bp 