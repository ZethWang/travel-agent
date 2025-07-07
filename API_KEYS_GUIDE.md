# API 密钥获取指南

这个旅行规划助手现在支持两种AI模型提供商：OpenAI 和 Google Gemini。请根据您的选择获取相应的API密钥。

## 🤖 OpenAI API 密钥

1. 访问 [OpenAI API Keys](https://platform.openai.com/api-keys)
2. 登录或注册 OpenAI 账户
3. 点击 "Create new secret key"
4. 复制生成的 API 密钥
5. 在应用侧边栏选择 "OpenAI" 并输入密钥

**推荐模型**: GPT-4o-mini (成本效益高，性能优秀)

## 🌟 Google Gemini API 密钥

1. 访问 [Google AI Studio](https://aistudio.google.com/apikey)
2. 登录您的 Google 账户
3. 点击 "Create API Key"
4. 复制生成的 API 密钥
5. 在应用侧边栏选择 "Gemini" 并输入密钥

**推荐模型**: Gemini 2.0 Flash (最新模型，支持多模态)

## 🗺️ 其他必需的 API 密钥

### 高德地图 API 密钥
1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 注册并登录账户
3. 创建应用并获取 API Key

### Google Maps API 密钥
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建项目并启用 Maps API
3. 生成 API 密钥

### AccuWeather API 密钥
1. 访问 [AccuWeather Developer](https://developer.accuweather.com/)
2. 注册账户并创建应用
3. 获取 API 密钥

### Google Calendar API 配置
1. 在 Google Cloud Console 中启用 Calendar API
2. 创建 OAuth 2.0 凭据
3. 获取客户端 ID、客户端密钥和刷新令牌

## 💡 选择建议

- **OpenAI GPT-4o-mini**: 适合需要快速响应和成本控制的场景
- **Google Gemini 2.0 Flash**: 适合需要最新AI能力和多模态处理的场景

## 🔒 安全提醒

- 不要在代码中硬编码 API 密钥
- 定期轮换您的 API 密钥
- 设置适当的使用限制和预警
- 监控 API 使用情况和费用
