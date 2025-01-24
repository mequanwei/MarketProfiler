import requests
from typing import Dict, Any

class ESIClient:
    def __init__(self, base_url: str, headers: Dict[str, str] = None):
        self.base_url = base_url.rstrip('/')  # 移除末尾斜杠以避免重复
        self.headers = headers or {}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送 GET 请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params)
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any] = None, json_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送 POST 请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, data=data, json=json_data)
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        return response.json()
    
    def get_system_id(self):
        return self.get('/universe/systems/')
    
    def get_system_info(self,id):
        return self.get(f'/universe/systems/{id}/')
    
    def get_industry_index(self):
        return self.get('/industry/systems/')

    def close(self):
        """关闭会话"""
        self.session.close()