from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw
import requests
import base64
import io
import json
import os
import zipfile
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 添加CORS支持
CORS(app)

# Supabase 配置（必须通过环境变量提供）
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]
try:
    # 直接创建客户端，不使用自定义HTTP客户端
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
except Exception as e:
    print(f"Supabase 初始化警告: {e}")
    # 尝试使用环境变量方式禁用SSL验证
    import os
    os.environ['CURL_CA_BUNDLE'] = ''  # 禁用SSL验证
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    except Exception as e2:
        print(f"Supabase 初始化第二次尝试失败: {e2}")
        supabase = None
        supabase_admin = None

# 从数据库获取 API 配置
def get_api_config():
    """从数据库获取 API 配置"""
    try:
        response = supabase_admin.table('api_config').select('*').order('created_at', desc=True).limit(1).execute()
        if response.data and len(response.data) > 0:
            return {
                "api_key": response.data[0]['api_key'],
                "api_url": response.data[0]['api_url'],
                "model": response.data[0]['model']
            }
    except Exception as e:
        print(f"获取 API 配置错误: {e}")
    # 默认配置
    return {
        "api_key": "sk-muDiVOc0MZmkpSWMLguFlJhmWRq4707fgKDTfMHSsMPctZxi",
        "api_url": "https://api.nofx.online/v1/chat/completions",
        "model": "gemini-3.1-flash-image-square"
    }

# 状态存储
current_image = None
current_image_bytes = None
current_coords = None
current_box_color = "#1677FF"
current_box_width = 3
generated_result = None

COLORS = [
    "#1677FF",
    "#52C41A",
    "#FAAD14",
    "#595959",
    "#FFFFFF",
    "#F5222D"
]

COLOR_NAMES = [
    "蓝色",
    "绿色",
    "橙色",
    "灰色",
    "白色",
    "红色"
]

