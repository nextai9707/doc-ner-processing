# 模型
from datetime import datetime

from sqlalchemy.dialects.mysql import LONGTEXT

from .exts import db


# 模型
class User(db.Model):
    # 表名
    __tablename__ = "tb_user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role = db.Column(db.Integer, default=1)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    status = db.Column(db.Integer, default=1)  # 1-正常 0-禁用
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Config(db.Model):
    # 表名
    __tablename__ = "tb_sysconfig"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主键
    name = db.Column(db.String(50), nullable=False)
    key = db.Column(db.String(50), unique=True, nullable=False)  # 配置键
    value = db.Column(db.String(255), nullable=False)  # 配置值
    description = db.Column(db.String(255))  # 描述

class Token(db.Model):
    __tablename__ = 'tb_token'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    user = db.relationship(
        'User',
        backref=db.backref('tokens', lazy=True, cascade='all, delete-orphan')
    )

# 操作日志模型
class OperationLog(db.Model):
    __tablename__ = 'tb_operation_log'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # login, logout, preprocess, keyword_summary, extract, upload, delete, export, etc.
    target_type = db.Column(db.String(50))  # document, user, task, etc.
    target_id = db.Column(db.Integer)
    detail = db.Column(db.Text)  # 详细描述
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship('User', backref=db.backref('operation_logs', lazy=True, passive_deletes=True))

# 权限角色模型（简化版）
class Role(db.Model):
    __tablename__ = 'tb_role'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)  # admin, user
    description = db.Column(db.String(255))
    permissions = db.Column(db.Text)  # JSON格式权限列表
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 文档模型
class Document(db.Model):
    __tablename__ = 'tb_document'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # txt, docx, pdf
    file_size = db.Column(db.Integer, nullable=False)  # 字节数
    status = db.Column(db.String(20), default='uploaded')  # uploaded, parsed, processed, error
    content = db.Column(LONGTEXT)  # 解析后的文本内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('documents', lazy=True))

# 处理任务模型
class ProcessTask(db.Model):
    __tablename__ = 'tb_process_task'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_id = db.Column(db.Integer, db.ForeignKey('tb_document.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)  # preprocess, extract, keyword_summary, batch
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    config = db.Column(db.Text)  # JSON格式的配置
    result = db.Column(LONGTEXT)  # 处理结果
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    document = db.relationship(
        'Document',
        backref=db.backref('tasks', lazy=True, cascade='all, delete-orphan')
    )
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))

# 信息抽取结果模型
class ExtractionResult(db.Model):
    __tablename__ = 'tb_extraction_result'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_id = db.Column(db.Integer, db.ForeignKey('tb_document.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tb_process_task.id'), nullable=False)
    extraction_type = db.Column(db.String(50), nullable=False)  # rule, algorithm
    field_name = db.Column(db.String(100), nullable=False)  # 字段名
    field_value = db.Column(LONGTEXT)  # 字段值
    confidence = db.Column(db.Float)  # 置信度
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    document = db.relationship(
        'Document',
        backref=db.backref('extractions', lazy=True, cascade='all, delete-orphan')
    )
    task = db.relationship(
        'ProcessTask',
        backref=db.backref('extractions', lazy=True, cascade='all, delete-orphan')
    )

# 关键词和摘要结果模型
class KeywordSummary(db.Model):
    __tablename__ = 'tb_keyword_summary'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_id = db.Column(db.Integer, db.ForeignKey('tb_document.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tb_process_task.id'), nullable=False)
    result_type = db.Column(db.String(20), nullable=False)  # keyword, summary
    algorithm = db.Column(db.String(50))  # TF-IDF, TextRank
    content = db.Column(LONGTEXT)  # 关键词列表或摘要内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    document = db.relationship(
        'Document',
        backref=db.backref('keyword_summaries', lazy=True, cascade='all, delete-orphan')
    )
    task = db.relationship(
        'ProcessTask',
        backref=db.backref('keyword_summaries', lazy=True, cascade='all, delete-orphan')
    )
