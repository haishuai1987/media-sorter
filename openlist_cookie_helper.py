#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenList Cookie 获取助手
通过OpenList OAuth登录后提取115网盘Cookie
"""

import requests
import json
from typing import Optional, Tuple, Dict
from urllib.parse import urlencode


class OpenListCookieHelper:
    """通过OpenList OAuth流程获取115 Cookie"""
    
    # OpenList API配置
    OPENLIST_API = 'https://api.oplist.org.cn'
    
    # 115网盘配置
    CLOUD115_DRIVER = '115cloud'
    CLOUD115_TYPE = '115cloud_go'
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
    
    def get_login_url(self) -> Tuple[Optional[str], Optional[str]]:
        """获取OpenList登录URL
        
        Returns:
            (login_url, error)
        """
        try:
            # 构建请求参数
            params = {
                'driver': self.CLOUD115_DRIVER,
                'driver_txt': self.CLOUD115_TYPE,
                'server_use': 'true',  # 使用OpenList提供的应用ID
            }
            
            url = f'{self.OPENLIST_API}/{self.CLOUD115_DRIVER}/requests'
            
            print(f"[OpenList] 请求登录URL: {url}")
            print(f"[OpenList] 参数: {params}")
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # OpenList返回格式: {"text": "https://..."}
                login_url = data.get('text')
                
                if login_url:
                    print(f"[OpenList] 获取登录URL成功")
                    return login_url, None
                else:
                    error = data.get('message', '未返回登录URL')
                    print(f"[OpenList] 获取登录URL失败: {error}")
                    return None, error
            else:
                error = f"HTTP错误: {response.status_code}"
                print(f"[OpenList] 请求失败: {error}")
                return None, error
                
        except Exception as e:
            error = f"请求异常: {str(e)}"
            print(f"[OpenList] {error}")
            return None, error
    
    def extract_cookie_from_callback(self, callback_url: str) -> Tuple[Optional[str], Optional[str]]:
        """从回调URL中提取Cookie
        
        用户完成OpenList登录后，会被重定向到回调URL
        我们需要从这个过程中提取115的Cookie
        
        Args:
            callback_url: OpenList回调URL
        
        Returns:
            (cookie, error)
        """
        try:
            print(f"[OpenList] 处理回调URL")
            
            # 访问回调URL，跟踪重定向
            response = self.session.get(callback_url, allow_redirects=True, timeout=10)
            
            # 检查是否有115的Cookie
            cookies = self.session.cookies.get_dict()
            
            # 115网盘的关键Cookie字段
            required_cookies = ['UID', 'CID', 'SEID']
            
            has_all_cookies = all(key in cookies for key in required_cookies)
            
            if has_all_cookies:
                # 构建Cookie字符串
                cookie_str = '; '.join([f'{k}={v}' for k, v in cookies.items()])
                print(f"[OpenList] 成功提取Cookie")
                return cookie_str, None
            else:
                missing = [key for key in required_cookies if key not in cookies]
                error = f"缺少必要的Cookie字段: {missing}"
                print(f"[OpenList] {error}")
                print(f"[OpenList] 当前Cookie: {list(cookies.keys())}")
                return None, error
                
        except Exception as e:
            error = f"提取Cookie异常: {str(e)}"
            print(f"[OpenList] {error}")
            return None, error
    
    def verify_cookie(self, cookie: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """验证Cookie是否有效
        
        Args:
            cookie: Cookie字符串
        
        Returns:
            (success, user_info, error)
        """
        try:
            # 使用115的用户信息API验证
            url = 'https://my.115.com/?ct=ajax&ac=nav'
            
            headers = {
                'Cookie': cookie,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('state'):
                    user_info = data.get('data', {})
                    print(f"[OpenList] Cookie验证成功")
                    return True, user_info, None
                else:
                    error = data.get('error', 'Cookie无效')
                    print(f"[OpenList] Cookie验证失败: {error}")
                    return False, None, error
            else:
                error = f"HTTP错误: {response.status_code}"
                print(f"[OpenList] 验证失败: {error}")
                return False, None, error
                
        except Exception as e:
            error = f"验证异常: {str(e)}"
            print(f"[OpenList] {error}")
            return False, None, error


def test_openlist_cookie_flow():
    """测试OpenList Cookie获取流程"""
    print("="*60)
    print("OpenList Cookie 获取流程测试")
    print("="*60)
    
    helper = OpenListCookieHelper()
    
    # 步骤1: 获取登录URL
    print("\n步骤1: 获取登录URL")
    print("-"*60)
    login_url, error = helper.get_login_url()
    
    if error:
        print(f"❌ 失败: {error}")
        return
    
    print(f"✅ 登录URL: {login_url}")
    print()
    print("请在浏览器中打开此URL并完成登录")
    print("登录成功后，你会被重定向到一个回调URL")
    print()
    
    # 步骤2: 等待用户输入回调URL
    print("步骤2: 输入回调URL")
    print("-"*60)
    print("请将浏览器地址栏中的完整URL粘贴到这里:")
    callback_url = input("> ").strip()
    
    if not callback_url:
        print("❌ 未输入回调URL")
        return
    
    # 步骤3: 提取Cookie
    print("\n步骤3: 提取Cookie")
    print("-"*60)
    cookie, error = helper.extract_cookie_from_callback(callback_url)
    
    if error:
        print(f"❌ 失败: {error}")
        return
    
    print(f"✅ Cookie: {cookie[:100]}...")
    
    # 步骤4: 验证Cookie
    print("\n步骤4: 验证Cookie")
    print("-"*60)
    success, user_info, error = helper.verify_cookie(cookie)
    
    if success:
        print(f"✅ Cookie有效!")
        print(f"   用户信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
        
        # 保存Cookie到文件
        with open('115_cookie.txt', 'w') as f:
            f.write(cookie)
        print(f"\n✅ Cookie已保存到: 115_cookie.txt")
    else:
        print(f"❌ Cookie无效: {error}")


if __name__ == '__main__':
    test_openlist_cookie_flow()
