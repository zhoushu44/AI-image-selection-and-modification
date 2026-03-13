import requests
import base64
from PIL import Image
import io

# API配置
API_URL = "https://api.nofx.online/v1/chat/completions"
API_KEY = "sk-muDiVOc0MZmkpSWMLguFlJhmWRq4707fgKDTfMHSsMPctZxi"
MODEL = "gemini-3.1-flash-image-square"

# 读取并编码图片
image_path = r"E:\360MoveData\Users\Administrator\Desktop\图片编辑\1.jpeg"

with open(image_path, "rb") as f:
    image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

# 构建请求
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

payload = {
    "model": MODEL,
    "stream": True,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "一袋变成2袋"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ],
    "max_tokens": 2000
}

print("🔧 正在测试流式API...")
print(f"📋 API URL: {API_URL}")
print(f"📋 Model: {MODEL}")
print(f"📋 提示词: 一袋变成2袋")
print("-" * 50)

try:
    response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=120)
    print(f"📊 响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("\n✅ 流式响应开始...")
        print("-" * 50)
        
        full_content = ""
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_str = line_text[6:]
                    if data_str != '[DONE]':
                        try:
                            import json
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    print(content, end='', flush=True)
                                    full_content += content
                        except Exception as e:
                            pass
        
        print("\n" + "=" * 50)
        print("\n💬 完整内容:")
        print("=" * 50)
        print(full_content)
    else:
        print(f"\n❌ API请求失败")
        print(f"响应内容: {response.text}")
        
except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
