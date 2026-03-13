import requests
import base64
import json

# 测试图片路径
IMAGE_PATH = "e:\\360MoveData\\Users\\Administrator\\Desktop\\图片编辑\\1.jpeg"

# API配置
API_KEY = "96d739dd-5f53-4a6d-b89d-1779f27be846"
API_URL = "https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions"
MODEL = "ark-code-latest"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_api():
    print("开始测试API...")
    
    # 读取并编码图片
    try:
        base64_image = encode_image(IMAGE_PATH)
        print("✓ 图片编码成功")
    except Exception as e:
        print(f"✗ 图片编码失败: {e}")
        return
    
    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 构建请求体（先测试简单的文本请求）
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "你好，请简单介绍一下自己"
            }
        ],
        "max_tokens": 100
    }
    
    print(f"\nAPI URL: {API_URL}")
    print(f"Model: {MODEL}")
    print(f"\n发送测试请求...")
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✓ API测试成功！")
        else:
            print("\n✗ API测试失败")
    except Exception as e:
        print(f"\n✗ 请求失败: {e}")

if __name__ == "__main__":
    test_api()
