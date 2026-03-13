# 图片编辑与AI生成应用

一个基于 Flask + Supabase 的完整图片编辑与 AI 生成 Web 应用，支持用户认证、积分系统、私有按钮配置等企业级功能。

## ✨ 功能特点

### 🔐 用户认证系统
- **注册/登录**：基于 Supabase Auth 的安全认证
- **邮箱验证**：支持邮箱验证（可配置）
- **会话管理**：安全的 Session 管理

### 💰 积分系统
- **新用户注册**：自动赠送 10 积分
- **每日领取**：每天可免费领取 10 积分
- **生成扣除**：每次成功生成图片扣除 2 积分
- **失败退款**：生成失败自动退还积分
- **积分明细**：完整的积分交易记录查询

### 📁 图片上传与框选
- 支持 JPG、PNG、JPEG 格式图片上传
- 鼠标左键拖拽框选
- 6 种颜色选择（蓝、绿、橙、灰、白、红）
- 3 种粗细可选（细 3px、中 6px、粗 10px）
- 清除框选功能

### 🔧 API 配置（安全存储）
- API Key、API URL、Model 安全存储在 Supabase 数据库
- 前端不暴露任何 API 配置
- 支持 OpenAI 格式的 API

### 🎯 私有功能按钮管理
- **全局模板**：管理员可设置全局按钮模板
- **用户私有**：每个用户有独立的按钮配置空间
- **自动初始化**：新用户首次访问自动复制全局模板
- **自定义按钮**：用户可添加、删除自己的按钮
- **数据隔离**：用户只能访问和修改自己的配置

### 🚀 生成与展示
- 点击功能按钮发送框选图片和提示词到 API
- 支持多次生成，结果依次展示
- 每个结果独立加载状态
- Markdown 图片链接自动解析
- 图片防盗链处理
- 下载生成的图片

### 💾 结果管理
- 多个结果卡片式展示
- 每个结果可单独下载
- 一键清除所有结果

## 🏗️ 项目架构

```
AI-image-selection-and-modification/
├── app_complete.py              # 主应用文件
├── requirements.txt             # 依赖列表
├── sql/
│   └── create_tables_simple.sql # 数据库表结构
├── 1.jpeg                       # 测试图片
├── Dockerfile                   # Docker 配置
├── .github/
│   └── workflows/
│       └── main.yml             # GitHub Actions 自动部署
└── README.md                    # 说明文档
```

## 🛠️ 技术栈

- **后端框架**: Flask
- **数据库**: Supabase PostgreSQL
- **用户认证**: Supabase Auth
- **图片处理**: Pillow
- **HTTP 请求**: requests
- **前端**: HTML + CSS + JavaScript
- **设计风格**: Minimalist Monochrome 极简单色

## 🚀 部署教程

### 前置准备

1. **注册 Supabase 账号**
   - 访问 https://supabase.com
   - 注册并创建新项目
   - 记录项目 URL 和 API Key

2. **获取 Supabase 密钥**
   - 进入项目 → Settings → API
   - 复制 `URL` 和 `anon public`（Anon Key）
   - 复制 `service_role secret`（Secret Key）

---

### 方式一：本地开发运行（推荐新手）

#### 步骤 1：克隆或下载项目
```bash
cd AI-image-selection-and-modification
```

#### 步骤 2：配置 Supabase
编辑 `app_complete.py` 文件，修改以下配置：
```python
SUPABASE_URL = "你的项目URL"
SUPABASE_ANON_KEY = "你的Anon Key"
SUPABASE_SECRET_KEY = "你的Secret Key"
```

#### 步骤 3：安装依赖
```bash
pip install -r requirements.txt
```

#### 步骤 4：创建数据库表
- 打开 Supabase 项目控制台
- 进入 SQL Editor
- 打开 `sql/create_tables_simple.sql` 文件
- 复制全部内容并在 SQL Editor 中执行

#### 步骤 5：启动应用
```bash
python app_complete.py
```

#### 步骤 6：访问应用
打开浏览器访问：http://localhost:5000

---

### 方式二：Docker 部署

#### 构建镜像
```bash
docker build -t ai-image-app .
```

