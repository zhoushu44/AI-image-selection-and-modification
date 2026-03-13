import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw
import io
import json

st.set_page_config(layout="wide", page_title="图片编辑应用")

st.title("📷 图片编辑与AI生成应用")

if "api_config" not in st.session_state:
    st.session_state.api_config = {
        "api_key": "96d739dd-5f53-4a6d-b89d-1779f27be846",
        "api_url": "https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions",
        "model": "ark-code-latest"
    }

if "buttons" not in st.session_state:
    st.session_state.buttons = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None

if "generated_result" not in st.session_state:
    st.session_state.generated_result = None

if "box_color" not in st.session_state:
    st.session_state.box_color = "#1677FF"

if "box_width" not in st.session_state:
    st.session_state.box_width = 3

if "box_coords" not in st.session_state:
    st.session_state.box_coords = None

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

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def draw_box_on_image(image_bytes, coords, color, width):
    img = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(img)
    x1, y1, x2, y2 = coords
    draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def call_api(image_bytes, prompt, api_config):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_config['api_key']}"
    }
    
    base64_image = encode_image(image_bytes)
    
    payload = {
        "model": api_config['model'],
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
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(api_config['api_url'], headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

col1, col2, col3 = st.columns(3)

with col1:
    st.header("📁 上传图片")
    
    uploaded_file = st.file_uploader("选择图片文件", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        st.session_state.uploaded_image = Image.open(uploaded_file)
        st.session_state.image_bytes = uploaded_file.getvalue()
        st.session_state.generated_result = None
        st.session_state.box_coords = None
    
    if st.session_state.uploaded_image is not None:
        img_width, img_height = st.session_state.uploaded_image.size
        
        st.markdown("---")
        
        st.subheader("🎨 框选样式")
        
        color_idx = COLORS.index(st.session_state.box_color)
        selected_color = st.selectbox(
            "选择颜色",
            options=range(len(COLORS)),
            format_func=lambda i: f"{COLOR_NAMES[i]} ({COLORS[i]})",
            index=color_idx
        )
        st.session_state.box_color = COLORS[selected_color]
        
        width_idx = WIDTHS.index(st.session_state.box_width)
        selected_width = st.selectbox(
            "选择粗细",
            options=range(len(WIDTHS)),
            format_func=lambda i: f"{WIDTH_NAMES[i]} ({WIDTHS[i]}px)",
            index=width_idx
        )
        st.session_state.box_width = WIDTHS[selected_width]
        
        st.markdown("---")
        
        st.subheader("🔲 框选操作")
        
        display_image = st.session_state.uploaded_image
        display_bytes = st.session_state.image_bytes
        
        if st.session_state.box_coords:
            display_bytes = draw_box_on_image(
                st.session_state.image_bytes,
                st.session_state.box_coords,
                st.session_state.box_color,
                st.session_state.box_width
            )
            display_image = Image.open(io.BytesIO(display_bytes))
        
        img_base64 = encode_image(display_bytes)
        box_coords_str = ""
        if st.session_state.box_coords:
            box_coords_str = f"{st.session_state.box_coords[0]},{st.session_state.box_coords[1]},{st.session_state.box_coords[2]},{st.session_state.box_coords[3]}"
        
        canvas_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    margin: 0;
                    padding: 10px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }}
                #container {{
                    position: relative;
                    display: inline-block;
                    max-width: 100%;
                }}
                #image {{
                    max-width: 100%;
                    display: block;
                }}
                #canvas {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    cursor: crosshair;
                }}
                .controls {{
                    margin-top: 10px;
                }}
                .info {{
                    font-family: monospace;
                    background: #f5f5f5;
                    padding: 8px;
                    border-radius: 4px;
                    margin-top: 5px;
                }}
                .hint {{
                    font-size: 14px;
                    color: #666;
                    margin: 5px 0;
                }}
                button {{
                    padding: 8px 16px;
                    background: #1677FF;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-right: 10px;
                }}
                button:hover {{
                    background: #0958d9;
                }}
                button.secondary {{
                    background: #f0f0f0;
                    color: #333;
                }}
                button.secondary:hover {{
                    background: #d9d9d9;
                }}
            </style>
        </head>
        <body>
            <div id="container">
                <img id="image" src="data:image/png;base64,{img_base64}" />
                <canvas id="canvas"></canvas>
            </div>
            <div class="controls">
                <p class="hint">提示：按住鼠标右键拖拽进行框选</p>
                <div id="coords" class="info"></div>
                <br>
                <button id="clearBtn" class="secondary">清除框选</button>
                <button id="applyBtn">应用框选</button>
            </div>

            <script>
                const image = document.getElementById('image');
                const canvas = document.getElementById('canvas');
                const ctx = canvas.getContext('2d');
                const coordsDiv = document.getElementById('coords');
                const clearBtn = document.getElementById('clearBtn');
                const applyBtn = document.getElementById('applyBtn');

                let isDrawing = false;
                let startX = 0, startY = 0;
                let currentBox = null;
                let imgWidth = {img_width};
                let imgHeight = {img_height};
                let boxColor = '{st.session_state.box_color}';
                let boxWidth = {st.session_state.box_width};

                function resizeCanvas() {{
                    canvas.width = image.offsetWidth;
                    canvas.height = image.offsetHeight;
                    redrawBox();
                }}

                function redrawBox() {{
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    if (currentBox) {{
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
                    }}
                }}

                function getImageCoords(e) {{
                    const rect = canvas.getBoundingClientRect();
                    const scaleX = imgWidth / canvas.width;
                    const scaleY = imgHeight / canvas.height;
                    return {{
                        x: Math.max(0, Math.min(imgWidth, Math.round((e.clientX - rect.left) * scaleX))),
                        y: Math.max(0, Math.min(imgHeight, Math.round((e.clientY - rect.top) * scaleY)))
                    }};
                }}

                image.onload = function() {{
                    setTimeout(resizeCanvas, 100);
                }};
                window.addEventListener('resize', resizeCanvas);

                canvas.addEventListener('contextmenu', (e) => {{
                    e.preventDefault();
                    e.stopPropagation();
                }});

                canvas.addEventListener('mousedown', (e) => {{
                    if (e.button === 2) {{
                        e.preventDefault();
                        isDrawing = true;
                        const coords = getImageCoords(e);
                        startX = coords.x;
                        startY = coords.y;
                    }}
                }});

                canvas.addEventListener('mousemove', (e) => {{
                    if (isDrawing) {{
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
                        coordsDiv.textContent = `框选中: (${{x1}}, ${{y1}}) → (${{x2}}, ${{y2}})`;
                    }}
                }});

                canvas.addEventListener('mouseup', (e) => {{
                    if (isDrawing && e.button === 2) {{
                        isDrawing = false;
                        const coords = getImageCoords(e);
                        currentBox = {{
                            x1: Math.min(startX, coords.x),
                            y1: Math.min(startY, coords.y),
                            x2: Math.max(startX, coords.x),
                            y2: Math.max(startY, coords.y)
                        }};
                        coordsDiv.textContent = `已框选: (${{currentBox.x1}}, ${{currentBox.y1}}) → (${{currentBox.x2}}, ${{currentBox.y2}})`;
                        redrawBox();
                    }}
                }});

                clearBtn.addEventListener('click', () => {{
                    currentBox = null;
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    coordsDiv.textContent = '';
                }});

                applyBtn.addEventListener('click', () => {{
                    if (currentBox) {{
                        const coordsStr = `${{currentBox.x1}},${{currentBox.y1}},${{currentBox.x2}},${{currentBox.y2}}`;
                        window.parent.postMessage({{
                            type: 'boxCoords',
                            coords: coordsStr
                        }}, '*');
                    }}
                }});

                {'if ("' + box_coords_str + '") {'}
                    const [x1, y1, x2, y2] = '{box_coords_str}'.split(',').map(Number);
                    currentBox = {{ x1, y1, x2, y2 }};
                    coordsDiv.textContent = `已框选: (${{x1}}, ${{y1}}) → (${{x2}}, ${{y2}})`;
                    setTimeout(resizeCanvas, 200);
                {'}'}
            </script>
        </body>
        </html>
        """
        
        st.components.v1.html(canvas_html, height=img_height + 200)
        
        st.markdown("---")
        
        col_apply, col_clear, col_refresh = st.columns(3)
        with col_clear:
            if st.button("🗑️ 清除框选", use_container_width=True):
                st.session_state.box_coords = None
                st.rerun()
        with col_refresh:
            if st.button("🔄 重新框选", use_container_width=True):
                st.session_state.box_coords = None
                st.rerun()
        
        st.markdown("---")
        
        col_start, col_end = st.columns(2)
        with col_start:
            x1 = st.number_input("起点 X", min_value=0, max_value=img_width, value=st.session_state.box_coords[0] if st.session_state.box_coords else 0)
            y1 = st.number_input("起点 Y", min_value=0, max_value=img_height, value=st.session_state.box_coords[1] if st.session_state.box_coords else 0)
        with col_end:
            x2 = st.number_input("终点 X", min_value=0, max_value=img_width, value=st.session_state.box_coords[2] if st.session_state.box_coords else img_width)
            y2 = st.number_input("终点 Y", min_value=0, max_value=img_height, value=st.session_state.box_coords[3] if st.session_state.box_coords else img_height)
        
        if st.button("✅ 应用坐标", use_container_width=True):
            st.session_state.box_coords = (
                min(x1, x2),
                min(y1, y2),
                max(x1, x2),
                max(y1, y2)
            )
            st.rerun()

with col2:
    st.header("👁️ 生成结果预览")
    
    if st.session_state.generated_result:
        if "error" in st.session_state.generated_result:
            st.error(f"错误: {st.session_state.generated_result['error']}")
        elif "choices" in st.session_state.generated_result:
            result_text = st.session_state.generated_result["choices"][0]["message"]["content"]
            st.markdown(result_text)
            
            st.download_button(
                label="📥 下载结果",
                data=json.dumps(st.session_state.generated_result, ensure_ascii=False, indent=2),
                file_name="generated_result.json",
                mime="application/json"
            )
    else:
        if st.session_state.uploaded_image is not None:
            st.info("选择功能按钮后，生成结果将在此显示")
        else:
            st.info("请先在左侧上传图片")

with col3:
    st.header("⚙️ 设置")
    
    with st.expander("API 配置", expanded=True):
        st.session_state.api_config["api_key"] = st.text_input("API Key", value=st.session_state.api_config["api_key"], type="password")
        st.session_state.api_config["api_url"] = st.text_input("API URL", value=st.session_state.api_config["api_url"])
        st.session_state.api_config["model"] = st.text_input("Model", value=st.session_state.api_config["model"])
    
    st.markdown("---")
    
    with st.expander("➕ 添加新功能按钮", expanded=True):
        new_button_name = st.text_input("按钮名字")
        new_prompt = st.text_area("提示词")
        if st.button("保存按钮"):
            if new_button_name and new_prompt:
                st.session_state.buttons.append({
                    "name": new_button_name,
                    "prompt": new_prompt
                })
                st.success(f"按钮 '{new_button_name}' 已添加！")
                st.rerun()
            else:
                st.error("请输入按钮名字和提示词")
    
    st.markdown("---")
    
    if st.session_state.buttons:
        st.subheader("📋 已添加的按钮")
        
        for i, btn in enumerate(st.session_state.buttons):
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                st.write(f"**{btn['name']}**: {btn['prompt']}")
            with col_btn2:
                if st.button(f"删除", key=f"del_{i}"):
                    st.session_state.buttons.pop(i)
                    st.rerun()
        
        st.markdown("---")
        
        st.subheader("🚀 选择功能生成")
        
        if st.session_state.uploaded_image is not None:
            display_bytes = st.session_state.image_bytes
            
            if st.session_state.box_coords:
                display_bytes = draw_box_on_image(
                    st.session_state.image_bytes,
                    st.session_state.box_coords,
                    st.session_state.box_color,
                    st.session_state.box_width
                )
            
            btn_cols_settings = st.columns(2)
            for i, btn in enumerate(st.session_state.buttons):
                with btn_cols_settings[i % 2]:
                    if st.button(f"{btn['name']}", key=f"gen_{i}", use_container_width=True):
                        with st.spinner(f"正在使用 '{btn['name']}' 生成..."):
                            result = call_api(display_bytes, btn['prompt'], st.session_state.api_config)
                            st.session_state.generated_result = result
                            st.rerun()
        else:
            st.info("请先在左侧上传图片")
