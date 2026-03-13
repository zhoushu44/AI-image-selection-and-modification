from flask import Flask, render_template_string, request, jsonify
from PIL import Image, ImageDraw
import requests
import base64
import io
import json
import os

app = Flask(__name__)

# 配置
API_CONFIG = {
    "api_key": "sk-muDiVOc0MZmkpSWMLguFlJhmWRq4707fgKDTfMHSsMPctZxi",
    "api_url": "https://api.nofx.online/v1/chat/completions",
    "model": "gemini-3.1-flash-image-square"
}

# 状态存储
buttons = []
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
        
        .header {
            padding: 48px 24px 32px;
            border-bottom: 4px solid #000000;
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
            display: flex;
            justify-content: space-between;
            align-items: center;
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
        
        .button-item span {
            flex: 1;
            margin-right: 16px;
        }
        
        .button-item button {
            margin: 0;
            padding: 8px 16px;
            font-size: 0.75rem;
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
                <button id="clearAllResults" class="ghost" onclick="clearAllResults()" style="display:none;">清除所有结果</button>
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
                <div class="expander-header" onclick="toggleExpander('api')">
                    <span>API 配置</span>
                    <span id="apiToggle">▼</span>
                </div>
                <div id="apiContent" class="expander-content">
                    <div style="margin:16px 0;">
                        <label>API Key</label>
                        <div style="display:flex;align-items:center;gap:12px;margin-top:8px;">
                            <input type="text" id="apiKey" value="{{ api_config.api_key }}" style="flex:1;margin:0;max-width:none;">
                            <button type="button" onclick="toggleApiKeyVisibility()" id="toggleKeyBtn" style="padding:12px 16px;margin:0;">显示</button>
                        </div>
                    </div>
                    <div style="margin:16px 0;">
                        <label>API URL</label>
                        <input type="text" id="apiUrl" value="{{ api_config.api_url }}" style="margin-top:8px;max-width:none;">
                    </div>
                    <div style="margin:16px 0;">
                        <label>Model</label>
                        <input type="text" id="apiModel" value="{{ api_config.model }}" style="margin-top:8px;max-width:none;">
                    </div>
                </div>
            </div>

            <div class="expander">
                <div class="expander-header" onclick="toggleExpander('addBtn')">
                    <span>添加新功能</span>
                    <span id="addBtnToggle">▼</span>
                </div>
                <div id="addBtnContent" class="expander-content">
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
                    <span id="buttonsListToggle">▼</span>
                </div>
                <div id="buttonsListContent" class="expander-content">
                    {% if buttons %}
                    {% for i in range(buttons|length) %}
                    <div class="button-item">
                        <span><strong>{{ buttons[i].name }}</strong>: {{ buttons[i].prompt }}</span>
                        <button class="danger" onclick="deleteButton({{ i }})">删除</button>
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

        // 显示/隐藏API Key
        let apiKeyVisible = true;
        function toggleApiKeyVisibility() {
            const apiKeyInput = document.getElementById('apiKey');
            const toggleBtn = document.getElementById('toggleKeyBtn');
            if (apiKeyVisible) {
                apiKeyInput.type = 'password';
                toggleBtn.textContent = '👁️‍🗨️';
            } else {
                apiKeyInput.type = 'text';
                toggleBtn.textContent = '👁️';
            }
            apiKeyVisible = !apiKeyVisible;
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

        function deleteButton(index) {
            fetch('/delete_button', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ index })
            }).then(() => {
                location.reload();
            });
        }

        function updateGenerateButtons() {
            fetch('/get_buttons')
                .then(r => r.json())
                .then(buttons => {
                    generateButtons.innerHTML = '';
                    buttons.forEach((btn, i) => {
                        const button = document.createElement('button');
                        button.textContent = btn.name;
                        button.onclick = () => generate(i);
                        generateButtons.appendChild(button);
                    });
                });
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
                        button_index: buttonIndex,
                        api_config: {
                            api_key: document.getElementById('apiKey').value,
                            api_url: document.getElementById('apiUrl').value,
                            model: document.getElementById('apiModel').value
                        }
                    })
                });
                
                const result = await generateResponse.json();
                
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
        }

        // 初始化
        updateGenerateButtons();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE,
        api_config=API_CONFIG,
        buttons=buttons,
        colors=COLORS,
        color_names=COLOR_NAMES,
        widths=WIDTHS,
        width_names=WIDTH_NAMES
    )

@app.route('/add_button', methods=['POST'])
def add_button():
    data = request.json
    buttons.append({"name": data["name"], "prompt": data["prompt"]})
    return jsonify({"success": True})

@app.route('/delete_button', methods=['POST'])
def delete_button():
    data = request.json
    if 0 <= data["index"] < len(buttons):
        buttons.pop(data["index"])
    return jsonify({"success": True})

@app.route('/get_buttons')
def get_buttons():
    return jsonify(buttons)

@app.route('/draw_box', methods=['POST'])
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
def generate():
    data = request.json
    button_index = data["button_index"]
    api_config = data["api_config"]
    image_data = data["image"]
    
    # 获取提示词
    prompt = buttons[button_index]["prompt"]
    
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
            return jsonify({"error": "未收到有效内容，请重试"})
        
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
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    print("🚀 应用启动中...")
    print("📱 请在浏览器中打开: http://localhost:5000")
    print("🌐 外部访问地址: http://<服务器IP>:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
