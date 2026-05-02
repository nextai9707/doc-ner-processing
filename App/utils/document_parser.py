# 文档解析工具
import os
import re
from typing import Optional

def parse_txt(file_path: str) -> Optional[str]:
    """解析TXT文件"""
    try:
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    return content
            except UnicodeDecodeError:
                continue
        return None
    except Exception as e:
        print(f"解析TXT文件失败: {e}")
        return None

def parse_docx(file_path: str) -> Optional[str]:
    """解析Word文档"""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        return '\n'.join(paragraphs)
    except ImportError:
        print("python-docx库未安装，无法解析Word文档")
        return None
    except Exception as e:
        print(f"解析Word文档失败: {e}")
        return None

def parse_pdf(file_path: str) -> Optional[str]:
    """解析PDF文件"""
    try:
        import pdfplumber
        text_content = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        return '\n'.join(text_content)
    except ImportError:
        print("pdfplumber库未安装，无法解析PDF文档")
        return None
    except Exception as e:
        print(f"解析PDF文件失败: {e}")
        return None

def parse_document(file_path: str, file_type: str) -> Optional[str]:
    """根据文件类型解析文档"""
    file_type = file_type.lower()
    if file_type == 'txt':
        return parse_txt(file_path)
    elif file_type in ['doc', 'docx']:
        return parse_docx(file_path)
    elif file_type == 'pdf':
        return parse_pdf(file_path)
    else:
        return None

