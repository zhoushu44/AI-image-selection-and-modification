import requests
import base64
from PIL import Image
import io

# API配置
API_URL = "https://api.nofx.online/v1/images/edits"
API_KEY = "sk-muDiVOc0MZmkpSWMLguFlJhmWRq4707fgKDTfMHSsMPctZxi"
MODEL = "gemini-3.1-flash-image-square"

# 读取图片
image_path = r"E:\360MoveData\Users\Administrator\Desktop\图片编辑\1.jpeg"

with open(image_path, "rb") as f:
    image_bytes = f.read()

# 构建请求
headers = {
    "Authorization": f"Bearer {API_KEY}"
}

files = {
    "image": ("image.jpg", image_bytes, "image/jpeg")
}

data = {
    "model": MODEL,
    "prompt": "一袋变成2袋",
    "n": 1,
    "size": "1024x1024"
}

print("🔧 正在测试图片编辑API...")
print(f"📋 API URL: {API_URL}")
print(f"📋 Model: {MODEL}")
print(f"📋 提示词: 一袋变成2袋")
print("-" * 50)

try:
    response = requests.post(API_URL, headers=headers, files=files, data=data, timeout=120)
    print(f"📊 响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ API测试成功！")
        print("\n📋 完整响应:")
        print("-" * 50)
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if "data" in result and len(result["data"]) > 0:
            image_url = result["data"][0].get("url") or result["data"][0].get("b64_json")
            print("\n" + "=" * 50)
            print("🖼️ 生成的图片:")
            print("=" * 50)
            if image_url:
                print(image_url)
    else:
        print(f"\n❌ API请求失败")
        print(f"响应内容: {response.text}")
        
except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
