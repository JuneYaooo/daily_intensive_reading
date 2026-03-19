from flask import Flask, jsonify, request, got_request_exception
from flask_cors import CORS
import os
import sys
import signal
import traceback
import threading
import psutil
import time
from datetime import datetime
from dotenv import load_dotenv
from .utils.logger import BeijingLogger

# Initialize logger
logger = BeijingLogger().get_logger()

# Load environment variables
load_dotenv()

# Create the Flask app
app = Flask(__name__)
app.url_map.strict_slashes = False

# Signal handler for various termination signals
def signal_handler(sig, frame):
    signal_name = {
        signal.SIGINT: "SIGINT",
        signal.SIGTERM: "SIGTERM",
        signal.SIGABRT: "SIGABRT",
        signal.SIGSEGV: "SIGSEGV"
    }.get(sig, f"Signal {sig}")

    # Keep signal handler minimal and async-safe
    # Avoid complex operations like traceback.format_stack() during signal handling
    try:
        logger.critical(f"收到终止信号: {signal_name}, PID={os.getpid()}")
    except:
        pass  # Ignore logging errors during shutdown
    sys.exit(1)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGABRT, signal_handler)

# Global exception handler
def log_exception(sender, exception, **extra):
    logger.critical(f"未捕获的异常: {str(exception)}")
    logger.critical(f"异常类型: {type(exception).__name__}")
    logger.critical(f"堆栈跟踪:\n{traceback.format_exc()}")
    
    # Get current request info if available
    if request:
        logger.critical(f"请求路径: {request.path}")
        logger.critical(f"请求方法: {request.method}")
        logger.critical(f"请求参数: {request.args}")
        if request.is_json:
            try:
                logger.critical(f"请求JSON: {request.get_json()}")
            except:
                pass

# Register global exception handler
got_request_exception.connect(log_exception, app)

# 配置 CORS，允许前端访问
CORS(app, 
     resources={r"/api/*": {"origins": "*"}}, 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Import route functions that return blueprints
from .routes.source_routes import get_source_blueprint
from .routes.prompt_routes import get_prompt_blueprint
from .routes.report_routes import get_report_blueprint
from .routes.card_routes import get_card_blueprint
from .routes.daily_reading_routes import get_daily_reading_blueprint

# Record startup information
logger.info(f"应用启动, 进程ID: {os.getpid()}")
logger.info(f"Python版本: {sys.version}")
logger.info(f"工作目录: {os.getcwd()}")

# Get blueprints from functions
source_bp = get_source_blueprint()
prompt_bp = get_prompt_blueprint()
report_bp = get_report_blueprint()
card_bp = get_card_blueprint()
daily_reading_bp = get_daily_reading_blueprint()

# Register blueprints
app.register_blueprint(source_bp, url_prefix='/api/sources')
app.register_blueprint(prompt_bp, url_prefix='/api/prompts')
app.register_blueprint(report_bp, url_prefix='/api/reports')
app.register_blueprint(card_bp, url_prefix='/api/cards')
app.register_blueprint(daily_reading_bp, url_prefix='/api/daily-reading')

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Daily Intensive Reading API"})

# Monitoring endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with detailed system information"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # Convert to MB for readability
        rss_mb = memory_info.rss / 1024 / 1024
        vms_mb = memory_info.vms / 1024 / 1024
        
        # Get CPU usage
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # Get process info
        start_time = datetime.fromtimestamp(process.create_time()).isoformat()
        
        # Get thread count
        thread_count = len(process.threads())
        
        # Get open files count
        try:
            open_files_count = len(process.open_files())
        except:
            open_files_count = "N/A"
        
        # Return detailed health info
        return jsonify({
            "status": "ok",
            "pid": os.getpid(),
            "uptime": start_time,
            "memory": {
                "rss_mb": round(rss_mb, 2),
                "vms_mb": round(vms_mb, 2)
            },
            "cpu_percent": cpu_percent,
            "threads": thread_count,
            "open_files": open_files_count,
            "python_version": sys.version,
        })
    except Exception as e:
        logger.error(f"健康检查错误: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# 添加针对preflight请求的处理
@app.route('/api/sources', methods=['OPTIONS'])
def handle_options_sources():
    return '', 204

@app.route('/api/sources/<path:path>', methods=['OPTIONS'])
def handle_options_sources_path(path):
    return '', 204

@app.route('/api/prompts', methods=['OPTIONS'])
def handle_options_prompts():
    return '', 204

@app.route('/api/prompts/<path:path>', methods=['OPTIONS'])
def handle_options_prompts_path(path):
    return '', 204

@app.route('/api/reports', methods=['OPTIONS'])
def handle_options_reports():
    return '', 204

@app.route('/api/reports/<path:path>', methods=['OPTIONS'])
def handle_options_reports_path(path):
    return '', 204

@app.route('/api/cards', methods=['OPTIONS'])
def handle_options_cards():
    return '', 204

@app.route('/api/cards/<path:path>', methods=['OPTIONS'])
def handle_options_cards_path(path):
    return '', 204

@app.route('/api/daily-reading', methods=['OPTIONS'])
def handle_options_daily_reading():
    return '', 204

@app.route('/api/daily-reading/<path:path>', methods=['OPTIONS'])
def handle_options_daily_reading_path(path):
    return '', 204

# Log when app is fully initialized
logger.info("应用初始化完成，准备处理请求")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Set Flask's default timeout to 20 minutes
    app.config['TIMEOUT'] = 1200
    app.run(host='0.0.0.0', port=port, debug=True)