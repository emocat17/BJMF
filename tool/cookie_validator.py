import requests
import re

def validate_cookie(headers):
    """
    验证cookie是否有效
    返回: (is_valid, user_info)
    is_valid: Boolean, 表示cookie是否有效
    user_info: Dict, 包含用户信息(name, student_id)或None
    """
    # 创建新的session确保无缓存
    session = requests.Session()
    session.headers.update(headers)
    
    # 访问个人页面
    profile_url = "https://bjmf.k8n.cn/student/my"
    
    try:
        response = session.get(profile_url, timeout=10)
        # 提取用户姓名和学号
        content = response.text
        
        # 查找姓名 (从JavaScript变量中提取)
        name_pattern = r'uname[\'"]?\s*:\s*[\'"]([^\'"]+)[\'"]'
        name_match = re.search(name_pattern, content)
        if not name_match:
            # 备用方案：从HTML中查找
            name_match = re.search(r'>([^<>\n\r]{2,4})\s*同学<', content)
        
        name = name_match.group(1).strip() if name_match else ""
        
        # 查找学号 (优先从HTML中查找正确的学号)
        # 首先尝试从用户信息区域查找学号 (在姓名下方的div中)
        id_pattern = r'<div class="font-weight-bold">[^<]+</div>\s*<div>(\d{9})</div>'
        id_match = re.search(id_pattern, content)
        
        # 如果没找到，尝试其他模式查找9位数字的学号
        if not id_match:
            id_pattern = r'(\d{9})'
            id_matches = re.findall(id_pattern, content)
            # 过滤掉可能的时间戳等非学号的9位数字
            valid_ids = [id for id in id_matches if not id.startswith(('1757596', '2024'))]
            if valid_ids:
                student_id = valid_ids[0]
            else:
                student_id = ""
        else:
            student_id = id_match.group(1).strip() if id_match else ""
        
        # 检查是否成功获取到用户信息
        # 以姓名是否返回的字段长度为空来判断cookie是否错误
        if len(name) == 0:
            return False, None
        
        user_info = {
            "name": name,
            "student_id": student_id
        }
        
        return True, user_info
            
    except requests.exceptions.RequestException as e:
        return False, None

def get_user_info(headers):
    """
    获取用户信息（兼容旧接口）
    返回用户信息字典或None
    """
    is_valid, user_info = validate_cookie(headers)
    return user_info if is_valid else None