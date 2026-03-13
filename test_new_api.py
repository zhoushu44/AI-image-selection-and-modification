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

print("🔧 正在测试API...")
print(f"📋 API URL: {API_URL}")
print(f"📋 Model: {MODEL}")
print(f"📋 提示词: 一袋变成2袋")
print("-" * 50)

try:
    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    print(f"📊 响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ API测试成功！")
        print("\n📋 完整响应:")
        print("-" * 50)
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print("\n" + "=" * 50)
            print("💬 生成内容:")
            print("=" * 50)
            print(content)
    else:
        print(f"\n❌ API请求失败")
        print(f"响应内容: {response.text}")
        
except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