WIDTHS = [3, 6, 10]
WIDTH_NAMES = ["细", "中", "粗"]

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>登录 / 注册</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Source+Serif+4:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');
        
        * {
            box-sizing: border-box;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Source Serif 4', Georgia, serif;
            background: #FFFFFF;
            color: #000000;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1000;
            background: repeating-linear-gradient(
                0deg,
                #000000 0px,
                #000000 1px,
                transparent 1px,
                transparent 8px
            );
            opacity: 0.015;
        }
        
        body::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1001;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
            opacity: 0.02;
        }
        
        .container {
            width: 100%;
            max-width: 480px;
            padding: 64px 48px;
            border: 2px solid #000000;
            position: relative;
            z-index: 1;
        }
        
        .header {
            text-align: center;
            margin-bottom: 48px;
            padding-bottom: 24px;
            border-bottom: 4px solid #000000;
        }
        
        h1 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 3rem;
            font-weight: 600;
            letter-spacing: -0.05em;
            line-height: 1;
            margin: 0 0 16px 0;
        }
        
        h2 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.75rem;
            font-weight: 600;
            letter-spacing: -0.025em;
            margin: 0 0 32px 0;
            text-align: center;
        }
        
        .tab-container {
            display: flex;
            margin-bottom: 32px;
            border-bottom: 2px solid #000000;
        }
        
        .tab {
            flex: 1;
            padding: 16px;
            text-align: center;
            cursor: pointer;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            transition: all 100ms ease;
            border-bottom: 4px solid transparent;
        }
        
        .tab.active {
            background: #000000;
            color: #FFFFFF;
            border-bottom: 4px solid #000000;
        }
        
        .tab:hover:not(.active) {
            background: #f0f0f0;
        }
        
        .form-group {
            margin-bottom: 24px;
        }
        
        label {
            display: block;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        
        input[type="email"],
        input[type="password"] {
            width: 100%;
            padding: 16px;
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 1rem;
            border: 2px solid #000000;
            border-radius: 0;
            background: #FFFFFF;
            color: #000000;
            transition: border-width 100ms ease;
        }
        
        input[type="email"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-width: 4px;
        }
        
        ::placeholder {
            color: #525252;
            font-style: italic;
        }
        
        button {
            width: 100%;
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            padding: 16px 32px;
            background: #000000;
            color: #FFFFFF;
            border: none;
            border-radius: 0;
            cursor: pointer;
            margin-top: 8px;
            transition: all 100ms ease;
        }
        
        button:hover {
            background: #FFFFFF;
            color: #000000;
            border: 2px solid #000000;
            padding: 14px 30px;
        }
        
        .error {
            background: #000000;
            color: #FFFFFF;
            padding: 16px;
            margin-bottom: 24px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            letter-spacing: 0.05em;
        }
        
        .success {
            background: #000000;
            color: #FFFFFF;
            padding: 16px;
            margin-bottom: 24px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            letter-spacing: 0.05em;
        }
        
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>图片编辑</h1>
        </div>
        
        <div id="errorMessage" class="error hidden"></div>
        <div id="successMessage" class="success hidden"></div>
        
        <div class="tab-container">
            <div class="tab active" onclick="switchTab('login')">登录</div>
            <div class="tab" onclick="switchTab('register')">注册</div>
        </div>
        
        <div id="loginForm">
            <h2>欢迎回来</h2>
            <div class="form-group">
                <label>邮箱</label>
                <input type="email" id="loginEmail" placeholder="请输入邮箱">
            </div>
            <div class="form-group">
                <label>密码</label>
                <input type="password" id="loginPassword" placeholder="请输入密码">
            </div>
            <button onclick="handleLogin()">登录</button>
        </div>
        
        <div id="registerForm" class="hidden">
            <h2>创建账户</h2>
            <div class="form-group">
                <label>邮箱</label>
                <input type="email" id="registerEmail" placeholder="请输入邮箱">
            </div>
            <div class="form-group">
                <label>密码</label>
                <input type="password" id="registerPassword" placeholder="请输入密码（至少6位）">
            </div>
            <div class="form-group">
                <label>确认密码</label>
                <input type="password" id="registerConfirmPassword" placeholder="请再次输入密码">
            </div>
            <button onclick="handleRegister()">注册</button>
        </div>
    </div>
    
    <script>
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelector('.tab:nth-child(' + (tab === 'login' ? '1' : '2') + ')').classList.add('active');
            
            document.getElementById('loginForm').classList.toggle('hidden', tab !== 'login');
            document.getElementById('registerForm').classList.toggle('hidden', tab !== 'register');
            
            hideMessages();
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('errorMessage');
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
            document.getElementById('successMessage').classList.add('hidden');
        }
        
        function showSuccess(message) {
            const successDiv = document.getElementById('successMessage');
            successDiv.textContent = message;
            successDiv.classList.remove('hidden');
            document.getElementById('errorMessage').classList.add('hidden');
        }
        
        function hideMessages() {
            document.getElementById('errorMessage').classList.add('hidden');
            document.getElementById('successMessage').classList.add('hidden');
        }
        
        async function handleLogin() {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            
            if (!email || !password) {
                showError('请填写所有字段');
                return;
            }
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showSuccess('登录成功！正在跳转...');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1000);
                } else {
                    showError(result.error || '登录失败');
                }
            } catch (e) {
                showError('网络错误，请重试');
            }
        }
        
        async function handleRegister() {
            const email = document.getElementById('registerEmail').value;
            const password = document.getElementById('registerPassword').value;
            const confirmPassword = document.getElementById('registerConfirmPassword').value;
            
            if (!email || !password || !confirmPassword) {
                showError('请填写所有字段');
                return;
            }
            
            if (password !== confirmPassword) {
                showError('两次输入的密码不一致');
                return;
            }
            
            if (password.length < 6) {
                showError('密码至少需要6位');
                return;
            }
            
            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showSuccess('注册成功！我们已向你的邮箱发送验证邮件，请点击邮件内的链接激活账号，激活后即可登录');
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                } else {
                    showError(result.error || '注册失败');
                }
            } catch (e) {
                showError('网络错误，请重试');
            }
        }
    </script>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>图片编辑与AI生成应用</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Source+Serif+4:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');
        
        * {
            box-sizing: border-box;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Source Serif 4', Georgia, serif;
            background: #FFFFFF;
            color: #000000;
            position: relative;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1000;
            background: repeating-linear-gradient(
                0deg,
                #000000 0px,
                #000000 1px,
                transparent 1px,
                transparent 8px
            );
            opacity: 0.015;
        }
        
        body::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1001;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
            opacity: 0.02;
        }
        
        .nav-bar {
            position: fixed;
            top: 0;
            right: 0;
            padding: 16px 24px;
            z-index: 100;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .user-info {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            letter-spacing: 0.05em;
        }
        
        .header {
            padding: 48px 24px 32px;
            border-bottom: 4px solid #000000;
            position: relative;
        }
        
        h1 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 4rem;
            font-weight: 600;
            letter-spacing: -0.05em;
            line-height: 1;
            margin: 0;
            text-align: center;
        }
        
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 0;
            max-width: 1600px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }
        
        .column {
            padding: 40px 32px;
            border-right: 1px solid #000000;
        }
        
        .column:last-child {
            border-right: none;
        }
        
        h2 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2rem;
            font-weight: 600;
            letter-spacing: -0.025em;
            margin: 0 0 24px 0;
            padding-bottom: 16px;
            border-bottom: 2px solid #000000;
        }
        
        h3 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.5rem;
            font-weight: 600;
            letter-spacing: -0.025em;
            margin: 32px 0 16px 0;
        }
        
        .upload-section {
            margin-bottom: 24px;
        }
        
        input[type="file"] {
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 1rem;
            padding: 12px 0;
            cursor: pointer;
        }
        
        .image-container {
            position: relative;
            display: inline-block;
            max-width: 100%;
            margin: 16px 0;
            border: 2px solid #000000;
        }
        
        #image {
            max-width: 100%;
            display: block;
        }
        
        #canvas {
            position: absolute;
            top: 0;
            left: 0;
            cursor: crosshair;
        }
        
        .controls {
            margin-top: 16px;
        }
        
        .info {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            background: #FFFFFF;
            border: 1px solid #000000;
            padding: 12px;
            margin-top: 8px;
            word-break: break-all;
            letter-spacing: 0.1em;
        }
        
        .hint {
            font-size: 0.9rem;
            color: #525252;
            margin: 8px 0;
            line-height: 1.625;
        }
        
        button {
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            padding: 16px 32px;
            background: #000000;
            color: #FFFFFF;
            border: none;
            border-radius: 0;
            cursor: pointer;
            margin: 8px 8px 8px 0;
            transition: all 100ms ease;
        }
        
        button:hover {
            background: #FFFFFF;
            color: #000000;
            border: 2px solid #000000;
            padding: 14px 30px;
        }
        
        button.secondary {
            background: transparent;
            color: #000000;
            border: 2px solid #000000;
            padding: 14px 30px;
        }
        
        button.secondary:hover {
            background: #000000;
            color: #FFFFFF;
            border: 2px solid #000000;
        }
        
        button.ghost {
            background: transparent;
            color: #000000;
            border: none;
            padding: 8px 0;
            text-decoration: none;
        }
        
        button.ghost:hover {
            text-decoration: underline;
            text-underline-offset: 4px;
            padding: 8px 0;
            border: none;
            background: transparent;
        }
        
        button.danger {
            background: #000000;
            color: #FFFFFF;
        }
        
        button.danger:hover {
            background: #FFFFFF;
            color: #000000;
            border: 2px solid #000000;
        }
        
        /* 按钮操作样式 */
        .button-action {
            background: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #000000 !important;
            padding: 8px 16px !important;
            font-size: 0.75rem !important;
            cursor: pointer !important;
            transition: none !important;
        }
        
        .button-action:hover {
            background: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #000000 !important;
            padding: 8px 16px !important;
        }
        
        .color-picker, .width-picker {
            margin: 16px 0;
        }
        
        label {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        
        select, input[type="text"], textarea {
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 1rem;
            padding: 12px 16px;
            border-radius: 0;
            border: 2px solid #000000;
            background: #FFFFFF;
            color: #000000;
            margin-left: 12px;
            width: 100%;
            max-width: 300px;
            transition: border-width 100ms ease;
        }
        
        select:focus, input[type="text"]:focus, textarea:focus {
            outline: none;
            border-width: 4px;
        }
        
        select {
            cursor: pointer;
        }
        
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        ::placeholder {
            color: #525252;
            font-style: italic;
        }
        
        .button-item {
            padding: 16px;
            background: #FFFFFF;
            border: 1px solid #000000;
            margin-bottom: 8px;
            transition: all 100ms ease;
        }
        
        .button-item:hover {
            background: #000000;
            color: #FFFFFF;
        }
        
        .button-item input, .button-item textarea {
            border: 2px solid #000000 !important;
            font-family: 'Source Serif 4', Georgia, serif !important;
            font-size: 1rem !important;
            transition: none !important;
        }
        
        .button-item input:focus, .button-item textarea:focus {
            border-width: 4px !important;
            outline: none !important;
        }
        
        .button-item:hover input, .button-item:hover textarea {
            background: #FFFFFF !important;
            color: #000000 !important;
            border-color: #FFFFFF !important;
        }
        
        .button-item:hover input:focus, .button-item:hover textarea:focus {
            border-color: #000000 !important;
            border-width: 4px !important;
        }
        
        .button-item-header {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            gap: 12px;
        }
        
        .button-label-input {
            flex: 1;
            max-width: 300px;
            padding: 8px 12px;
            height: 40px;
            box-sizing: border-box;
            vertical-align: middle;
        }
        
        .button-item-actions {
            display: flex;
            gap: 12px;
        }
        
        .button-action {
            height: 40px !important;
            min-width: 60px;
            padding: 0 16px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-sizing: border-box !important;
            vertical-align: middle;
            background: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #000000 !important;
            font-family: 'Source Serif 4', Georgia, serif !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
            cursor: pointer !important;
        }
        
        .button-action:hover {
            background: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #000000 !important;
        }
        
        .button-prompt-input {
            width: 100%;
            min-height: 80px;
            padding: 8px 12px;
            box-sizing: border-box;
            resize: vertical;
            margin: 0;
        }
        
        .result-card {
            background: #FFFFFF;
            border: 2px solid #000000;
            padding: 24px;
            margin-bottom: 24px;
            transition: all 300ms ease;
        }
        
        .result-card:hover {
            border-width: 4px;
        }
        
        .result-card h4 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.5rem;
            font-weight: 600;
            letter-spacing: -0.025em;
            margin: 0 0 16px 0;
            padding-bottom: 12px;
            border-bottom: 1px solid #000000;
        }
        
        .result-content {
            background: #FFFFFF;
            padding: 0;
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.625;
        }
        
        .result-content img {
            max-width: 100%;
            height: auto;
            margin: 16px 0;
            border: 2px solid #000000;
            transition: all 300ms ease;
        }
        
        .result-content img:hover {
            border-width: 4px;
            transform: scale(1.05);
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            border: 3px solid #FFFFFF;
            border-top: 3px solid #000000;
            border-radius: 0;
            width: 48px;
            height: 48px;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .expander {
            margin-bottom: 24px;
        }
        
        .expander-header {
            cursor: pointer;
            padding: 16px;
            background: #FFFFFF;
            border: 2px solid #000000;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 100ms ease;
        }
        
        .expander-header:hover {
            background: #000000;
            color: #FFFFFF;
        }
        
        .expander-header span:first-child {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        
        .expander-content {
            padding: 24px;
            border: 2px solid #000000;
            border-top: none;
            background: #FFFFFF;
        }
        
        .generate-buttons {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }
        
        .generate-buttons button {
            width: 100%;
            margin: 0;
        }
        
        .section-divider {
            height: 4px;
            background: #000000;
            margin: 48px 0;
        }
        
        .grid-texture {
            background-image: 
                linear-gradient(rgba(0,0,0,0.015) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,0,0,0.015) 1px, transparent 1px);
            background-size: 20px 20px;
        }
        
        .inverse {
            background: #000000;
            color: #FFFFFF;
        }
        
        .inverse button {
            background: #FFFFFF;
            color: #000000;
        }
        
        .inverse button:hover {
            background: #000000;
            color: #FFFFFF;
            border: 2px solid #FFFFFF;
        }
    </style>
</head>
<body>
    <div class="nav-bar">
        <span class="user-info">
            <button id="pointsDisplay" style="background:#000000;color:#FFFFFF;border:none;padding:8px 16px;cursor:pointer;font-family:'JetBrains Mono',monospace;" onclick="openPointsModalSimple();">
                积分: {{ current_points }}
            </button>
        </span>
        {% if can_claim_daily %}
        <button id="claimDailyBtn" style="padding:8px 16px;font-size:0.875rem;margin-left:16px;" onclick="claimDailyPoints()">领取每日积分</button>
        {% endif %}
        <span class="user-info" style="margin-left:16px;">{{ user_email }}</span>
        <button class="secondary" onclick="logout()">退出</button>
    </div>
    
    <!-- 积分详情弹窗 -->
    <div id="pointsModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:2000;">
        <div style="position:absolute;top:50px;left:50%;transform:translateX(-50%);background:#FFFFFF;border:4px solid #000000;width:90%;max-width:500px;max-height:70vh;overflow-y:auto;">
            <div style="padding:20px;border-bottom:4px solid #000000;">
                <h2 style="margin:0;font-family:'Playfair Display',serif;font-size:1.5rem;">积分详情</h2>
            </div>
            <div style="padding:20px;">
                <div style="margin-bottom:20px;padding:16px;border:2px solid #000000;">
                    <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;" id="modalPointsDisplay">{{ current_points }} 积分</div>
                </div>
                
                <div style="margin-bottom:20px;">
                    <h3 style="margin:0 0 12px 0;font-family:'Playfair Display',serif;">积分规则</h3>
                    <div style="font-size:0.875rem;line-height:1.8;">
                        <p>- 新用户注册：自动赠送 10 积分</p>
                        <p>- 每日领取：每天可免费领取 10 积分</p>
                        <p>- 生成图片：每次成功生成扣除 2 积分</p>
                        <p>- 失败退款：生成失败自动退还积分</p>
                    </div>
                </div>
                
                <div style="margin-bottom:20px;">
                    <h3 style="margin:0 0 12px 0;font-family:'Playfair Display',serif;">积分明细</h3>
                    <div id="transactionsList" style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;">
                        <p style="color:#525252;">加载中...</p>
                    </div>
                </div>
                
                <button style="width:100%;padding:12px;background:#000000;color:#FFFFFF;border:none;cursor:pointer;" onclick="document.getElementById('pointsModal').style.display='none';">关闭</button>
            </div>
        </div>
    </div>
    
    <div class="header">
        <h1>图片编辑与AI生成</h1>
    </div>
    <div class="container">
        <!-- 第一列：上传和框选 -->
        <div class="column">
            <h2>上传图片</h2>
            <div class="upload-section">
                <input type="file" id="fileInput" accept="image/png,image/jpg,image/jpeg">
            </div>
            
            <div id="imageSection" style="display:none;">
                <div class="color-picker">
                    <label>颜色</label>
                    <select id="colorSelect">
                        {% for i in range(colors|length) %}
                        <option value="{{ colors[i] }}">{{ color_names[i] }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="width-picker">
                    <label>粗细</label>
                    <select id="widthSelect">
                        {% for i in range(widths|length) %}
                        <option value="{{ widths[i] }}">{{ width_names[i] }} ({{ widths[i] }}px)</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="image-container">
                    <img id="image">
                    <canvas id="canvas"></canvas>
                </div>
                <div class="controls">
                    <p class="hint">提示：按住鼠标左键拖拽进行框选</p>
                    <div id="coords" class="info"></div>
                    <br>
                    <button id="clearBtn" class="secondary">清除框选</button>
                </div>
            </div>
        </div>

        <!-- 第二列：生成结果 -->
        <div class="column">
            <h2>生成结果</h2>
            <div style="margin-bottom:16px;">
                <button id="clearAllResults" class="ghost" onclick="clearAllResults()" style="display:none;margin-right:16px;">清除所有结果</button>
                <button id="downloadAllResults" class="ghost" onclick="downloadAllImages()" style="display:none;">下载所有图片</button>
            </div>
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>正在生成...</p>
            </div>
            <div id="resultSection">
                <p class="hint">选择功能按钮后，生成结果将在此显示</p>
            </div>
        </div>

        <!-- 第三列：设置 -->
        <div class="column">
            <h2>设置</h2>
            
            <div class="expander">
                <div class="expander-header" onclick="toggleExpander('addBtn')">
                    <span>添加新功能</span>
                    <span id="addBtnToggle">▶</span>
                </div>
                <div id="addBtnContent" class="expander-content" style="display:none;">
                    <div style="margin:16px 0;">
                        <label>按钮名称</label>
                        <input type="text" id="newBtnName" placeholder="输入按钮名称" style="margin-top:8px;max-width:none;">
                    </div>
                    <div style="margin:16px 0;">
                        <label>提示词</label>
                        <textarea id="newBtnPrompt" placeholder="输入提示词" style="margin-top:8px;max-width:none;"></textarea>
                    </div>
                    <button id="saveBtn">保存按钮</button>
                </div>
            </div>

            <div class="expander">
                <div class="expander-header" onclick="toggleExpander('buttonsList')">
                    <span>已添加的按钮</span>
                    <span id="buttonsListToggle">▶</span>
                </div>
                <div id="buttonsListContent" class="expander-content" style="display:none;">
                    {% if buttons %}
                    {% for btn in buttons %}
                    <div class="button-item" data-button-id="{{ btn.id }}">
                        <div class="button-item-header">
                            <input type="text" class="button-label-input" value="{{ btn.button_label }}" placeholder="按钮名称">
                            <div class="button-item-actions">
                                <button class="button-action" onclick="deleteButton('{{ btn.id }}')">删除</button>
                                <button class="button-action" onclick="saveButton('{{ btn.id }}')">保存</button>
                            </div>
                        </div>
                        <textarea class="button-prompt-input" placeholder="提示词">{{ btn.prompt_text }}</textarea>
                    </div>
                    {% endfor %}
                    {% else %}
                    <p class="hint">暂无按钮，请先添加</p>
                    {% endif %}
                </div>
            </div>

            <div id="generateSection">
                <h3>选择功能生成</h3>
                <div id="generateButtons" class="generate-buttons"></div>
            </div>
        </div>
    </div>

    <script>
        // 全局变量
        let isDrawing = false;
        let startX = 0, startY = 0;
        let currentBox = null;
        let imgWidth = 0, imgHeight = 0;
        let boxColor = '#1677FF';
        let boxWidth = 3;
        let currentImageData = null;
        let resultCount = 0;

        // DOM 元素
        const fileInput = document.getElementById('fileInput');
        const imageSection = document.getElementById('imageSection');
        const image = document.getElementById('image');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const coordsDiv = document.getElementById('coords');
        const clearBtn = document.getElementById('clearBtn');
        const colorSelect = document.getElementById('colorSelect');
        const widthSelect = document.getElementById('widthSelect');
        const resultSection = document.getElementById('resultSection');
        const loading = document.getElementById('loading');
        const generateSection = document.getElementById('generateSection');
        const generateButtons = document.getElementById('generateButtons');

        // 折叠面板
        function toggleExpander(id) {
            const content = document.getElementById(id + 'Content');
            const toggle = document.getElementById(id + 'Toggle');
            if (content.style.display === 'none') {
                content.style.display = 'block';
                toggle.textContent = '▼';
            } else {
                content.style.display = 'none';
                toggle.textContent = '▶';
            }
        }



        // 退出登录
        function logout() {
            fetch('/logout', { method: 'POST' })
                .then(() => {
                    window.location.href = '/login';
                });
        }

        // 简单的打开积分弹窗函数
        function openPointsModalSimple() {
            const modal = document.getElementById('pointsModal');
            modal.style.display = 'block';
            loadTransactions();
        }

        // 打开积分详情弹窗
        function openPointsModal() {
            const modal = document.getElementById('pointsModal');
            modal.style.display = 'block';
            loadTransactions();
        }

        // 关闭积分详情弹窗
        function closePointsModal() {
            const modal = document.getElementById('pointsModal');
            modal.style.display = 'none';
        }

        // 加载积分明细
        async function loadTransactions() {
            const listDiv = document.getElementById('transactionsList');
            try {
                const response = await fetch('/api/points/transactions');
                const result = await response.json();
                
                if (result.success && result.data && result.data.length > 0) {
                    let html = '';
                    result.data.forEach(tx => {
                        const typeLabels = {
                            'signup_bonus': '注册赠送',
                            'daily_claim': '每日领取',
                            'generation': '生成扣除',
                            'refund': '失败退款',
                            'admin_give': '管理员赠送',
                            'admin_deduct': '管理员扣除'
                        };
                        const typeLabel = typeLabels[tx.transaction_type] || tx.transaction_type;
                        const sign = tx.points_change > 0 ? '+' : '';
                        const color = tx.points_change > 0 ? '#52C41A' : '#F5222D';
                        const date = new Date(tx.created_at).toLocaleString('zh-CN');
                        
                        html += `
                            <div style="padding:12px 0;border-bottom:1px solid #d9d9d9;">
                                <div style="display:flex;justify-content:space-between;align-items:center;">
                                    <span>${typeLabel}</span>
                                    <span style="color:${color};font-weight:600;">${sign}${tx.points_change}</span>
                                </div>
                                <div style="color:#525252;font-size:0.75rem;margin-top:4px;">
                                    ${date}
                                    ${tx.description ? '<br>' + tx.description : ''}
                                </div>
                                <div style="color:#525252;font-size:0.75rem;">
                                    余额: ${tx.balance_after}
                                </div>
                            </div>
                        `;
                    });
                    listDiv.innerHTML = html;
                } else {
                    listDiv.innerHTML = '<p style="color:#525252;">暂无积分记录</p>';
                }
            } catch (e) {
                listDiv.innerHTML = '<p style="color:#F5222D;">加载失败，请重试</p>';
            }
        }

        // 领取每日积分
        async function claimDailyPoints() {
            const btn = document.getElementById('claimDailyBtn');
            btn.disabled = true;
            btn.textContent = '领取中...';
            
            try {
                const response = await fetch('/api/points/claim-daily', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('pointsDisplay').textContent = '🪙 ' + result.new_balance;
                    document.getElementById('modalPointsDisplay').textContent = result.new_balance;
                    btn.style.display = 'none';
                    alert('领取成功！获得10积分');
                    loadTransactions();
                } else {
                    alert('领取失败: ' + result.error);
                    btn.disabled = false;
                    btn.textContent = '领取每日积分';
                }
            } catch (e) {
                alert('网络错误，请重试');
                btn.disabled = false;
                btn.textContent = '领取每日积分';
            }
        }

        // 刷新积分显示
        async function refreshPoints() {
            try {
                const response = await fetch('/api/points');
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('pointsDisplay').textContent = '🪙 ' + result.data.current_points;
                    document.getElementById('modalPointsDisplay').textContent = result.data.current_points;
                    const claimBtn = document.getElementById('claimDailyBtn');
                    if (claimBtn) {
                        if (result.data.can_claim_daily) {
                            claimBtn.style.display = 'inline-block';
                        } else {
                            claimBtn.style.display = 'none';
                        }
                    }
                }
            } catch (e) {
                console.log('刷新积分失败:', e);
            }
        }

        // 图片上传
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = async (event) => {
                    image.src = event.target.result;
                    currentImageData = event.target.result;
                    imageSection.style.display = 'block';
                    
                    // 获取图片尺寸
                    const img = new Image();
                    img.onload = () => {
                        imgWidth = img.width;
                        imgHeight = img.height;
                        setTimeout(resizeCanvas, 100);
                    };
                    img.src = event.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
        
        // 页面加载时更新生成按钮
        updateGenerateButtons();

        // Canvas 相关
        function resizeCanvas() {
            canvas.width = image.offsetWidth;
            canvas.height = image.offsetHeight;
            redrawBox();
        }

        function redrawBox() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            if (currentBox) {
                const scaleX = canvas.width / imgWidth;
                const scaleY = canvas.height / imgHeight;
                ctx.strokeStyle = boxColor;
                ctx.lineWidth = boxWidth;
                ctx.strokeRect(
                    currentBox.x1 * scaleX,
                    currentBox.y1 * scaleY,
                    (currentBox.x2 - currentBox.x1) * scaleX,
                    (currentBox.y2 - currentBox.y1) * scaleY
                );
            }
        }

        function getImageCoords(e) {
            const rect = canvas.getBoundingClientRect();
            const scaleX = imgWidth / canvas.width;
            const scaleY = imgHeight / canvas.height;
            return {
                x: Math.max(0, Math.min(imgWidth, Math.round((e.clientX - rect.left) * scaleX))),
                y: Math.max(0, Math.min(imgHeight, Math.round((e.clientY - rect.top) * scaleY)))
            };
        }

        image.onload = function() {
            setTimeout(resizeCanvas, 100);
        };
        window.addEventListener('resize', resizeCanvas);

        canvas.addEventListener('mousedown', (e) => {
            if (e.button === 0) {
                e.preventDefault();
                isDrawing = true;
                const coords = getImageCoords(e);
                startX = coords.x;
                startY = coords.y;
            }
        });

        canvas.addEventListener('mousemove', (e) => {
            if (isDrawing) {
                const coords = getImageCoords(e);
                const scaleX = canvas.width / imgWidth;
                const scaleY = canvas.height / imgHeight;
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.strokeStyle = boxColor;
                ctx.lineWidth = boxWidth;
                const x1 = Math.min(startX, coords.x);
                const y1 = Math.min(startY, coords.y);
                const x2 = Math.max(startX, coords.x);
                const y2 = Math.max(startY, coords.y);
                ctx.strokeRect(
                    x1 * scaleX,
                    y1 * scaleY,
                    (x2 - x1) * scaleX,
                    (y2 - y1) * scaleY
                );
                coordsDiv.textContent = `框选中: (${x1}, ${y1}) → (${x2}, ${y2})`;
            }
        });

        canvas.addEventListener('mouseup', (e) => {
            if (isDrawing && e.button === 0) {
                isDrawing = false;
                const coords = getImageCoords(e);
                currentBox = {
                    x1: Math.min(startX, coords.x),
                    y1: Math.min(startY, coords.y),
                    x2: Math.max(startX, coords.x),
                    y2: Math.max(startY, coords.y)
                };
                coordsDiv.textContent = `已框选: (${currentBox.x1}, ${currentBox.y1}) → (${currentBox.x2}, ${currentBox.y2})`;
                redrawBox();
            }
        });
        
        canvas.addEventListener('mouseleave', (e) => {
            if (isDrawing) {
                isDrawing = false;
                const coords = getImageCoords(e);
                currentBox = {
                    x1: Math.min(startX, coords.x),
                    y1: Math.min(startY, coords.y),
                    x2: Math.max(startX, coords.x),
                    y2: Math.max(startY, coords.y)
                };
                coordsDiv.textContent = `已框选: (${currentBox.x1}, ${currentBox.y1}) → (${currentBox.x2}, ${currentBox.y2})`;
                redrawBox();
            }
        });

        clearBtn.addEventListener('click', () => {
            currentBox = null;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            coordsDiv.textContent = '';
        });

        colorSelect.addEventListener('change', (e) => {
            boxColor = e.target.value;
            redrawBox();
        });

        widthSelect.addEventListener('change', (e) => {
            boxWidth = parseInt(e.target.value);
            redrawBox();
        });

        // 按钮管理
        document.getElementById('saveBtn').addEventListener('click', () => {
            const name = document.getElementById('newBtnName').value;
            const prompt = document.getElementById('newBtnPrompt').value;
            if (name && prompt) {
                fetch('/add_button', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, prompt })
                }).then(() => {
                    location.reload();
                });
            }
        });

        function deleteButton(buttonId) {
            fetch('/delete_button', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ button_id: buttonId })
            }).then(() => {
                location.reload();
            });
        }
        
        function saveButton(buttonId) {
            const buttonItem = document.querySelector(`[data-button-id="${buttonId}"]`);
            const labelInput = buttonItem.querySelector('.button-label-input');
            const promptInput = buttonItem.querySelector('.button-prompt-input');
            
            const newLabel = labelInput.value.trim();
            const newPrompt = promptInput.value.trim();
            
            if (!newLabel || !newPrompt) {
                alert('按钮名称和提示词不能为空');
                return;
            }
            
            fetch('/update_button', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    button_id: buttonId, 
                    button_label: newLabel, 
                    prompt_text: newPrompt 
                })
            }).then(response => response.json())
              .then(result => {
                  if (result.success) {
                      alert('按钮更新成功');
                      location.reload();
                  } else {
                      alert('更新失败: ' + result.error);
                  }
              })
              .catch(e => {
                  alert('网络错误，请重试');
              });
        }

        function updateGenerateButtons() {
            fetch('/get_buttons')
                .then(r => r.json())
                .then(buttons => {
                    generateButtons.innerHTML = '';
                    buttons.forEach((btn, i) => {
                        const button = document.createElement('button');
                        button.textContent = btn.button_label;
                        button.onclick = () => generate(i);
                        generateButtons.appendChild(button);
                    });
                });
        }
        
        async function downloadAllImages() {
            try {
                const resultCards = document.querySelectorAll('.result-card');
                const imageUrls = [];
                
                resultCards.forEach(card => {
                    const images = card.querySelectorAll('img');
                    images.forEach(img => {
                        if (img.src && img.src.startsWith('http')) {
                            imageUrls.push(img.src);
                        }
                    });
                });
                
                if (imageUrls.length === 0) {
                    alert('没有可下载的图片');
                    return;
                }
                
                // 向服务器发送请求，获取打包的图片
                const response = await fetch('/download_all_images', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ image_urls: imageUrls })
                });
                
                if (!response.ok) {
                    throw new Error('下载失败');
                }
                
                // 创建下载链接
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'generated_images.zip';
                document.body.appendChild(a);
                a.click();
                
                // 清理
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }, 100);
            } catch (e) {
                alert('下载失败: ' + e.message);
            }
        }

        // 生成功能
        async function generate(buttonIndex) {
            resultCount++;
            const currentResultId = resultCount;
            
            // 创建加载中的结果卡片
            const loadingDiv = document.createElement('div');
            loadingDiv.id = `loading-${currentResultId}`;
            loadingDiv.className = 'result-card';
            loadingDiv.innerHTML = `
                <h4>结果 #${currentResultId} <span style="color:#525252;font-size:1rem;font-weight:400;">(生成中...)</span></h4>
                <div class="loading" style="display:block;padding:40px;">
                    <div class="spinner"></div>
                    <p>正在生成...</p>
                </div>
            `;
            
            resultSection.appendChild(loadingDiv);
            document.getElementById('clearAllResults').style.display = 'inline-block';
            document.getElementById('downloadAllResults').style.display = 'inline-block';
            resultSection.style.display = 'block';
            
            try {
                // 准备图片（带框）
                let imageData = currentImageData;
                if (currentBox) {
                    const response = await fetch('/draw_box', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            image: currentImageData,
                            coords: currentBox,
                            color: boxColor,
                            width: boxWidth
                        })
                    });
                    const result = await response.json();
                    imageData = result.image;
                }
                
                // 调用API
                const generateResponse = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        image: imageData,
                        button_index: buttonIndex
                    })
                });
                
                const result = await generateResponse.json();
                
                // 刷新积分显示
                refreshPoints();
                
                // 更新结果卡片
                const resultDiv = document.getElementById(`loading-${currentResultId}`);
                if (resultDiv) {
                    if (result.error) {
                        resultDiv.innerHTML = `
                            <h4>结果 #${currentResultId} <span style="color:#000000;font-size:1rem;font-weight:400;">(失败)</span></h4>
                            <p style="color:#000000;font-weight:600;">错误: ${result.error}</p>
                        `;
                    } else if (result.choices) {
                        let content = result.choices[0].message.content;
                        content = content.replace(/<img /g, '<img referrerpolicy="no-referrer" ');
                        content = content.replace(/!\[.*?\]\(`?([^`\)]+)`?\)/g, '<img src="$1" referrerpolicy="no-referrer" style="max-width:100%;height:auto;margin:16px 0;">');
                        
                        resultDiv.innerHTML = `
                            <h4>结果 #${currentResultId}</h4>
                            <div class="result-content">${content}</div>
                            <button style="margin-top:16px;" onclick="downloadResultWithContent('${encodeURIComponent(content)}')">下载结果</button>
                        `;
                        window[`result_${currentResultId}`] = result;
                    }
                }
            } catch (e) {
                const resultDiv = document.getElementById(`loading-${currentResultId}`);
                if (resultDiv) {
                    resultDiv.innerHTML = `
                        <h4>结果 #${currentResultId} <span style="color:#000000;font-size:1rem;font-weight:400;">(失败)</span></h4>
                        <p style="color:#000000;font-weight:600;">错误: ${e.message}</p>
                    `;
                }
            }
        }

        async function downloadResultWithContent(encodedContent) {
            const content = decodeURIComponent(encodedContent);
            let imageUrl = null;
            
            const markdownMatch = content.match(/!\[.*?\]\(`?([^`\)]+)`?\)/);
            if (markdownMatch) {
                imageUrl = markdownMatch[1];
            }
            
            const imgMatch = content.match(/<img[^>]+src="([^"]+)"/);
            if (!imageUrl && imgMatch) {
                imageUrl = imgMatch[1];
            }
            
            if (imageUrl) {
                try {
                    const response = await fetch(imageUrl, { referrerPolicy: 'no-referrer' });
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'generated_image.png';
                    a.click();
                    URL.revokeObjectURL(url);
                } catch (e) {
                    alert('下载图片失败: ' + e.message);
                }
            } else {
                alert('未找到图片URL');
            }
        }

        function clearAllResults() {
            resultSection.innerHTML = '<p class="hint">选择功能按钮后，生成结果将在此显示</p>';
            resultCount = 0;
            document.getElementById('clearAllResults').style.display = 'none';
            document.getElementById('downloadAllResults').style.display = 'none';
        }

        // 初始化
        updateGenerateButtons();
        
        // 积分弹窗事件绑定
        document.addEventListener('DOMContentLoaded', function() {
            const pointsBtn = document.getElementById('pointsButton');
            const closeModalBtn = document.getElementById('closeModalBtn');
            const modal = document.getElementById('pointsModal');
            
            if (pointsBtn) {
                pointsBtn.addEventListener('click', function() {
                    modal.style.display = 'block';
                    loadTransactions();
                });
            }
            
            if (closeModalBtn) {
                closeModalBtn.addEventListener('click', function() {
                    modal.style.display = 'none';
                });
            }
            
            if (modal) {
                modal.addEventListener('click', function(e) {
                    if (e.target === modal) {
                        modal.style.display = 'none';
                    }
                });
            }
        });
    </script>
