from ..models import *
class ConfigManager:
    @staticmethod
    def get_value(key):
        """通过键获取配置值"""
        config = Config.query.filter_by(key=key).first()
        return config.value if config else None

    @staticmethod
    def add_config(name, key, value, description=None):
        """添加新的配置项"""
        if Config.query.filter_by(key=key).first():
            raise ValueError("配置键已存在！")
        new_config = Config(name=name, key=key, value=value, description=description)
        db.session.add(new_config)
        db.session.commit()

    @staticmethod
    def update_config(key, value):
        """更新配置项的值"""
        config = Config.query.filter_by(key=key).first()
        if not config:
            raise ValueError("配置项不存在！")

        config.value = value
        db.session.commit()

    @staticmethod
    def delete_config(key):
        """删除配置项"""
        config = Config.query.filter_by(key=key).first()
        if not config:
            raise ValueError("配置项不存在！")

        db.session.delete(config)
        db.session.commit()

    @staticmethod
    def get_file_path(key):

      return ""