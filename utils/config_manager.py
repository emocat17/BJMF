"""
配置文件管理模块
负责读取和保存配置文件
"""

import json
import os


def load_config(config_file='data.json'):
    """
    加载配置文件
    
    Args:
        config_file (str): 配置文件名
        
    Returns:
        dict: 配置数据
    """
    try:
        if not os.path.exists(config_file):
            print(f"配置文件 {config_file} 不存在")
            return {}
            
        with open(config_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return {}


def save_config(config_data, config_file='data.json'):
    """
    保存配置数据到文件
    
    Args:
        config_data (dict): 要保存的配置数据
        config_file (str): 配置文件名
    """
    try:
        with open(config_file, 'w', encoding='utf-8') as file:
            json.dump(config_data, file, ensure_ascii=False, indent=4)
        print(f"配置文件 {config_file} 更新成功")
    except Exception as e:
        print(f"保存配置文件时出错: {e}")


def get_students(config_file='data.json'):
    """
    从配置文件中获取学生列表
    
    Args:
        config_file (str): 配置文件名
        
    Returns:
        list: 学生列表
    """
    config = load_config(config_file)
    return config.get('students', [])