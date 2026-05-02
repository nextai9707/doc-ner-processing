from flask import jsonify
# 统一返回接口
class APIUtils:

    @staticmethod
    def success_response(data=None, message="Success", status_code=200):
        """成功响应封装"""
        response = {
            'code': '200',
            'message': message,
            'data': data
        }
        return jsonify(response), status_code

    @staticmethod
    def error_response(message="Error", status_code=200):
        """错误响应封装"""
        response = {
            'code': '500',
            'msg': message
        }
        return jsonify(response), status_code
    @staticmethod
    def error_auth(message="Error", code=401):
        """错误响应封装"""
        response = {
            'code': code,
            'msg': message
        }
        return jsonify(response), code

    @staticmethod
    def validate_json(request_json, required_fields):
        """验证 JSON 请求体中是否包含所需字段"""
        missing_fields = [field for field in required_fields if field not in request_json]
        if missing_fields:
            return False, f'缺失字段: {", ".join(missing_fields)}'
        return True, ""

    @staticmethod
    def paginate(query, page, per_page):
        """分页处理"""
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return {
            'total': total,
            'items': items
        }



class CustomException(Exception):
    """自定义异常类，所有自定义异常应继承自此类"""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        """将异常信息转换为字典格式"""
        return {'error': self.message, 'status_code': self.status_code}
