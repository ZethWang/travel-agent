# AI 旅行规划助手 - 模块化版本

## 项目结构

这个项目已经被重构为模块化架构，便于维护和扩展。

### 文件结构

```
├── config.py           # 配置文件（API密钥、模型配置等）
├── frontend.py         # Streamlit前端界面模块
├── agents.py          # 多智能体定义模块
├── tools_config.py    # MCP工具配置模块
├── main.py           # 主入口文件
├── app_new.py        # 简化运行脚本
├── app.py            # 原始单文件版本（保留）
└── README.md         # 本文件
```

### 模块说明

#### 1. `config.py` - 配置管理
- API密钥默认值
- 模型配置参数
- UI组件选项
- 环境变量设置

#### 2. `frontend.py` - 前端界面
- `StreamlitUI`: 管理所有UI组件
- 侧边栏API密钥配置
- 主要内容区域渲染
- 用户输入验证
- 页面状态管理

#### 3. `agents.py` - AI代理系统
- `ModelManager`: 模型创建和管理
- `AgentFactory`: 创建不同类型的AI代理
  - 地图代理
  - 搜索代理
  - 预订代理
  - 时间管理代理
- `TeamManager`: 创建和管理代理团队
- `TravelPlannerService`: 旅行规划服务主类

#### 4. `tools_config.py` - 工具配置
- `ToolsManager`: MCP工具管理器
- 工具初始化和环境配置
- 异步上下文管理

#### 5. `main.py` - 主应用程序
- `TravelPlannerApp`: 应用程序主类
- 整合前端、后端和AI代理
- 异步旅行规划执行

## 使用方法

### 运行应用

```bash
# 使用新的模块化版本
streamlit run main.py

# 或使用简化脚本
streamlit run app_new.py

# 或继续使用原始版本
streamlit run app.py
```

### 配置API密钥

1. **默认配置**: 在 `config.py` 中设置默认API密钥
2. **运行时配置**: 在Streamlit侧边栏中输入API密钥
3. **环境变量**: 设置 `SEARCHAPI_API_KEY` 和 `OPENAI_API_KEY`

## 优势

### 1. 模块化设计
- 代码职责分离
- 易于维护和测试
- 支持独立开发和部署

### 2. 可扩展性
- 容易添加新的AI代理
- 支持新的模型提供商
- 可插拔的工具系统

### 3. 配置管理
- 集中化配置
- 环境特定设置
- 灵活的API密钥管理

### 4. 错误处理
- 更好的异常管理
- 详细的错误信息
- 优雅的失败处理

## 开发指南

### 添加新的AI代理

1. 在 `agents.py` 的 `AgentFactory` 中添加新方法
2. 在 `TeamManager.create_travel_team()` 中包含新代理
3. 更新代理的 `goal` 和工具描述

### 添加新的模型提供商

1. 在 `config.py` 中添加模型配置
2. 在 `agents.py` 的 `ModelManager` 中添加创建方法
3. 在 `frontend.py` 中更新UI选项和帮助信息

### 自定义工具

1. 修改 `config.py` 中的 `MCP_TOOLS_CONFIG`
2. 在 `tools_config.py` 中调整环境变量配置
3. 更新代理的工具描述

## 性能优化

- 异步执行提高响应速度
- 会话状态管理减少重复初始化
- 模块化加载降低内存使用

## 故障排除

### 常见问题

1. **API连接超时**: 检查网络连接和API密钥有效性
2. **模块导入错误**: 确保所有依赖模块在同一目录
3. **配置问题**: 验证 `config.py` 中的设置

### 调试模式

可以使用 `test_api.py` 脚本来测试API连接：

```bash
python test_api.py
```

## 贡献

欢迎提交Pull Request来改进项目。请确保：
- 遵循现有的代码结构
- 添加适当的注释和文档
- 测试新功能的兼容性

### 3. 日历 MCP 服务器
- **功能**：管理日历事件和日程安排
- **特性**：
  - 创建和管理日历事件
  - 处理时区转换
  - 安排提醒和通知
- **集成**：在 `calendar_mcp.py` 中实现

### 4. 预订 MCP 服务器
- **功能**：使用 Airbnb MCP 服务器


## 安装设置

### 环境要求

1. **API 密钥和凭证**：
    - **Google Maps API 密钥**：从 Google Cloud Console 设置 Google Maps API 密钥
    - **Google Calendar API**：启用并配置 Calendar API 密钥
    - **Google OAuth 凭证**：用于身份验证的客户端 ID、客户端密钥和刷新令牌
    - **AccuWeather API 密钥**：获取 AccuWeather API 密钥 https://developer.accuweather.com/
    - **OpenAI API 密钥**：在 OpenAI 注册以获取 API 密钥。

2. **Python 3.8+**：确保已安装 Python 3.8 或更高版本。

### 安装步骤

1. 克隆此仓库：
   ```bash
   git clone https://github.com/yourusername/ai_travel_planner_mcp_agent_team
   cd ai_travel_planner_mcp_agent_team
   ```

2. 安装所需的 Python 包：
   ```bash
   pip install -r requirements.txt
   ```

3. 设置环境变量：
   在项目根目录创建 `.env` 文件，包含以下变量：
   ```
   GOOGLE_CLIENT_ID=
   GOOGLE_CLIENT_SECRET=
   GOOGLE_REFRESH_TOKEN=
   GOOGLE_MAPS_API_KEY=
   OPENAI_API_KEY=
   ACCUWEATHER_API_KEY=
   ```

### 运行应用

1. 为 Google Calendar 生成 OAuth 令牌

2. 启动 Streamlit 应用：
   ```bash
   streamlit run app.py
   ```

3. 在应用界面中：
   - 使用侧边栏配置您的偏好设置
   - 输入您的旅行详情

## 项目结构

- `app.py`：主要的 Streamlit 应用程序
- `calendar_mcp.py`：日历 MCP 集成功能
- `requirements.txt`：项目依赖
- `.env`：环境变量

## 日历 MCP 集成

`calendar_mcp.py` 模块通过 MCP（模型上下文协议）框架提供与 Google Calendar 的无缝集成。此集成允许旅行规划助手：

- **创建事件**：自动为旅行活动、航班和住宿创建日历事件
- **日程管理**：处理时区转换和日程冲突
- **事件详情**：包含全面的事件信息，如：
  - 带有 Google Maps 链接的位置详情
  - 事件时间的天气预报
  - 旅行时长和交通详情
  - 备注和提醒

### 日历设置

1. **OAuth 认证**：
   - 应用程序使用 OAuth 2.0 与 Google Calendar 进行安全认证
   - 首次设置需要生成刷新令牌
   - 刷新令牌安全存储在 `.env` 文件中

2. **事件创建**：
   ```python
   # 创建日历事件的示例
   event = {
       'summary': '飞往巴黎的航班',
       'location': '戴高乐机场',
       'description': '航班详情和天气预报',
       'start': {'dateTime': '2024-04-20T10:00:00', 'timeZone': 'Europe/Paris'},
       'end': {'dateTime': '2024-04-20T12:00:00', 'timeZone': 'Europe/Paris'}
   }
   ```