#### 运行容器
```bash
docker run -d \
  -p 5000:5000 \
  -e SUPABASE_URL="你的URL" \
  -e SUPABASE_ANON_KEY="你的AnonKey" \
  -e SUPABASE_SECRET_KEY="你的SecretKey" \
  ai-image-app
```

---

### 方式三：使用 GitHub Actions 自动部署到 Docker Hub

1. Fork 本项目到你的 GitHub
2. 在 GitHub 仓库 Settings → Secrets 中添加：
   - `DOCKER_HUB_USERNAME`: 你的 Docker Hub 用户名
   - `DOCKER_HUB_TOKEN`: 你的 Docker Hub Token
3. 推送代码到 main 分支，自动构建并推送镜像

## 📖 使用说明

### 第一步：注册账号
1. 打开应用
2. 点击"注册"标签
3. 输入邮箱和密码
4. 点击"注册"按钮
5. （可选）验证邮箱

### 第二步：登录系统
1. 使用注册的邮箱和密码登录
2. 登录后自动获得 10 积分（新用户）
3. 自动获得 8 个默认功能按钮

### 第三步：上传图片
1. 点击"选择文件"上传图片
2. 图片会在第一列显示

### 第四步：框选（可选）
1. 在图片上按住鼠标左键拖拽进行框选
2. 可选择框的颜色和粗细
3. 点击"清除框选"重置

### 第五步：使用功能按钮生成
1. 在"选择功能生成"区域点击按钮
2. 结果会在第二列显示
3. 可多次点击生成多个结果
4. 每次生成扣除 2 积分

### 第六步：管理你的按钮
1. 展开"添加新功能"面板
2. 输入按钮名字和提示词
3. 点击"保存按钮"
4. 展开"已添加的按钮"可以查看和删除

### 第七步：积分管理
1. 点击顶部的"积分"按钮查看详情
2. 点击"领取每日积分"领取 10 积分（每天一次）
3. 查看积分明细记录

### 第八步：下载图片
1. 点击结果卡片中的"下载结果"按钮
2. 图片会自动下载

## 🎨 数据库表结构

### api_config - API 配置表
存储 API Key、URL、Model 等配置（仅后端访问）

### user_points - 用户积分表
存储每个用户的当前积分和每日领取记录

### point_transactions - 积分交易记录表
记录每一笔积分变动（收入/支出）

### generation_records - 生成记录表
记录每次图片生成的详细信息

### global_button_templates - 全局按钮模板表
存储所有用户共用的初始按钮模板（仅管理员可修改）

### user_buttons - 用户私有按钮表
存储单个用户的所有按钮配置

## ⚙️ Supabase 配置建议

### Auth 设置
1. 进入 Authentication → Providers
2. 启用 Email 提供商
3. （可选）关闭 Confirm email 可跳过邮箱验证

### RLS 策略
所有表都已启用 RLS（Row Level Security），确保数据安全：
- 用户只能访问自己的积分、交易记录、按钮配置
- 全局模板表仅后端可访问
- API 配置表仅后端可访问

## 🔒 安全特性

1. **API 配置安全存储**：不在前端暴露任何 API Key
2. **数据隔离**：基于 Supabase RLS 的严格数据隔离
3. **双 Key 架构**：
   - Anon Key：仅用于 Auth（注册/登录）
   - Secret Key：用于数据库操作（后端）
4. **无数据库触发器**：避免触发器导致的注册问题
5. **后端初始化**：所有用户数据初始化通过后端代码完成

## 📝 注意事项

1. 确保网络连接正常，能够访问 API 服务
2. 积分不足时请先领取每日积分
3. 生成大图片可能需要较长时间，请耐心等待
4. 如遇问题可查看浏览器控制台和终端日志
5. 首次部署务必先在 Supabase 执行 SQL 创建表

## 🆘 常见问题

### Q: 注册失败提示 "Database error saving new user"
A: 确保已在 Supabase 执行了 `sql/create_tables_simple.sql`，并且没有其他数据库触发器。

### Q: 没有看到功能按钮
A: 新用户首次登录会自动初始化按钮，如果没有请刷新页面试试。

### Q: 积分没有增加
A: 查看积分详情弹窗中的交易记录，确认积分变动。

## 📄 许可证

MIT License

## 🙏 致谢

- Flask - Web 框架
- Supabase - 后端即服务
- Pillow - 图片处理
- Minimalist Monochrome - 设计灵感
