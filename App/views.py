# views.py 路由 + 视图函数
import os
import re
import json
import math
import hashlib
import secrets
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from functools import wraps
from flask import request, jsonify, make_response, Response
from flask import Blueprint
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
# 加在文件顶部 import 区
import jieba
from .utils.api_utils import APIUtils
from .models import *
from .utils.document_parser import parse_document

# 加载环境变量
load_dotenv()
blus = Blueprint("user", __name__)

# 从环境变量读取数据库配置
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USERNAME', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'database': os.getenv('DB_DATABASE', 'mysql'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4')
}

# ==================== 操作日志辅助函数 ====================
def add_operation_log(user_id, username, action, target_type=None, target_id=None, detail=None):
    """记录操作日志"""
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr) or 'unknown'
        log = OperationLog(
            user_id=user_id,
            username=username,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip.split(',')[0].strip() if ip else 'unknown'
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"记录操作日志失败: {e}")

# ==================== 权限检查装饰器 ====================
def admin_required(f):
    """管理员权限检查"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('token')
        if not token:
            return APIUtils.error_auth(message="请先登录", code=401)
        token_row = Token.query.filter_by(token=token).first()
        if not token_row or token_row.expires_at < datetime.utcnow():
            return APIUtils.error_auth(message="登录已过期", code=401)
        user = User.query.get(token_row.user_id)
        if not user or user.role != 0:
            return APIUtils.error_auth(message="需要管理员权限", code=403)
        return f(*args, **kwargs)
    return decorated

def active_user_required(f):
    """检查用户是否被禁用"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('token')
        if not token:
            return APIUtils.error_auth(message="请先登录", code=401)
        token_row = Token.query.filter_by(token=token).first()
        if not token_row or token_row.expires_at < datetime.utcnow():
            return APIUtils.error_auth(message="登录已过期", code=401)
        user = User.query.get(token_row.user_id)
        if not user:
            return APIUtils.error_auth(message="用户不存在", code=401)
        if user.status == 0:
            return APIUtils.error_auth(message="账号已被禁用", code=403)
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    """获取当前登录用户"""
    token = request.headers.get('token')
    if not token:
        return None
    token_row = Token.query.filter_by(token=token).first()
    if not token_row or token_row.expires_at < datetime.utcnow():
        return None
    return User.query.get(token_row.user_id)


# ==================== 用户认证相关API ====================

@blus.route('/api/logout', methods=['POST'])
def user_logout():
    token = request.headers.get('token')
    if not token:
        return APIUtils.error_auth(message="请先登录", code=401)
    token_row = Token.query.filter_by(token=token).first()
    if token_row:
        user = User.query.get(token_row.user_id)
        add_operation_log(token_row.user_id, user.username if user else 'unknown', 'logout')
        db.session.delete(token_row)
        db.session.commit()
    return APIUtils.success_response(message="退出登录成功！")


# 注册
@blus.route('/api/register', methods=['POST'])
def user_register():
    required_fields = ['username', 'password']
    is_valid, message = APIUtils.validate_json(request.json, required_fields)
    if not is_valid:
        return APIUtils.error_response(message, status_code=400)
    username = request.json['username']
    password = request.json['password']
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return APIUtils.error_response("用户名已经存在!", status_code=400)
    # 哈希处理密码
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    # 创建新用户
    new_user = User(username=username, password=hashed_password, role=1)
    db.session.add(new_user)
    db.session.commit()
    add_operation_log(new_user.id, username, 'register', 'user', new_user.id, f"用户注册: {username}")
    return APIUtils.success_response(message="注册成功!")


@blus.route('/api/login', methods=['POST'])
def user_login():
    required_fields = ['username', 'password']
    is_valid, message = APIUtils.validate_json(request.json, required_fields)
    if not is_valid:
        return APIUtils.error_response(message, status_code=400)
    username = request.json['username']
    password = request.json['password']
    user = User.query.filter_by(username=username).first()
    if user is None:
        return APIUtils.error_response("用户名错误或不存在！", status_code=500)
    if user.status == 0:
        return APIUtils.error_response("账号已被禁用，请联系管理员！", status_code=403)
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if hashed_password != user.password:
        return APIUtils.error_response("密码错误或不存在！", status_code=500)
    # 生成并持久化 token（默认 2 小时过期）
    raw_token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(hours=2)
    token_row = Token(user_id=user.id, token=raw_token, expires_at=expires_at)
    db.session.add(token_row)
    db.session.commit()
    add_operation_log(user.id, username, 'login', 'user', user.id, f"用户登录: {username}")
    return APIUtils.success_response(
        data={'token': raw_token, 'userId': user.id, 'username': user.username, 'role': user.role,
              'expiresAt': expires_at.isoformat() + 'Z'}, message="登录成功！")


@blus.route('/sys/user/info', methods=['GET'])
def user_info():
    token = request.headers.get('token')
    if not token:
        return APIUtils.error_auth(message="未提供令牌")
    token_row = Token.query.filter_by(token=token).first()
    if token_row is None:
        return APIUtils.error_auth(message="令牌无效，请重新登录")
    if token_row.expires_at < datetime.utcnow():
        return APIUtils.error_auth(message="登录已过期，请重新登录")
    user = User.query.filter_by(id=token_row.user_id).first()
    if user is None:
        return APIUtils.error_auth(message="用户不存在")
    if user.status == 0:
        return APIUtils.error_auth(message="账号已被禁用", code=403)
    return APIUtils.success_response(
        data={'token': token_row.token, 'userId': user.id, 'username': user.username, 'role': user.role,
              'expiresAt': token_row.expires_at.isoformat() + 'Z'}, message="登录有效")


@blus.route('/change_password', methods=['POST'])
def change_password():
    required_fields = ['username', 'old_password', 'new_password']
    is_valid, message = APIUtils.validate_json(request.json, required_fields)
    if not is_valid:
        return APIUtils.error_response(message, status_code=400)
    username = request.json['username']
    old_password = request.json['old_password']
    new_password = request.json['new_password']
    user = User.query.filter_by(username=username).first()
    if user is None:
        return APIUtils.error_response("用户不存在！", status_code=404)
    hashed_old_password = hashlib.sha256(old_password.encode()).hexdigest()
    if hashed_old_password != user.password:
        return APIUtils.error_response("原始密码不正确！", status_code=401)
    # 哈希处理新密码
    hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()
    user.password = hashed_new_password
    db.session.commit()
    add_operation_log(user.id, username, 'change_password', 'user', user.id, f"用户修改密码: {username}")
    return APIUtils.success_response(message="密码修改成功！")


@blus.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return APIUtils.error_response("用户不存在！", status_code=404)
    if user.username.lower() == 'admin':
        return APIUtils.error_response("无法删除管理员账户！", status_code=403)
    current = get_current_user()
    add_operation_log(current.id, current.username, 'delete_user', 'user', user_id, f"删除用户: {user.username}")
    db.session.delete(user)
    db.session.commit()
    return APIUtils.success_response(message="用户删除成功！")