</body>
</html>
"""

# ==================== 积分功能辅助函数 ====================

def get_user_id_from_email(email):
    """通过邮箱获取用户 ID"""
    try:
        response = supabase_admin.auth.admin.list_users()
        for user in response:
            if user.email == email:
                return user.id
        return None
    except Exception as e:
        print(f"获取用户ID错误: {e}")
        return None

def get_user_points(user_id):
    """获取用户当前积分"""
    try:
        response = supabase_admin.table('user_points').select('*').eq('user_id', user_id).single().execute()
        if response.data:
            return response.data
        return None
    except Exception as e:
        print(f"获取用户积分错误: {e}")
        return None

def check_daily_claim_available(user_id):
    """检查用户今天是否可以领取每日积分"""
    try:
        from datetime import date
        today = date.today().isoformat()
        user_points = get_user_points(user_id)
        if not user_points:
            return False
        return user_points.get('last_daily_claim') != today
    except Exception as e:
        print(f"检查每日领取错误: {e}")
        return False

def add_points(user_id, points, transaction_type, description=None, related_id=None):
    """为用户增加积分"""
    try:
        user_points = get_user_points(user_id)
        if not user_points:
            return False, "用户积分记录不存在"
        
        new_balance = user_points['current_points'] + points
        new_total_earned = user_points['total_earned'] + (points if points > 0 else 0)
        new_total_spent = user_points['total_spent'] + (abs(points) if points < 0 else 0)
        
        # 更新积分余额
        update_data = {
            'current_points': new_balance,
            'total_earned': new_total_earned,
            'total_spent': new_total_spent
        }
        
        supabase_admin.table('user_points').update(update_data).eq('user_id', user_id).execute()
        
        # 记录交易
        transaction_data = {
            'user_id': user_id,
            'points_change': points,
            'balance_after': new_balance,
            'transaction_type': transaction_type,
            'description': description
        }
        if related_id:
            transaction_data['related_id'] = related_id
        
        supabase_admin.table('point_transactions').insert(transaction_data).execute()
        
        return True, new_balance
    except Exception as e:
        print(f"增加积分错误: {e}")
        return False, str(e)

def deduct_points(user_id, points, transaction_type, description=None, related_id=None):
    """扣除用户积分"""
    user_points = get_user_points(user_id)
    if not user_points:
        return False, "用户积分记录不存在"
    
    if user_points['current_points'] < points:
        return False, "积分不足"
    
    return add_points(user_id, -points, transaction_type, description, related_id)

def claim_daily_points(user_id):
    """领取每日积分"""
    try:
        if not check_daily_claim_available(user_id):
            return False, "今天已经领取过了"
        
        from datetime import date
        today = date.today().isoformat()
        
        # 先增加积分
        success, result = add_points(user_id, 10, 'daily_claim', '每日签到领取10积分')
        if not success:
            return False, result
        
        # 更新每日领取记录
        supabase_admin.table('user_points').update({'last_daily_claim': today}).eq('user_id', user_id).execute()
        
        return True, result
    except Exception as e:
        print(f"领取每日积分错误: {e}")
        return False, str(e)

def create_generation_record(user_id, prompt, image_data=None):
    """创建生成记录"""
    try:
        data = {
            'user_id': user_id,
            'prompt': prompt,
            'status': 'pending'
        }
        if image_data:
            data['image_data'] = image_data
        
        response = supabase_admin.table('generation_records').insert(data).execute()
        if response.data:
            return response.data[0]['id']
        return None
    except Exception as e:
        print(f"创建生成记录错误: {e}")
        return None

def update_generation_record(record_id, status, result_image_url=None, error_message=None, points_deducted=None):
    """更新生成记录"""
    try:
        data = {'status': status}
        if result_image_url:
            data['result_image_url'] = result_image_url
        if error_message:
            data['error_message'] = error_message
        if points_deducted is not None:
            data['points_deducted'] = points_deducted
        if status in ['success', 'failed', 'refunded']:
            from datetime import datetime
            data['completed_at'] = datetime.utcnow().isoformat()
        
        supabase_admin.table('generation_records').update(data).eq('id', record_id).execute()
        return True
    except Exception as e:
        print(f"更新生成记录错误: {e}")
        return False

# ==================== 用户按钮配置管理函数 ====================

def check_user_buttons_initialized(user_id):
    """检查用户是否已初始化按钮配置"""
    try:
        response = supabase_admin.table('user_buttons').select('id').eq('user_id', user_id).limit(1).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"检查用户按钮初始化错误: {e}")
        return False

def initialize_user_buttons(user_id):
    """为用户初始化按钮配置（从全局模板复制）"""
    try:
        response = supabase_admin.table('global_button_templates').select('*').order('created_at').execute()
        if response.data:
            for template in response.data:
                button_data = {
                    'user_id': user_id,
                    'button_label': template['button_label'],
                    'prompt_text': template['prompt_text'],
                    'type': 'initial'
                }
                supabase_admin.table('user_buttons').insert(button_data).execute()
        return True
    except Exception as e:
        print(f"初始化用户按钮错误: {e}")
        return False

def get_user_buttons(user_id):
    """获取用户的按钮配置"""
    try:
        response = supabase_admin.table('user_buttons').select('*').eq('user_id', user_id).order('created_at').execute()
        return response.data
    except Exception as e:
        print(f"获取用户按钮错误: {e}")
        return []

def add_user_button(user_id, button_label, prompt_text):
    """为用户添加自定义按钮"""
    try:
        button_data = {
            'user_id': user_id,
            'button_label': button_label,
            'prompt_text': prompt_text,
            'type': 'custom'
        }
        response = supabase_admin.table('user_buttons').insert(button_data).execute()
        return True, response.data[0] if response.data else None
    except Exception as e:
        print(f"添加用户按钮错误: {e}")
        return False, str(e)

def delete_user_button(user_id, button_id):
    """删除用户的按钮"""
    try:
        supabase_admin.table('user_buttons').delete().eq('user_id', user_id).eq('id', button_id).execute()
        return True
    except Exception as e:
        print(f"删除用户按钮错误: {e}")
        return False

def update_user_button(user_id, button_id, button_label, prompt_text):
    """更新用户的按钮"""
    try:
        update_data = {
            'button_label': button_label,
            'prompt_text': prompt_text
        }
        supabase_admin.table('user_buttons').update(update_data).eq('user_id', user_id).eq('id', button_id).execute()
        return True, None
    except Exception as e:
        print(f"更新用户按钮错误: {e}")
        return False, str(e)

# ==================== 登录检查装饰器 ====================

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/login')
def login_page():
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register')
def register_page():
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register', methods=['POST'])
def register():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase 未正确配置，请检查 API Key"})
    
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    print(f"注册请求 - 邮箱: {email}")
    
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        print(f"注册响应: {response}")
        print(f"用户信息: {response.user}")
        print(f"会话信息: {response.session}")
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"注册错误: {e}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        error_msg = str(e)
        if "Invalid API key" in error_msg:
            error_msg = "Supabase API Key 无效，请在 Supabase 控制台获取正确的 Anon Key"
        return jsonify({"success": False, "error": error_msg})

@app.route('/login', methods=['POST'])
def login():
    if not supabase:
        return jsonify({"success": False, "error": "Supabase 未正确配置，请检查 API Key"})
    
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        user_id = None
        if response.user:
            user_id = str(response.user.id)
            
            try:
                user_points = get_user_points(user_id)
                if not user_points:
                    from datetime import date
                    today = date.today().isoformat()
                    
                    user_points_data = {
                        'user_id': user_id,
                        'current_points': 10,
                        'total_earned': 10,
                        'total_spent': 0,
                        'last_daily_claim': None
                    }
                    supabase_admin.table('user_points').insert(user_points_data).execute()
                    
                    transaction_data = {
                        'user_id': user_id,
                        'points_change': 10,
                        'balance_after': 10,
                        'transaction_type': 'signup_bonus',
                        'description': '新用户注册赠送10积分'
                    }
                    supabase_admin.table('point_transactions').insert(transaction_data).execute()
            except Exception as e:
                print(f"登录时初始化用户积分错误: {e}")
        
        session['user'] = {
            'email': email,
            'user_id': user_id,
            'access_token': response.session.access_token if response.session else None,
            'refresh_token': response.session.refresh_token if response.session else None
        }
        return jsonify({"success": True})
    except Exception as e:
        error_msg = str(e)
        if "Invalid API key" in error_msg:
            error_msg = "Supabase API Key 无效，请在 Supabase 控制台获取正确的 Anon Key"
        return jsonify({"success": False, "error": error_msg})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    try:
        supabase.auth.sign_out()
    except:
        pass
    return jsonify({"success": True})

# ==================== 积分功能路由 ====================

@app.route('/api/points')
@login_required
def get_points():
    """获取用户积分信息"""
    user_id = session['user'].get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "无法获取用户信息"})
    
    user_points = get_user_points(user_id)
    if not user_points:
        return jsonify({"success": False, "error": "积分记录不存在"})
    
    can_claim_daily = check_daily_claim_available(user_id)
    
    return jsonify({
        "success": True,
        "data": {
            "current_points": user_points['current_points'],
            "total_earned": user_points['total_earned'],
            "total_spent": user_points['total_spent'],
            "can_claim_daily": can_claim_daily
        }
    })

@app.route('/api/points/claim-daily', methods=['POST'])
@login_required
def claim_daily():
    """领取每日积分"""
    user_id = session['user'].get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "无法获取用户信息"})
    
    success, result = claim_daily_points(user_id)
    if success:
        return jsonify({"success": True, "new_balance": result})
    else:
        return jsonify({"success": False, "error": result})

@app.route('/api/points/transactions')
@login_required
def get_transactions():
    """获取积分交易记录"""
    user_id = session['user'].get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "无法获取用户信息"})
    
    try:
        response = supabase_admin.table('point_transactions').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(50).execute()
        return jsonify({"success": True, "data": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==================== 主页面 ====================

@app.route('/')
@login_required
def index():
    user_email = session['user']['email']
    user_id = session['user'].get('user_id')
    
    user_points_data = None
    user_buttons_list = []
    if user_id:
        user_points_data = get_user_points(user_id)
        
        if not check_user_buttons_initialized(user_id):
            initialize_user_buttons(user_id)
        
        user_buttons_list = get_user_buttons(user_id)
    
    current_points = user_points_data['current_points'] if user_points_data else 0
    can_claim_daily = check_daily_claim_available(user_id) if user_id else False
    
    return render_template_string(
        HTML_TEMPLATE,
        buttons=user_buttons_list,
        colors=COLORS,
        color_names=COLOR_NAMES,
        widths=WIDTHS,
        width_names=WIDTH_NAMES,
        user_email=user_email,
        current_points=current_points,
        can_claim_daily=can_claim_daily
    )

@app.route('/add_button', methods=['POST'])
@login_required
def add_button():
    data = request.json
    user_id = session['user'].get('user_id')
    success, result = add_user_button(user_id, data["name"], data["prompt"])
    return jsonify({"success": success, "result": result})

@app.route('/delete_button', methods=['POST'])
@login_required
def delete_button():
    data = request.json
    user_id = session['user'].get('user_id')
    success = delete_user_button(user_id, data["button_id"])
    return jsonify({"success": success})

@app.route('/get_buttons')
@login_required
def get_buttons_route():
    user_id = session['user'].get('user_id')
    buttons_list = get_user_buttons(user_id)
    return jsonify(buttons_list)

@app.route('/update_button', methods=['POST'])
@login_required
def update_button():
    data = request.json
    user_id = session['user'].get('user_id')
    button_id = data.get('button_id')
    button_label = data.get('button_label')
    prompt_text = data.get('prompt_text')
    
    if not button_id or not button_label or not prompt_text:
        return jsonify({"success": False, "error": "缺少必要参数"})
    
    success, error = update_user_button(user_id, button_id, button_label, prompt_text)
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": error})

@app.route('/draw_box', methods=['POST'])
@login_required
def draw_box():
    data = request.json
    # 解码base64图片
    img_data = data["image"].split(",")[1]
    img_bytes = base64.b64decode(img_data)
    img = Image.open(io.BytesIO(img_bytes))
    
    # 画框
    draw = ImageDraw.Draw(img)
    coords = data["coords"]
    draw.rectangle(
        [coords["x1"], coords["y1"], coords["x2"], coords["y2"]],
        outline=data["color"],
        width=data["width"]
    )
    
    # 重新编码
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    new_image_data = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return jsonify({"image": new_image_data})

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    data = request.json
    button_index = data["button_index"]
    image_data = data["image"]
    
    # 从数据库获取 API 配置
    api_config = get_api_config()
    
    # 获取用户信息
    user_id = session['user'].get('user_id')
    
    if not user_id:
        return jsonify({"error": "无法获取用户信息"})
    
    # 检查积分是否足够
    user_points = get_user_points(user_id)
    if not user_points or user_points['current_points'] < 2:
        return jsonify({"error": "积分不足，请先领取每日积分或充值"})
    
    # 获取用户的按钮列表
    user_buttons_list = get_user_buttons(user_id)
    if button_index >= len(user_buttons_list):
        return jsonify({"error": "按钮索引无效"})
    
    # 获取提示词
    prompt = user_buttons_list[button_index]["prompt_text"]
    
    # 创建生成记录
    record_id = create_generation_record(user_id, prompt, image_data)
    
    # 扣除积分
    deduct_success, deduct_result = deduct_points(
        user_id, 
        2, 
        'generation', 
        f'图片生成: {user_buttons_list[button_index]["button_label"]}',
        record_id
    )
    
    if not deduct_success:
        if record_id:
            update_generation_record(record_id, 'failed', error_message="扣除积分失败")
        return jsonify({"error": deduct_result})
    
    # 更新生成记录
    if record_id:
        update_generation_record(record_id, 'pending', points_deducted=2)
    
    # 处理图片
    img_base64 = image_data.split(",")[1]
    
    # 构建请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_config['api_key']}"
    }
    
    payload = {
        "model": api_config['model'],
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(api_config['api_url'], headers=headers, json=payload, stream=True, timeout=300)
        response.raise_for_status()
        
        full_content = ""
        try:
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8', errors='ignore')
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]
                        if data_str != '[DONE]':
                            try:
                                import json
                                data_obj = json.loads(data_str)
                                if 'choices' in data_obj and len(data_obj['choices']) > 0:
                                    delta = data_obj['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        full_content += content
                            except Exception:
                                pass
        except Exception as e:
            print(f"流式读取警告: {e}")
        
        if not full_content:
            # 生成失败，退款
            if record_id:
                update_generation_record(record_id, 'failed', error_message="未收到有效内容")
                # 退款
                add_points(user_id, 2, 'refund', '生成失败退款', record_id)
            return jsonify({"error": "未收到有效内容，请重试，积分已退还"})
        
        # 生成成功
        if record_id:
            update_generation_record(record_id, 'success')
        
        return jsonify({
            "choices": [
                {
                    "message": {
                        "content": full_content
                    }
                }
            ]
        })
    except Exception as e:
        # 生成失败，退款
        if record_id:
            update_generation_record(record_id, 'failed', error_message=str(e))
            # 退款
            add_points(user_id, 2, 'refund', '生成失败退款', record_id)
        return jsonify({"error": f"{str(e)}，积分已退还"})

@app.route('/download_all_images', methods=['POST'])
@login_required
def download_all_images():
    """下载所有生成的图片，打包为ZIP文件"""
    try:
        data = request.json
        image_urls = data.get('image_urls', [])
        
        if not image_urls:
            return jsonify({"error": "没有要下载的图片"}), 400
        
        # 创建临时目录保存图片
        temp_dir = 'temp_images'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # 创建ZIP文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, url in enumerate(image_urls):
                try:
                    # 下载图片
                    response = requests.get(url, timeout=10, verify=False)  # 禁用SSL验证
                    response.raise_for_status()
                    
                    # 保存图片到ZIP文件
                    image_name = f'image_{i+1}.png'
                    zip_file.writestr(image_name, response.content)
                except Exception as e:
                    print(f"下载图片失败 {url}: {e}")
                    continue
        
        # 清理临时目录
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)
        
        # 重置文件指针
        zip_buffer.seek(0)
        
        # 返回ZIP文件
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='generated_images.zip'
        )
    except Exception as e:
        print(f"下载所有图片失败: {e}")
        return jsonify({"error": f"下载失败: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 应用启动中...")
    print("📱 请在浏览器中打开: http://localhost:5000")
    print("🌐 外部访问地址: http://<服务器IP>:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