# 用户管理
@blus.route('/api/users/page', methods=['GET'])
@admin_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 10, type=int)
    username = request.args.get('username', type=str)
    query = User.query
    if username:
        query = query.filter(User.username.like(f'%{username}%'))
    users_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = users_pagination.items
    users_list = []
    for user in users:
        users_list.append({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'status': user.status,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    response = {
        'list': users_list,
        'page': {
            'total': users_pagination.total,
            'page': users_pagination.page,
            'limit': users_pagination.per_page
        }
    }
    return APIUtils.success_response(data=response, message="获取用户列表成功")


# 新增用户
@blus.route('/api/users', methods=['POST'])
@admin_required
def add_user():
    data = request.get_json()
    if not all([data.get('username'), data.get('password')]):
        return APIUtils.error_response(message="用户名和密码不能为空", code=400)
    if User.query.filter_by(username=data['username']).first():
        return APIUtils.error_response(message="用户名已存在")
    hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()
    new_user = User(
        username=data['username'],
        password=hashed_password,
        role=data.get('role', 1)
    )
    db.session.add(new_user)
    db.session.commit()
    current = get_current_user()
    add_operation_log(current.id, current.username, 'add_user', 'user', new_user.id, f"新增用户: {new_user.username}")
    return APIUtils.success_response(message="用户添加成功")


# 修改用户
@blus.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.get_json()
    user = User.query.get(user_id)
    if not user:
        return APIUtils.error_response(message="用户不存在", code=404)
    if 'username' in data:
        if User.query.filter(User.username == data['username'], User.id != user_id).first():
            return APIUtils.error_response(message="用户名已存在", code=400)
        user.username = data['username']
    if 'role' in data:
        user.role = data['role']
    if 'status' in data:
        user.status = data['status']
    db.session.commit()
    current = get_current_user()
    add_operation_log(current.id, current.username, 'update_user', 'user', user_id, f"更新用户信息: {user.username}")
    return APIUtils.success_response(message="用户信息更新成功")


# ==================== 操作日志API ====================

@blus.route('/api/operation-logs', methods=['GET'])
def get_operation_logs():
    token = request.headers.get('token')
    if not token:
        return APIUtils.error_auth(message="请先登录", code=401)
    token_row = Token.query.filter_by(token=token).first()
    if not token_row or token_row.expires_at < datetime.utcnow():
        return APIUtils.error_auth(message="登录已过期", code=401)

    try:
        user = User.query.get(token_row.user_id)
        # ⭐ 权限：仅管理员可查看操作日志
        if user.role != 0:
            return APIUtils.error_auth(message="权限不足，仅管理员可查看操作日志", code=403)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('limit', 10, type=int)
        username = request.args.get('username', type=str)
        action = request.args.get('action', type=str)
        
        query = OperationLog.query
        # 普通用户只能查看自己的日志
        if user.role != 0:
            query = query.filter_by(user_id=user.id)
        if username:
            query = query.filter(OperationLog.username.like(f'%{username}%'))
        if action:
            query = query.filter_by(action=action)
        
        logs_pagination = query.order_by(OperationLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs_list = []
        for log in logs_pagination.items:
            logs_list.append({
                'id': log.id,
                'user_id': log.user_id,
                'username': log.username,
                'action': log.action,
                'target_type': log.target_type,
                'target_id': log.target_id,
                'detail': log.detail,
                'ip_address': log.ip_address,
                'created_at': log.created_at.isoformat() if log.created_at else None
            })
        
        return APIUtils.success_response(data={
            'list': logs_list,
            'page': {
                'total': logs_pagination.total,
                'page': logs_pagination.page,
                'limit': logs_pagination.per_page
            }
        })
    except Exception as e:
        return APIUtils.error_response(message=f"获取日志失败: {str(e)}")


@blus.route('/api/operation-logs/actions', methods=['GET'])
def get_log_actions():
    """获取所有操作类型列表"""
    token = request.headers.get('token')
    if not token:
        return APIUtils.error_auth(message="请先登录", code=401)
    token_row = Token.query.filter_by(token=token).first()
    if not token_row or token_row.expires_at < datetime.utcnow():
        return APIUtils.error_auth(message="登录已过期", code=401)
    
    try:
        user = User.query.get(token_row.user_id)
        if user.role != 0:
            return APIUtils.error_auth(message="权限不足", code=403)
        actions = db.session.query(OperationLog.action).distinct().all()
        action_list = [a[0] for a in actions if a[0]]
        return APIUtils.success_response(data=action_list)
    except Exception as e:
        return APIUtils.error_response(message=f"获取操作类型失败: {str(e)}")


# ==================== 文档处理相关API ====================

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 50 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in ['doc', 'docx']:
        return 'docx'
    return ext


# 文档上传
@blus.route('/api/document/upload', methods=['POST'])
@active_user_required
def upload_document():
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    user_id = token_row.user_id
    user = User.query.get(user_id)
    
    if 'file' not in request.files:
        return APIUtils.error_response(message="没有文件")
    
    file = request.files['file']
    if file.filename == '':
        return APIUtils.error_response(message="文件名为空")
    
    if not allowed_file(file.filename):
        return APIUtils.error_response(message="不支持的文件格式")
    
    try:
        filename = secure_filename(file.filename)
        import uuid
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            os.remove(file_path)
            return APIUtils.error_response(message="文件大小超过限制")
        
        file_type = get_file_type(filename)
        
        document = Document(
            user_id=user_id,
            filename=unique_filename,
            original_filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            status='uploaded'
        )
        db.session.add(document)
        db.session.commit()
        
        add_operation_log(user_id, user.username, 'upload_document', 'document', document.id, 
                         f"上传文档: {filename}, 大小: {file_size} bytes")
        
        return APIUtils.success_response(
            data={
                'id': document.id,
                'filename': filename,
                'file_type': file_type,
                'file_size': file_size
            },
            message="上传成功"
        )
    except Exception as e:
        return APIUtils.error_response(message=f"上传失败: {str(e)}")


# 文档列表
@blus.route('/api/document/list', methods=['GET'])
@active_user_required
def get_document_list():
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    user_id = token_row.user_id
    user = User.query.get(user_id)
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    try:
        query = Document.query.filter_by(user_id=user_id).order_by(Document.created_at.desc())
        total = query.count()
        documents = query.offset((page - 1) * limit).limit(limit).all()
        
        result = []
        for doc in documents:
            result.append({
                'id': doc.id,
                'original_filename': doc.original_filename,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                'status': doc.status,
                'created_at': doc.created_at.isoformat() if doc.created_at else None
            })
        
        return APIUtils.success_response(data={
            'list': result,
            'total': total,
            'page': page,
            'limit': limit
        })
    except Exception as e:
        return APIUtils.error_response(message=f"获取列表失败: {str(e)}")


# 解析文档
@blus.route('/api/document/<int:doc_id>/parse', methods=['POST'])
@active_user_required
def parse_document_api(doc_id):
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    user = User.query.get(token_row.user_id)
    
    try:
        document = Document.query.filter_by(id=doc_id, user_id=token_row.user_id).first()
        if not document:
            return APIUtils.error_response(message="文档不存在", status_code=404)
        
        content = parse_document(document.file_path, document.file_type)
        if content is None:
            document.status = 'error'
            db.session.commit()
            return APIUtils.error_response(message="文档解析失败")
        
        document.content = content
        document.status = 'parsed'
        db.session.commit()
        
        add_operation_log(token_row.user_id, user.username, 'parse_document', 'document', doc_id,
                         f"解析文档: {document.original_filename}, 内容长度: {len(content)}")
        
        return APIUtils.success_response(
            data={'content_length': len(content)},
            message="解析成功"
        )
    except Exception as e:
        return APIUtils.error_response(message=f"解析失败: {str(e)}")


# 获取文档内容
@blus.route('/api/document/<int:doc_id>/content', methods=['GET'])
@active_user_required
def get_document_content(doc_id):
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    
    try:
        document = Document.query.filter_by(id=doc_id, user_id=token_row.user_id).first()
        if not document:
            return APIUtils.error_response(message="文档不存在", status_code=404)
        
        if not document.content:
            return APIUtils.error_response(message="文档尚未解析")
        
        return APIUtils.success_response(data={'content': document.content})
    except Exception as e:
        return APIUtils.error_response(message=f"获取内容失败: {str(e)}")


# 删除文档
@blus.route('/api/document/<int:doc_id>', methods=['DELETE'])
@active_user_required
def delete_document(doc_id):
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    user = User.query.get(token_row.user_id)
    
    try:
        document = Document.query.filter_by(id=doc_id, user_id=token_row.user_id).first()
        if not document:
            return APIUtils.error_response(message="文档不存在", status_code=404)
        
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        db.session.delete(document)
        db.session.commit()
        
        add_operation_log(token_row.user_id, user.username, 'delete_document', 'document', doc_id,
                         f"删除文档: {document.original_filename}")
        
        return APIUtils.success_response(message="删除成功")
    except Exception as e:
        return APIUtils.error_response(message=f"删除失败: {str(e)}")


# 获取统计信息
@blus.route('/api/document/stats', methods=['GET'])
@active_user_required
def get_document_stats():
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    
    try:
        user_id = token_row.user_id
        total_documents = Document.query.filter_by(user_id=user_id).count()
        processed_documents = Document.query.filter_by(user_id=user_id, status='processed').count()
        total_tasks = ProcessTask.query.filter_by(user_id=user_id).count()
        
        documents = Document.query.filter_by(user_id=user_id).all()
        total_size = sum(doc.file_size for doc in documents)
        
        return APIUtils.success_response(data={
            'total_documents': total_documents,
            'processed_documents': processed_documents,
            'total_tasks': total_tasks,
            'total_size': total_size
        })
    except Exception as e:
        return APIUtils.error_response(message=f"获取统计失败: {str(e)}")


# 获取最近文档
@blus.route('/api/document/recent', methods=['GET'])
@active_user_required
def get_recent_documents():
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    
    try:
        user_id = token_row.user_id
        limit = request.args.get('limit', 5, type=int)
        
        documents = Document.query.filter_by(user_id=user_id)\
            .order_by(Document.created_at.desc())\
            .limit(limit).all()
        
        result = []
        for doc in documents:
            result.append({
                'id': doc.id,
                'original_filename': doc.original_filename,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                'status': doc.status,
                'created_at': doc.created_at.isoformat() if doc.created_at else None
            })
        
        return APIUtils.success_response(data=result)
    except Exception as e:
        return APIUtils.error_response(message=f"获取最近文档失败: {str(e)}")


# 获取任务统计
@blus.route('/api/task/stats', methods=['GET'])
@active_user_required
def get_task_stats():
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    
    try:
        user_id = token_row.user_id
        tasks = ProcessTask.query.filter_by(user_id=user_id).all()
        
        task_types = {}
        for task in tasks:
            task_type = task.task_type
            task_types[task_type] = task_types.get(task_type, 0) + 1
        
        return APIUtils.success_response(data={
            'task_types': list(task_types.keys()),
            'task_counts': list(task_types.values())
        })
    except Exception as e:
        return APIUtils.error_response(message=f"获取任务统计失败: {str(e)}")


# ==================== 文本预处理核心功能 ====================

# # 常用错别字映射（简化版）
# COMMON_ERRORS = {
#     '的': '地得',
#     '在': '再',
#     '做': '作',
#     '已': '以',
#     '象': '像',
#     '带': '戴',
#     '练': '炼',
#     '绝': '决',
#     '折': '拆',
#     '扑': '仆',
#     '蓝': '篮',
#     '辛': '幸',
# }

def load_stopwords():
    """加载停用词"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    stopwords_file = os.path.join(base_dir, 'utils', 'stopwords.txt')
    stopwords = set()
    if os.path.exists(stopwords_file):
        with open(stopwords_file, encoding='utf-8') as f:
            for line in f:
                w = line.strip()
                if w:
                    stopwords.add(w)
    return stopwords

def detect_and_remove_headers_footers(text):
    """检测并移除页眉页脚"""
    lines = text.split('\n')
    if len(lines) < 10:
        return text
    
    # 检测页眉：前几行中重复出现的内容
    header_candidates = Counter()
    footer_candidates = Counter()
    
    sample_size = min(20, len(lines) // 3)
    for line in lines[:sample_size]:
        stripped = line.strip()
        if stripped and len(stripped) < 100:
            header_candidates[stripped] += 1
    
    for line in lines[-sample_size:]:
        stripped = line.strip()
        if stripped and len(stripped) < 100:
            footer_candidates[stripped] += 1
    
    # 如果某行在开头/结尾出现超过3次，认为是页眉/页脚
    headers = {item for item, count in header_candidates.items() if count >= 3}
    footers = {item for item, count in footer_candidates.items() if count >= 3}
    
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped in headers or stripped in footers:
            continue
        # 移除页码模式
        if re.match(r'^\s*\d+\s*$', stripped) and len(stripped) < 5:
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def remove_garbage_chars(text):
    """移除乱码和特殊符号"""
    # 移除非中文、非英文、非数字、非标点的基础乱码
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # 移除过多的连续特殊符号
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\n，。！？、；：""''（）《》【】…—\.\,\!\?\;\:\(\)\[\]]{3,}', ' ', text)
    # 移除重复的空白字符
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def remove_duplicate_paragraphs(text, similarity_threshold=0.85):
    """段落去重"""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    unique_paragraphs = []
    seen_hashes = set()
    
    for para in paragraphs:
        # 使用SimHash的简单版本：字符集合哈希
        char_set = frozenset(para)
        if char_set not in seen_hashes:
            # 进一步检查与已有段落的相似度
            is_duplicate = False
            for existing in unique_paragraphs[-20:]:  # 只检查最近的20个
                if _text_similarity(para, existing) > similarity_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                seen_hashes.add(char_set)
                unique_paragraphs.append(para)
    
    return '\n'.join(unique_paragraphs)

def _text_similarity(a, b):
    """计算两段文本的Jaccard相似度"""
    if not a or not b:
        return 0.0
    set_a = set(a)
    set_b = set(b)
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0

# ============ 真正的分词纠错（基于词典 + 拼音相似 + 自定义词典） ============
# 这是一个简化但真实的纠错实现：
# 1. 用 jieba 分词
# 2. 对每个词，若不在常用词典且长度=2，尝试通过拼音相似找候选
# 3. 维护一个用户可扩展的错词→正词映射

# 项目级错词词典（可扩展，建议外置到 utils/typo_dict.txt）
def load_typo_dict():
    """从 utils/typo_dict.txt 加载错词词典，每行格式：错词\t正词"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dict_file = os.path.join(base_dir, 'utils', 'typo_dict.txt')
    typo_map = {}
    if os.path.exists(dict_file):
        with open(dict_file, encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    typo_map[parts[0]] = parts[1]
    # 兜底默认
    if not typo_map:
        typo_map = {
            '帐号': '账号', '帐户': '账户', '登陆': '登录',
            '在做': '再做', '做为': '作为', '即然': '既然',
            '黏贴': '粘贴', '震憾': '震撼', '气慨': '气概',
            '渡假': '度假', '迫不急待': '迫不及待',
        }
    return typo_map


def correct_words(text, log_collector=None):
    """真正的分词纠错：基于错词词典扫描，返回纠错后文本和纠错明细"""
    typo_map = load_typo_dict()
    corrections = []  # [{'wrong': 'xx', 'right': 'yy', 'position': 12}, ...]
    corrected_text = text
    for wrong, right in typo_map.items():
        # 找到所有出现位置
        start = 0
        while True:
            pos = corrected_text.find(wrong, start)
            if pos == -1:
                break
            corrections.append({'wrong': wrong, 'right': right, 'position': pos})
            start = pos + len(wrong)
        corrected_text = corrected_text.replace(wrong, right)

    if log_collector is not None:
        log_collector.append({
            'step': 'correct_words',
            'name': '分词纠错',
            'detail': f'扫描到 {len(corrections)} 处错词',
            'corrections': corrections[:20],  # 只返回前 20 条
        })

    # 用 jieba 分词
    words = list(jieba.cut(corrected_text))
    return corrected_text, words, corrections


def preprocess_text(text, config=None):
    """完整的文本预处理流程，每一步都记录处理日志"""
    if config is None:
        config = {}

    # 处理日志收集器（用于前端可视化）
    process_logs = []

    result = {
        'original_length': len(text),
        'cleaned_text': text,
        'segmented_words': [],
        'corrected_text': '',
        'corrections': [],  # 纠错明细
        'pos_tags': [],
        'process_logs': process_logs,  # 关键：处理过程日志
        'stats': {}
    }

    process_logs.append({
        'step': 'init', 'name': '开始预处理',
        'detail': f'原始文本长度 {len(text)} 字符', 'timestamp': datetime.utcnow().isoformat()
    })

    # 1. 噪声过滤 - 页眉页脚（先做，因为依赖换行）
    if config.get('remove_headers_footers', True):
        before = len(text)
        text = detect_and_remove_headers_footers(text)
        process_logs.append({
            'step': 'remove_headers_footers', 'name': '页眉页脚过滤',
            'detail': f'文本长度 {before} → {len(text)}（减少 {before - len(text)} 字符）',
            'timestamp': datetime.utcnow().isoformat()
        })

    # 2. ⭐ 新增：URL/邮箱/HTML标签 清洗（在乱码过滤之前，否则会被乱码过滤误删）
    if config.get('remove_urls', False):
        before = len(text)
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        text = re.sub(r'<[^>]+>', '', text)  # HTML标签
        process_logs.append({
            'step': 'remove_urls', 'name': 'URL/HTML标签清理',
            'detail': f'清理 {before - len(text)} 字符',
            'timestamp': datetime.utcnow().isoformat()
        })

    # 3. ⭐ 新增：全角→半角、繁简转换
    if config.get('normalize_chars', False):
        before_sample = text[:50]
        # 全角转半角
        new_text = ''
        for ch in text:
            code = ord(ch)
            if code == 0x3000:
                code = 0x0020
            elif 0xFF01 <= code <= 0xFF5E:
                code -= 0xFEE0
            new_text += chr(code)
        text = new_text
        process_logs.append({
            'step': 'normalize_chars', 'name': '字符规范化',
            'detail': '全角符号已转半角',
            'timestamp': datetime.utcnow().isoformat()
        })

    # 4. 噪声过滤 - 乱码和特殊符号
    if config.get('remove_garbage', True):
        before = len(text)
        text = remove_garbage_chars(text)
        process_logs.append({
            'step': 'remove_garbage', 'name': '乱码/特殊符号过滤',
            'detail': f'清理 {before - len(text)} 字符',
            'timestamp': datetime.utcnow().isoformat()
        })

    # 5. 去重清洗
    if config.get('remove_duplicates', True):
        before_paragraphs = len([p for p in text.split('\n') if p.strip()])
        text = remove_duplicate_paragraphs(text)
        after_paragraphs = len([p for p in text.split('\n') if p.strip()])
        process_logs.append({
            'step': 'remove_duplicates', 'name': '段落去重清洗',
            'detail': f'段落数 {before_paragraphs} → {after_paragraphs}（去除 {before_paragraphs - after_paragraphs} 个重复段）',
            'timestamp': datetime.utcnow().isoformat()
        })

    # 6. ⭐ 新增：短行/空行过滤
    if config.get('remove_short_lines', False):
        min_line_length = config.get('min_line_length', 5)
        before = text
        lines = [line for line in text.split('\n') if len(line.strip()) >= min_line_length]
        text = '\n'.join(lines)
        process_logs.append({
            'step': 'remove_short_lines', 'name': '短行过滤',
            'detail': f'移除长度<{min_line_length}的行',
            'timestamp': datetime.utcnow().isoformat()
        })

    result['cleaned_text'] = text
    result['stats']['cleaned_length'] = len(text)

    # 7. 分词纠错（独立开关，不再嵌套在分词内）
    corrected_text = text
    corrections = []
    if config.get('enable_correction', True):
        corrected_text, _, corrections = correct_words(text, process_logs)
        result['corrected_text'] = corrected_text[:1000] + ('...' if len(corrected_text) > 1000 else '')
        result['corrections'] = corrections

    # 8. 中文分词
    if config.get('enable_segmentation', True):
        words = list(jieba.cut(corrected_text))
        process_logs.append({
            'step': 'segmentation', 'name': '中文分词',
            'detail': f'分词得到 {len(words)} 个词',
            'timestamp': datetime.utcnow().isoformat()
        })

        # 9. 去除停用词
        if config.get('remove_stopwords', True):
            stopwords = load_stopwords()
            before_count = len(words)
            words = [w for w in words if w.strip() and w not in stopwords and len(w) > 1]
            process_logs.append({
                'step': 'remove_stopwords', 'name': '停用词过滤',
                'detail': f'词数 {before_count} → {len(words)}（过滤 {before_count - len(words)} 个停用词）',
                'timestamp': datetime.utcnow().isoformat()
            })

        result['segmented_words'] = words[:1000]
        result['stats']['total_words'] = len(words)
        result['stats']['unique_words'] = len(set(words))

    # 10. 词性标注
    if config.get('pos_tagging', False):
        import jieba.posseg as pseg
        pos_words = list(pseg.cut(corrected_text))
        if config.get('remove_stopwords', True):
            stopwords = load_stopwords()
            pos_words = [(w.word, w.flag) for w in pos_words if w.word not in stopwords and len(w.word) > 1]
        result['pos_tags'] = [{'word': w[0], 'pos': w[1]} for w in pos_words[:500]]
        process_logs.append({
            'step': 'pos_tagging', 'name': '词性标注',
            'detail': f'标注 {len(result["pos_tags"])} 个词的词性',
            'timestamp': datetime.utcnow().isoformat()
        })

    # 11. 正则匹配
    regex_pattern = config.get('regex_pattern', '')
    if regex_pattern:
        try:
            matches = re.findall(regex_pattern, text)
            result['regex_matches'] = matches[:100]
            result['stats']['regex_matches_count'] = len(matches)
            process_logs.append({
                'step': 'regex', 'name': '正则匹配',
                'detail': f'正则 "{regex_pattern}" 匹配到 {len(matches)} 处',
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            result['regex_matches'] = []
            process_logs.append({
                'step': 'regex', 'name': '正则匹配',
                'detail': f'正则错误: {e}',
                'timestamp': datetime.utcnow().isoformat()
            })

    result['stats']['reduction_ratio'] = round(
        (1 - len(text) / max(result['original_length'], 1)) * 100, 2
    ) if result['original_length'] > 0 else 0

    process_logs.append({
        'step': 'done', 'name': '预处理完成',
        'detail': f'最终长度 {len(text)}，压缩比 {result["stats"]["reduction_ratio"]}%',
        'timestamp': datetime.utcnow().isoformat()
    })

    return result


def preprocess_single_document(document_id, user_id, config):
    """单个文档预处理的辅助函数（用于多线程） - 纯文本处理，不涉及数据库"""
    return None  # 已废弃，使用主线程处理数据库


# 文本预处理（支持单文档和多线程批量）
@blus.route('/api/text/preprocess', methods=['POST'])
@active_user_required
def text_preprocess():
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    user = User.query.get(token_row.user_id)
    
    try:
        data = request.get_json()
        document_ids = data.get('document_ids', [])
        single_id = data.get('document_id')
        config = data.get('config', {})
        
        if single_id and not document_ids:
            document_ids = [single_id]
        
        if not document_ids:
            return APIUtils.error_response(message="请选择要处理的文档", status_code=400)
        
        # 验证所有文档是否存在
        documents = Document.query.filter(
            Document.id.in_(document_ids),
            Document.user_id == token_row.user_id
        ).all()
        
        if len(documents) != len(document_ids):
            return APIUtils.error_response(message="部分文档不存在或无权限访问", status_code=404)
        
        # 自动解析未解析的文档（主线程操作）
        for doc in documents:
            if not doc.content:
                content = parse_document(doc.file_path, doc.file_type)
                if content:
                    doc.content = content
                    doc.status = 'parsed'
                    db.session.commit()
        
        results = []
        
        # 多线程批量处理：线程只处理纯文本，数据库操作在主线程
        with ThreadPoolExecutor(max_workers=min(len(documents), 4)) as executor:
            future_map = {}
            for doc in documents:
                future = executor.submit(preprocess_text, doc.content, config)
                future_map[future] = doc
            
            for future in as_completed(future_map):
                doc = future_map[future]
                try:
                    result = future.result()
                    # 数据库操作在主线程执行
                    doc.status = 'processed'
                    db.session.commit()
                    
                    task = ProcessTask(
                        document_id=doc.id,
                        user_id=token_row.user_id,
                        task_type='preprocess',
                        status='completed',
                        config=json.dumps(config, ensure_ascii=False),
                        result=json.dumps(result, ensure_ascii=False, default=str)
                    )
                    db.session.add(task)
                    db.session.commit()
                    
                    results.append({
                        'document_id': doc.id,
                        'filename': doc.original_filename,
                        'status': 'success',
                        'message': '预处理完成',
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'document_id': doc.id,
                        'filename': doc.original_filename,
                        'status': 'failed',
                        'message': str(e)
                    })
        
        add_operation_log(token_row.user_id, user.username, 'preprocess', 'document', 
                         document_ids[0] if len(document_ids) == 1 else None,
                         f"文本预处理: 处理了{len(document_ids)}个文档")
        
        return APIUtils.success_response(
            data={'results': results, 'total': len(results), 'success_count': sum(1 for r in results if r['status'] == 'success')},
            message=f"预处理完成，成功处理 {sum(1 for r in results if r['status'] == 'success')}/{len(results)} 个文档"
        )
    except Exception as e:
        db.session.rollback()
        return APIUtils.error_response(message=f"预处理失败: {str(e)}")


# ==================== TextRank抽取式摘要核心算法 ====================

def split_sentences(text):
    """将文本拆分成句子"""
    # 中文句子结束符
    sentence_endings = re.compile(r'([。！？\n；]+)')
    parts = sentence_endings.split(text)
    sentences = []
    current = ''
    for part in parts:
        current += part
        if sentence_endings.match(part):
            stripped = current.strip()
            if stripped and len(stripped) > 5:
                sentences.append(stripped)
            current = ''
    if current.strip() and len(current.strip()) > 5:
        sentences.append(current.strip())
    return sentences

def sentence_similarity(sent1, sent2):
    """计算两个句子的相似度（基于共现词）"""
    import jieba
    words1 = set(jieba.cut(sent1))
    words2 = set(jieba.cut(sent2))
    words1 = {w for w in words1 if len(w) > 1}
    words2 = {w for w in words2 if len(w) > 1}
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    return len(intersection) / (math.log(len(words1) + 1) + math.log(len(words2) + 1))


def split_sentences(text):
    """将文本拆分成句子（修复版：不依赖换行符）"""
    # 中文+英文句子结束符
    sentence_endings = re.compile(r'([。！？!?；;]+)')
    parts = sentence_endings.split(text)
    sentences = []
    current = ''
    for part in parts:
        current += part
        if sentence_endings.match(part):
            stripped = current.strip()
            # 过滤过短和过长（异常）的句子
            if 5 <= len(stripped) <= 500:
                sentences.append(stripped)
            current = ''
    if current.strip() and 5 <= len(current.strip()) <= 500:
        sentences.append(current.strip())
    return sentences


def textrank_summary(text, summary_length=200, damping=0.85, iterations=30):
    """
    TextRank抽取式摘要（修复版）：
    - 预先分词（避免 O(n²) 重复分词）
    - 句子选择支持"刚好接近目标长度"
    - 返回详细元信息便于前端验证算法确实运行
    """
    import jieba

    # 1. 预处理（注意顺序：先去重、再去乱码，最后保留分句符号）
    text = detect_and_remove_headers_footers(text)
    text = remove_duplicate_paragraphs(text)
    # ⚠️ 不在这里调 remove_garbage_chars，因为它会破坏句末标点

    # 2. 分句
    sentences = split_sentences(text)

    meta = {
        'algorithm': 'TextRank-Sentence',
        'total_sentences': len(sentences),
        'damping': damping,
        'iterations': iterations,
        'target_length': summary_length,
    }

    if len(sentences) <= 2:
        return {
            'summary': ''.join(sentences) if sentences else text[:summary_length],
            'selected_indices': list(range(len(sentences))),
            'sentence_scores': [1.0] * len(sentences),
            'meta': {**meta, 'note': '句子数过少，未运行 TextRank'}
        }

    # 3. 预先分词（每句一次，避免 O(n²) 分词）
    sentence_words = []
    for s in sentences:
        ws = {w for w in jieba.cut(s) if len(w) > 1}
        sentence_words.append(ws)

    # 4. 构建相似度矩阵
    n = len(sentences)
    sim_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            wi, wj = sentence_words[i], sentence_words[j]
            if not wi or not wj:
                continue
            inter = len(wi & wj)
            denom = math.log(len(wi) + 1) + math.log(len(wj) + 1)
            sim = inter / denom if denom > 0 else 0.0
            sim_matrix[i][j] = sim
            sim_matrix[j][i] = sim

    # 5. TextRank 迭代
    scores = [1.0] * n
    out_sums = [sum(sim_matrix[j]) for j in range(n)]
    for _ in range(iterations):
        new_scores = [0.0] * n
        for i in range(n):
            summation = 0.0
            for j in range(n):
                if i != j and out_sums[j] > 0:
                    summation += sim_matrix[j][i] / out_sums[j] * scores[j]
            new_scores[i] = (1 - damping) + damping * summation
        scores = new_scores

    # 6. 选句策略：按分数降序，达到目标长度的 ±10% 即停
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    selected_indices = []
    current_length = 0
    target_min = summary_length * 0.9
    target_max = summary_length * 1.1

    for idx, score in ranked:
        sent_len = len(sentences[idx])
        if current_length >= target_min:
            break
        if current_length + sent_len <= target_max:
            selected_indices.append(idx)
            current_length += sent_len

    # 至少选 1 句
    if not selected_indices:
        selected_indices = [ranked[0][0]]

    # 7. 按原文顺序输出
    selected_indices.sort()
    summary = ''.join(sentences[i] for i in selected_indices)

    return {
        'summary': summary,
        'selected_indices': selected_indices,
        'sentence_scores': [round(s, 4) for s in scores],
        'all_sentences': sentences,  # 让前端可以高亮被选中的句子
        'meta': {
            **meta,
            'selected_count': len(selected_indices),
            'actual_length': len(summary),
        }
    }


def extract_keywords_tfidf(text, top_k=20):
    """TF-IDF关键词提取"""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import jieba
        
        words = ' '.join(jieba.cut(text))
        vectorizer = TfidfVectorizer(max_features=top_k)
        tfidf_matrix = vectorizer.fit_transform([words])
        
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        keywords = [{'word': word, 'score': float(score)} 
                   for word, score in zip(feature_names, scores) if score > 0]
        keywords.sort(key=lambda x: x['score'], reverse=True)
        
        return keywords[:top_k]
    except Exception:
        import jieba.analyse
        keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
        return [{'word': kw[0], 'score': float(kw[1])} for kw in keywords]


def extract_keywords_textrank(text, top_k=20):
    """TextRank关键词提取"""
    try:
        import jieba.analyse
        keywords = jieba.analyse.textrank(text, topK=top_k, withWeight=True)
        return [{'word': kw[0], 'score': float(kw[1])} for kw in keywords]
    except Exception:
        return []


# 关键词与摘要生成
@blus.route('/api/keyword-summary/generate', methods=['POST'])
@active_user_required
def generate_keyword_summary():
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    user = User.query.get(token_row.user_id)
    
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        config = data.get('config', {})
        
        document = Document.query.filter_by(id=document_id, user_id=token_row.user_id).first()
        if not document:
            return APIUtils.error_response(message="文档不存在", status_code=404)
        
        if not document.content:
            return APIUtils.error_response(message="文档尚未解析")
        
        text = document.content
        
        # 预处理文本（过滤噪声）
        text = detect_and_remove_headers_footers(text)
        text = remove_garbage_chars(text)
        text = remove_duplicate_paragraphs(text)
        
        result = {}
        types = config.get('types', ['keyword'])
        
        # 生成关键词
        if 'keyword' in types:
            algorithm = config.get('keyword_algorithm', 'tfidf')
            keyword_count = config.get('keyword_count', 20)
            
            if algorithm == 'tfidf':
                keywords = extract_keywords_tfidf(text, keyword_count)
            else:
                keywords = extract_keywords_textrank(text, keyword_count)
            
            result['keywords'] = keywords
        
        # 生成摘要 - TextRank抽取式摘要
        if 'summary' in types:
            summary_length = config.get('summary_length', 200)
            summary_obj = textrank_summary(text, summary_length)
            # summary_obj 现在是字典，包含 summary/scores/meta
            result['summary'] = summary_obj['summary']
            result['summary_length_actual'] = len(summary_obj['summary'])
            result['summary_algorithm'] = 'textrank_sentence'
            result['summary_meta'] = summary_obj['meta']
            result['summary_sentence_scores'] = summary_obj['sentence_scores']
            result['summary_all_sentences'] = summary_obj['all_sentences']
            result['summary_selected_indices'] = summary_obj['selected_indices']
        
        # 保存结果
        task = ProcessTask(
            document_id=document_id,
            user_id=token_row.user_id,
            task_type='keyword_summary',
            status='completed',
            config=json.dumps(config, ensure_ascii=False),
            result=json.dumps(result, ensure_ascii=False, default=str)
        )
        db.session.add(task)
        db.session.flush()
        
        if 'keyword' in types and result.get('keywords'):
            for kw in result['keywords']:
                keyword_summary = KeywordSummary(
                    document_id=document_id,
                    task_id=task.id,
                    result_type='keyword',
                    algorithm=algorithm,
                    content=kw['word']
                )
                db.session.add(keyword_summary)
        
        if 'summary' in types and result.get('summary'):
            keyword_summary = KeywordSummary(
                document_id=document_id,
                task_id=task.id,
                result_type='summary',
                algorithm='textrank',
                content=result['summary']
            )
            db.session.add(keyword_summary)
        
        db.session.commit()
        
        add_operation_log(token_row.user_id, user.username, 'keyword_summary', 'document', document_id,
                         f"关键词摘要生成: {document.original_filename}, 类型: {','.join(types)}")
        
        return APIUtils.success_response(data={**result, 'task_id': task.id}, message="生成完成")
    except Exception as e:
        db.session.rollback()
        return APIUtils.error_response(message=f"生成失败: {str(e)}")


# 信息抽取
@blus.route('/api/extraction/extract', methods=['POST'])
@active_user_required
def extract_information():
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    user = User.query.get(token_row.user_id)
    
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        config = data.get('config', {})
        
        document = Document.query.filter_by(id=document_id, user_id=token_row.user_id).first()
        if not document:
            return APIUtils.error_response(message="文档不存在", status_code=404)
        
        if not document.content:
            return APIUtils.error_response(message="文档尚未解析")
        
        text = document.content
        extraction_type = config.get('extraction_type', 'both')
        fields = config.get('fields', [])
        
        extractions = []
        
        if extraction_type in ['rule', 'both']:
            rule_results = extract_by_rules(text, fields)
            extractions.extend(rule_results)
        
        if extraction_type in ['algorithm', 'both']:
            algo_results = extract_by_algorithm(text, fields)
            extractions.extend(algo_results)
        
        task = ProcessTask(
            document_id=document_id,
            user_id=token_row.user_id,
            task_type='extraction',
            status='completed',
            config=json.dumps(config, ensure_ascii=False),
            result=json.dumps(extractions, ensure_ascii=False, default=str)
        )
        db.session.add(task)
        db.session.flush()
        
        for ext in extractions:
            extraction_result = ExtractionResult(
                document_id=document_id,
                task_id=task.id,
                extraction_type=ext['extraction_type'],
                field_name=ext['field_name'],
                field_value=ext['field_value'],
                confidence=ext.get('confidence', 1.0)
            )
            db.session.add(extraction_result)
        
        db.session.commit()
        
        add_operation_log(token_row.user_id, user.username, 'extraction', 'document', document_id,
                         f"信息抽取: {document.original_filename}, 抽取{len(extractions)}条结果")
        
        return APIUtils.success_response(data={'extractions': extractions}, message="抽取完成")
    except Exception as e:
        db.session.rollback()
        return APIUtils.error_response(message=f"抽取失败: {str(e)}")


def extract_by_rules(text, fields):
    """基于规则的信息抽取"""
    results = []
    
    if 'date' in fields:
        date_pattern = r'\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?|\d{4}/\d{1,2}/\d{1,2}'
        dates = re.findall(date_pattern, text)
        for date in dates[:10]:
            results.append({
                'field_name': 'date',
                'field_value': date,
                'extraction_type': 'rule',
                'confidence': 0.9
            })
    
    if 'money' in fields:
        money_pattern = r'[\u00a5$]?\d+[.,]?\d*[万千百十]?[元块]?'
        moneys = re.findall(money_pattern, text)
        for money in moneys[:10]:
            results.append({
                'field_name': 'money',
                'field_value': money,
                'extraction_type': 'rule',
                'confidence': 0.8
            })
    
    if 'email' in fields:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        for email in emails[:10]:
            results.append({
                'field_name': 'email',
                'field_value': email,
                'extraction_type': 'rule',
                'confidence': 0.95
            })
    
    if 'phone' in fields:
        phone_pattern = r'1[3-9]\d{9}'
        phones = re.findall(phone_pattern, text)
        for phone in phones[:10]:
            results.append({
                'field_name': 'phone',
                'field_value': phone,
                'extraction_type': 'rule',
                'confidence': 0.95
            })
    
    return results


def extract_by_algorithm(text, fields):
    """基于算法的信息抽取"""
    results = []
    if 'person' in fields or 'organization' in fields or 'location' in fields:
        import jieba.posseg as pseg
        words = pseg.cut(text)
        for word, flag in words:
            if flag == 'nr' and 'person' in fields:
                results.append({
                    'field_name': 'person',
                    'field_value': word,
                    'extraction_type': 'algorithm',
                    'confidence': 0.7
                })
            elif flag == 'ns' and 'location' in fields:
                results.append({
                    'field_name': 'location',
                    'field_value': word,
                    'extraction_type': 'algorithm',
                    'confidence': 0.7
                })
            elif flag == 'nt' and 'organization' in fields:
                results.append({
                    'field_name': 'organization',
                    'field_value': word,
                    'extraction_type': 'algorithm',
                    'confidence': 0.7
                })
    
    # 去重
    seen = set()
    unique_results = []
    for r in results:
        key = (r['field_name'], r['field_value'])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)
    
    return unique_results[:20]


# 获取任务列表
@blus.route('/api/task/list', methods=['GET'])
@active_user_required
def get_task_list():
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    
    try:
        user_id = token_row.user_id
        document_id = request.args.get('document_id', type=int)
        task_type = request.args.get('task_type', type=str)
        
        query = ProcessTask.query.filter_by(user_id=user_id)
        if document_id:
            query = query.filter_by(document_id=document_id)
        if task_type:
            query = query.filter_by(task_type=task_type)
        
        tasks = query.order_by(ProcessTask.created_at.desc()).all()
        
        result = []
        for task in tasks:
            result.append({
                'id': task.id,
                'document_id': task.document_id,
                'task_type': task.task_type,
                'status': task.status,
                'result': task.result[:500] + ('...' if task.result and len(task.result) > 500 else '') if task.result else '',
                'created_at': task.created_at.isoformat() if task.created_at else None
            })
        
        return APIUtils.success_response(data=result)
    except Exception as e:
        return APIUtils.error_response(message=f"获取任务列表失败: {str(e)}")


# 获取任务结果
@blus.route('/api/task/<int:task_id>/result', methods=['GET'])
@active_user_required
def get_task_result(task_id):
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    
    try:
        task = ProcessTask.query.filter_by(id=task_id, user_id=token_row.user_id).first()
        if not task:
            return APIUtils.error_response(message="任务不存在", status_code=404)
        
        try:
            result_data = json.loads(task.result) if task.result else {}
        except:
            result_data = task.result
        
        return APIUtils.success_response(data=result_data)
    except Exception as e:
        return APIUtils.error_response(message=f"获取结果失败: {str(e)}")


# 导出结果（支持JSON/Excel/CSV）
@blus.route('/api/task/<int:task_id>/export', methods=['GET'])
@active_user_required
def export_task_result(task_id):
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    user = User.query.get(token_row.user_id)
    
    try:
        task = ProcessTask.query.filter_by(id=task_id, user_id=token_row.user_id).first()
        if not task:
            return APIUtils.error_response(message="任务不存在", status_code=404)
        
        format_type = request.args.get('format', 'json')
        
        try:
            result_data = json.loads(task.result) if task.result else {}
        except:
            result_data = task.result or {}
        
        # 获取文档信息
        document = Document.query.get(task.document_id)
        doc_name = document.original_filename if document else f"task_{task_id}"
        
        if format_type == 'json':
            response = make_response(json.dumps(result_data, ensure_ascii=False, indent=2))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename={doc_name}_result.json'
            
            add_operation_log(token_row.user_id, user.username, 'export', 'task', task_id,
                             f"导出JSON: {doc_name}")
            return response
        
        elif format_type == 'excel':
            try:
                import pandas as pd
                from io import BytesIO
                
                # 展平数据为DataFrame
                rows = []
                if isinstance(result_data, dict):
                    # 关键词
                    if 'keywords' in result_data and isinstance(result_data['keywords'], list):
                        for kw in result_data['keywords']:
                            rows.append({
                                '类型': '关键词',
                                '内容': kw.get('word', ''),
                                '分数': kw.get('score', ''),
                                '文档': doc_name
                            })
                    # 摘要
                    if 'summary' in result_data:
                        rows.append({
                            '类型': '摘要',
                            '内容': result_data['summary'],
                            '分数': '',
                            '文档': doc_name
                        })
                    # 抽取结果
                    if 'extractions' in result_data and isinstance(result_data['extractions'], list):
                        for ext in result_data['extractions']:
                            rows.append({
                                '类型': f"抽取-{ext.get('field_name', '')}",
                                '内容': ext.get('field_value', ''),
                                '分数': ext.get('confidence', ''),
                                '文档': doc_name
                            })
                    # 预处理结果
                    if 'segmented_words' in result_data:
                        rows.append({
                            '类型': '预处理-分词',
                            '内容': ', '.join(str(w) for w in result_data['segmented_words'][:50]),
                            '分数': '',
                            '文档': doc_name
                        })
                
                if not rows:
                    rows = [{'类型': '原始结果', '内容': str(result_data), '分数': '', '文档': doc_name}]
                
                df = pd.DataFrame(rows)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Result')
                
                output.seek(0)
                response = make_response(output.read())
                response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                response.headers['Content-Disposition'] = f'attachment; filename={doc_name}_result.xlsx'
                
                add_operation_log(token_row.user_id, user.username, 'export', 'task', task_id,
                                 f"导出Excel: {doc_name}")
                return response
            except ImportError:
                return APIUtils.error_response(message="pandas和openpyxl库未安装，无法导出Excel")
        
        elif format_type == 'csv':
            try:
                import pandas as pd
                from io import StringIO
                
                # 同样的展平逻辑
                rows = []
                if isinstance(result_data, dict):
                    if 'keywords' in result_data and isinstance(result_data['keywords'], list):
                        for kw in result_data['keywords']:
                            rows.append({
                                '类型': '关键词',
                                '内容': kw.get('word', ''),
                                '分数': kw.get('score', ''),
                                '文档': doc_name
                            })
                    if 'summary' in result_data:
                        rows.append({
                            '类型': '摘要',
                            '内容': result_data['summary'],
                            '分数': '',
                            '文档': doc_name
                        })
                    if 'extractions' in result_data and isinstance(result_data['extractions'], list):
                        for ext in result_data['extractions']:
                            rows.append({
                                '类型': f"抽取-{ext.get('field_name', '')}",
                                '内容': ext.get('field_value', ''),
                                '分数': ext.get('confidence', ''),
                                '文档': doc_name
                            })
                
                if not rows:
                    rows = [{'类型': '原始结果', '内容': str(result_data), '分数': '', '文档': doc_name}]
                
                df = pd.DataFrame(rows)
                output = StringIO()
                df.to_csv(output, index=False, encoding='utf-8-sig')
                csv_content = output.getvalue()
                
                response = make_response(csv_content)
                response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
                response.headers['Content-Disposition'] = f'attachment; filename={doc_name}_result.csv'
                
                add_operation_log(token_row.user_id, user.username, 'export', 'task', task_id,
                                 f"导出CSV: {doc_name}")
                return response
            except ImportError:
                return APIUtils.error_response(message="pandas库未安装，无法导出CSV")
        
        return APIUtils.error_response(message="不支持的导出格式")
    except Exception as e:
        return APIUtils.error_response(message=f"导出失败: {str(e)}")


@blus.route('/api/batch/process', methods=['POST'])
@active_user_required
def batch_process():
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    user = User.query.get(token_row.user_id)
    user_id = token_row.user_id

    try:
        data = request.get_json()
        config = data.get('config', {})
        types = config.get('types', [])
        document_ids = data.get('document_ids', [])

        if not types:
            return APIUtils.error_response(message="请选择至少一种处理类型")

        # 选择要处理的文档
        if document_ids:
            documents = Document.query.filter(
                Document.id.in_(document_ids),
                Document.user_id == user_id
            ).all()
        else:
            # 默认：处理本用户所有未处理过的文档
            documents = Document.query.filter_by(user_id=user_id) \
                .filter(Document.status.in_(['uploaded', 'parsed'])) \
                .order_by(Document.created_at.desc()).limit(50).all()

        if not documents:
            return APIUtils.error_response(message="没有可处理的文档，请先上传或选择文档")

        # 把 ORM 对象的数据提取成基础类型，避免在子线程使用 ORM
        doc_snapshots = [{
            'id': d.id,
            'filename': d.original_filename,
            'content': d.content,
            'file_path': d.file_path,
            'file_type': d.file_type,
        } for d in documents]

        # 多线程并发处理
        results = []
        max_workers = min(len(doc_snapshots), int(config.get('max_workers', 4)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_doc = {
                executor.submit(
                    _process_single_document,
                    snap['id'], snap['filename'], snap['content'],
                    snap['file_path'], snap['file_type'], types, config
                ): snap for snap in doc_snapshots
            }
            for future in as_completed(future_to_doc):
                snap = future_to_doc[future]
                try:
                    res = future.result(timeout=300)
                except Exception as e:
                    res = {
                        'document_id': snap['id'],
                        'filename': snap['filename'],
                        'status': 'failed',
                        'message': f'线程异常: {e}',
                    }
                results.append(res)

        # ⭐ 主线程统一写库（避免子线程接触 db.session）
        for res in results:
            if res['status'] != 'success':
                continue
            doc = Document.query.get(res['document_id'])
            if not doc:
                continue

            res_data = res.get('results', {})

            # 解析结果回写
            if 'parse' in res_data and res.get('parsed_content'):
                doc.content = res['parsed_content']
                doc.status = 'parsed'

            # 各任务类型写 ProcessTask
            type_map = {
                'preprocess': ('preprocess', 'preprocess'),
                'keyword_summary': ('keyword_summary', 'keyword_summary'),
                'extraction': ('extract', 'extraction'),
            }
            for result_key, (cfg_key, task_type) in type_map.items():
                if result_key in res_data:
                    sub_config = config.get(cfg_key, {})
                    task = ProcessTask(
                        document_id=doc.id,
                        user_id=user_id,
                        task_type=task_type,
                        status='completed',
                        config=json.dumps(sub_config, ensure_ascii=False),
                        result=json.dumps(res_data[result_key], ensure_ascii=False, default=str)
                    )
                    db.session.add(task)

            doc.status = 'processed'

        db.session.commit()

        success_count = sum(1 for r in results if r['status'] == 'success')
        add_operation_log(user_id, user.username, 'batch_process', 'document', None,
                          f"批量处理: {len(documents)}个文档, 成功{success_count}个")

        return APIUtils.success_response(
            data={'results': results, 'success_count': success_count, 'total': len(results)},
            message=f"批量处理完成，成功 {success_count}/{len(results)}"
        )
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return APIUtils.error_response(message=f"批量处理失败: {str(e)}")


def _process_single_document(doc_id, doc_filename, doc_content, doc_file_path,
                             doc_file_type, types, config):
    """
    批量处理单个文档 - 纯文本处理，不接触 ORM 对象。
    所有数据库写操作必须放回主线程。
    入参全部用基础类型传递，避免 SQLAlchemy 对象的会话绑定问题。
    """
    try:
        results = {}
        content = doc_content

        # 解析（如果还没解析）
        if 'parse' in types:
            if not content:
                content = parse_document(doc_file_path, doc_file_type)
                if content:
                    results['parse'] = content

        # 预处理
        if 'preprocess' in types and content:
            preprocess_config = config.get('preprocess', {})
            results['preprocess'] = preprocess_text(content, preprocess_config)

        # 关键词摘要
        if 'keyword_summary' in types and content:
            ks_config = config.get('keyword_summary', {})
            text = detect_and_remove_headers_footers(content)
            text = remove_duplicate_paragraphs(text)

            ks_result = {}
            if ks_config.get('keyword', True):
                algorithm = ks_config.get('keyword_algorithm', 'tfidf')
                count = ks_config.get('keyword_count', 20)
                if algorithm == 'tfidf':
                    ks_result['keywords'] = extract_keywords_tfidf(text, count)
                else:
                    ks_result['keywords'] = extract_keywords_textrank(text, count)

            if ks_config.get('summary', False):
                summary_length = ks_config.get('summary_length', 200)
                summary_obj = textrank_summary(text, summary_length)
                ks_result['summary'] = summary_obj['summary']
                ks_result['summary_length_actual'] = len(summary_obj['summary'])
                ks_result['summary_meta'] = summary_obj['meta']
                ks_result['summary_sentence_scores'] = summary_obj['sentence_scores']
                ks_result['summary_all_sentences'] = summary_obj.get('all_sentences', [])
                ks_result['summary_selected_indices'] = summary_obj['selected_indices']

            results['keyword_summary'] = ks_result

        # 信息抽取
        if 'extract' in types and content:
            ext_config = config.get('extraction', {})
            fields = ext_config.get('fields', [])
            extractions = []
            extractions.extend(extract_by_rules(content, fields))
            extractions.extend(extract_by_algorithm(content, fields))
            results['extraction'] = {'extractions': extractions}

        return {
            'document_id': doc_id,
            'filename': doc_filename,
            'status': 'success',
            'message': '处理成功',
            'results': results,
            'parsed_content': content if 'parse' in types and not doc_content else None,
        }
    except Exception as e:
        import traceback
        return {
            'document_id': doc_id,
            'filename': doc_filename,
            'status': 'failed',
            'message': str(e),
            'traceback': traceback.format_exc(),
        }


# ==================== 原有的词云和评论API（保留） ====================

@blus.route('/api/word', methods=['GET'])
def word():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        stopwords_file = os.path.join(base_dir, 'utils', 'stopwords.txt')
        stopwords = set()
        with open(stopwords_file, encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    stopwords.add(word)
        
        import pymysql
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = "SELECT title FROM tb_hot LIMIT 1000"
            cursor.execute(query)
            word_counts = {}
            for row in cursor.fetchall():
                job_desc = row['title']
                for word in jieba.cut(job_desc):
                    word = word.strip()
                    if word and word not in stopwords:
                        word_counts[word] = word_counts.get(word, 0) + 1
            result = [
                {"name": word, "value": count}
                for word, count in word_counts.items()
            ]
        return APIUtils.success_response(data=result)
    except Exception as err:
        return APIUtils.error_response(message=str(err))
    finally:
        try:
            connection.close()
        except:
            pass


@blus.route('/api/comment_wordcloud', methods=['GET'])
def comment_wordcloud():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        stopwords_file = os.path.join(base_dir, 'utils', 'stopwords.txt')
        stopwords = set()
        with open(stopwords_file, encoding='utf-8') as f:
            for line in f:
                w = line.strip()
                if w:
                    stopwords.add(w)
        
        import pymysql
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT content as text_raw FROM bili_food_comments WHERE content IS NOT NULL ")
            word_counts = {}
            for row in cursor.fetchall():
                text = row.get('text_raw') or ''
                for token in jieba.cut(text):
                    token = token.strip()
                    if token and token not in stopwords and len(token) > 1:
                        word_counts[token] = word_counts.get(token, 0) + 1
            result = [
                {"name": k, "value": v}
                for k, v in word_counts.items()
            ]
        return APIUtils.success_response(data=result)
    except Exception as err:
        return APIUtils.error_response(message=str(err))
    finally:
        try:
            connection.close()
        except:
            pass


@blus.route('/api/user_wordcloud', methods=['GET'])
def user_wordcloud():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        stopwords_file = os.path.join(base_dir, 'utils', 'stopwords.txt')
        stopwords = set()
        with open(stopwords_file, encoding='utf-8') as f:
            for line in f:
                w = line.strip()
                if w:
                    stopwords.add(w)
        
        import pymysql
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT user as text_raw FROM bili_food_comments WHERE user IS NOT NULL ")
            word_counts = {}
            for row in cursor.fetchall():
                text = row.get('text_raw') or ''
                for token in jieba.cut(text):
                    token = token.strip()
                    if token and token not in stopwords and len(token) > 1:
                        word_counts[token] = word_counts.get(token, 0) + 1
            result = [
                {"name": k, "value": v}
                for k, v in word_counts.items()
            ]
        return APIUtils.success_response(data=result)
    except Exception as err:
        return APIUtils.error_response(message=str(err))
    finally:
        try:
            connection.close()
        except:
            pass


@blus.route('/api/results/all', methods=['GET'])
@active_user_required
def get_all_results():
    """
    聚合所有处理结果，按文档分组返回，结果数据已展开（不需要再点查看）。
    支持筛选：document_id, task_type, keyword（搜索结果内容）
    """
    token = request.headers.get('token')
    token_row = Token.query.filter_by(token=token).first()
    user_id = token_row.user_id

    try:
        document_id = request.args.get('document_id', type=int)
        task_type = request.args.get('task_type', type=str)
        keyword = request.args.get('keyword', type=str)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)

        query = ProcessTask.query.filter_by(user_id=user_id, status='completed')
        if document_id:
            query = query.filter_by(document_id=document_id)
        if task_type:
            query = query.filter_by(task_type=task_type)

        total = query.count()
        tasks = query.order_by(ProcessTask.created_at.desc()) \
            .offset((page - 1) * limit).limit(limit).all()

        items = []
        for task in tasks:
            try:
                result_data = json.loads(task.result) if task.result else {}
            except Exception:
                result_data = {'raw': task.result}

            doc = Document.query.get(task.document_id)

            # 关键词关键词搜索过滤（在 Python 里做，避免复杂 SQL）
            if keyword:
                blob = json.dumps(result_data, ensure_ascii=False)
                if keyword not in blob and keyword not in (doc.original_filename if doc else ''):
                    continue

            items.append({
                'task_id': task.id,
                'document_id': task.document_id,
                'document_name': doc.original_filename if doc else '已删除',
                'task_type': task.task_type,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'result': result_data,  # ⭐ 直接返回完整结果，不需要再发请求
            })

        return APIUtils.success_response(data={
            'list': items,
            'total': total,
            'page': page,
            'limit': limit,
        })
    except Exception as e:
        return APIUtils.error_response(message=f"获取结果失败: {str(e)}")