import asyncio
import os
from datetime import date
from fpdf import FPDF
import io
import base64

from agno.agent import Agent
from agno.tools.mcp import MultiMCPTools
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
import streamlit as st

# 配置页面 - 必须是第一个 Streamlit 命令
st.set_page_config(
    page_title="AI 旅行规划助手",
    page_icon="✈️",
    layout="wide"
)

# 设置默认的API密钥环境变量
os.environ.setdefault("SEARCHAPI_API_KEY", "5722Vw5rYoJTVHyffqNph3F4")
# os.environ.setdefault("OPENAI_API_KEY", "sk-FxhjDpv1D62n33JGICef3aVagezAr73GFnoXmSQ4ikMpf9Hb")
os.environ.setdefault("OPENAI_API_KEY", "sk-widDrKmkgrnCsmVg281bD224F984400eBb4586657a519a68")

def create_travel_plan_pdf(travel_plan_text, source, destination, travel_dates, budget):
    """创建旅行计划的PDF文档"""
    try:
        # 创建PDF对象
        pdf = FPDF()
        pdf.add_page()
        
        # 设置字体
        pdf.set_font('Arial', 'B', 16)
        
        # 处理文本，转换为ASCII兼容格式
        def clean_text(text):
            import re
            # 移除或替换特殊字符，保留基本标点
            text = re.sub(r'[^\x00-\x7F]+', ' ', str(text))  # 移除非ASCII字符
            text = re.sub(r'\s+', ' ', text)  # 合并多个空格
            return text.strip()
        
        # 清理输入数据
        source_clean = clean_text(source)
        destination_clean = clean_text(destination)
        
        # 标题
        try:
            pdf.cell(0, 10, f'AI Travel Plan: {source_clean} to {destination_clean}', 0, 1, 'C')
        except:
            pdf.cell(0, 10, 'AI Travel Plan', 0, 1, 'C')
        pdf.ln(5)
        
        # 基本信息
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, f'From: {source_clean}', 0, 1)
        pdf.cell(0, 8, f'To: {destination_clean}', 0, 1)
        pdf.cell(0, 8, f'Dates: {travel_dates[0]} to {travel_dates[1]}', 0, 1)
        pdf.cell(0, 8, f'Budget: ${budget} USD', 0, 1)
        pdf.ln(8)
        
        # 旅行计划内容
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, 'Travel Plan Details:', 0, 1)
        pdf.ln(3)
        
        # 处理旅行计划文本
        clean_plan = clean_text(travel_plan_text)
        
        # 分行处理
        lines = clean_plan.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # 处理长行
                while len(line) > 85:
                    break_point = line.rfind(' ', 0, 85)
                    if break_point == -1:
                        break_point = 85
                    
                    try:
                        pdf.cell(0, 5, line[:break_point], 0, 1)
                    except:
                        pdf.cell(0, 5, 'Content contains special characters', 0, 1)
                    line = line[break_point:].strip()
                
                if line:
                    try:
                        pdf.cell(0, 5, line, 0, 1)
                    except:
                        pdf.cell(0, 5, 'Content contains special characters', 0, 1)
            else:
                pdf.ln(2)
        
        # 返回PDF字节数据
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        # 如果还是失败，创建一个简化版本
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'AI Travel Plan', 0, 1, 'C')
            pdf.ln(5)
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 8, f'Budget: ${budget} USD', 0, 1)
            pdf.cell(0, 8, f'Date: {travel_dates[0]} to {travel_dates[1]}', 0, 1)
            pdf.ln(5)
            pdf.cell(0, 8, 'Travel plan contains special characters.', 0, 1)
            pdf.cell(0, 8, 'Please refer to the web version for full details.', 0, 1)
            return pdf.output(dest='S').encode('latin-1')
        except Exception as e2:
            st.error(f"PDF生成失败: {str(e2)}")
            return None

def create_download_link(pdf_bytes, filename):
    """创建PDF下载链接"""
    if pdf_bytes:
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📄 下载PDF旅行计划</a>'
        return href
    return None

def create_text_download_link(text_content, filename):
    """创建文本文件下载链接"""
    try:
        # 清理文本内容
        clean_content = text_content.encode('utf-8', errors='ignore').decode('utf-8')
        b64 = base64.b64encode(clean_content.encode('utf-8')).decode()
        href = f'<a href="data:text/plain;charset=utf-8;base64,{b64}" download="{filename}">📄 下载文本版旅行计划</a>'
        return href
    except Exception as e:
        return None

# Remove dotenv import and loading since we'll use sidebar
# from dotenv import load_dotenv
# load_dotenv()

# 移除团队配置导入，单智能体不需要团队配置
# try:
#     from team_config import AGENT_CONFIGS, TEAM_CONFIG, WORKFLOW_CONFIG
# except ImportError:
#     # 如果配置文件不存在，使用默认配置
#     AGENT_CONFIGS = None
#     TEAM_CONFIG = {"show_chain_of_thought": True}
#     WORKFLOW_CONFIG = None

def display_agent_status():
    """显示智能体状态和工作流程"""
    with st.expander("🤖 AI 旅行规划专家状态", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🧠 AI 旅行规划专家")
            st.markdown("""
            **状态**: 待命中 ⏳
            **AI模型**: GPT-4o-mini / Gemini-2.0-flash-exp
            **专业领域**: 全方位旅行规划
            **核心能力**:
            - 信息搜索与验证
            - 行程规划与优化
            - 预算分析与控制
            - 个性化推荐
            """)
            
        with col2:
            st.markdown("### �️ 工具集") 
            st.markdown("""
            **搜索工具**:
            - Google地图搜索
            - Google航班搜索  
            - Google酒店搜索
            - 综合信息搜索
            - 地点评论获取
            - 视频搜索
            """)
        
        st.markdown("### 🔄 工作流程")
        st.markdown("""
        1. **需求分析** (30秒) - 解析用户需求和偏好
        2. **信息收集** (2-3分钟) - 搜索目的地、航班、酒店等信息  
        3. **方案制定** (2-3分钟) - 整合信息并制定旅行方案
        4. **优化完善** (1分钟) - 优化行程安排和预算分配
        """)

def create_progress_tracker():
    """创建进度跟踪器"""
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    def update_progress(step, total_steps, message):
        progress = step / total_steps
        progress_placeholder.progress(progress)
        status_placeholder.info(f"🔄 {message}")
    
    return update_progress

async def run_travel_agent(message: str):
    """使用单智能体运行旅行规划任务，集成信息收集和行程规划功能。"""

    # 从会话状态获取 API 密钥
    searchapi_key = st.session_state.get('searchapi_key')
    openai_key = st.session_state.get('openai_key')
    gemini_key = st.session_state.get('gemini_key')
    model_provider = st.session_state.get('model_provider', 'OpenAI')

    if not searchapi_key:
        raise ValueError("🚨 缺少 SearchAPI API 密钥。请在侧边栏中输入。")
    elif model_provider == 'OpenAI' and not openai_key:
        raise ValueError("🚨 缺少 OpenAI API 密钥。请在侧边栏中输入。")
    elif model_provider == 'Gemini' and not gemini_key:
        raise ValueError("🚨 缺少 Gemini API 密钥。请在侧边栏中输入。")

    # 设置环境变量
    env = {
        **os.environ,
        "SEARCHAPI_API_KEY": searchapi_key
    }
    
    if model_provider == 'OpenAI':
        env["OPENAI_API_KEY"] = openai_key
    elif model_provider == 'Gemini':
        env["GOOGLE_API_KEY"] = gemini_key

    # 根据选择的模型提供商初始化模型
    if model_provider == 'OpenAI':
       
        travel_model = OpenAIChat(
            id="gpt-4.1",  # 使用xi-ai支持的模型
            api_key=openai_key,  # 使用新的API密钥
            base_url="https://api.xi-ai.cn/v1",  # 使用新的API URL
        )
    elif model_provider == 'Gemini':
        # 使用Gemini模型
        travel_model = Gemini(id="gemini-2.0-flash-exp", api_key=gemini_key)

    async with MultiMCPTools(
        ["python /mnt/public/code/zzy/wzh/doremi/searchAPI-mcp/mcp_server.py"],
        env=env,
    ) as mcp_tools:
        
        # 创建单个全能旅行规划智能体
        travel_agent = Agent(
            tools=[mcp_tools],
            model=travel_model,
            name="AI旅行规划专家",
            instructions="""
            作为专业的AI旅行规划专家，你具备全方位的旅行规划能力，能够独立完成从信息收集到行程规划的全部工作。

            ## 核心职责：
            
            ### 📊 信息收集与分析
            1. **目的地调研**: 使用搜索工具收集目的地的景点、文化、气候、安全等基本信息
            2. **航班搜索**: 使用Google航班搜索工具查找最佳航班选项和价格
            3. **住宿搜索**: 使用Google酒店搜索工具查找符合用户偏好和预算的住宿选项
            4. **餐饮推荐**: 搜索当地特色餐厅、美食推荐，考虑用户的饮食限制
            5. **交通规划**: 收集当地交通信息、路线规划、交通费用等
            6. **活动搜索**: 根据用户偏好搜索相关的活动、景点、体验项目

            ### 🗓️ 行程规划与优化
            1. **需求分析**: 深入分析用户的旅行需求、偏好、预算和时间限制
            2. **行程设计**: 制定详细的日程安排，包括时间、地点、活动安排
            3. **路线优化**: 优化旅行路线，减少不必要的往返和时间浪费
            4. **预算管理**: 进行成本估算和预算分配，确保在用户预算范围内
            5. **个性化定制**: 根据用户偏好提供个性化的推荐和建议
            6. **备选方案**: 提供备选方案、应急计划和实用建议

            ### 💬 多轮对话和针对性回答
            当用户提供了旅行计划上下文和具体问题时：
            1. **理解上下文**: 仔细分析已有的旅行计划内容
            2. **针对性回答**: 基于现有计划回答用户的具体问题
            3. **计划调整**: 如果用户要求修改，提供具体的替代方案
            4. **深入细节**: 对计划中的特定内容提供更详细的信息
            5. **实用建议**: 提供相关的实用提示和注意事项

            ## 工作模式判断：
            - 如果用户消息包含"【当前旅行计划上下文】"，则说明这是针对已有计划的追问，请基于上下文进行针对性回答
            - 如果用户消息是全新的旅行规划请求，则执行完整的规划流程
            - 优先回答用户的具体问题，保持回答的相关性和实用性

            ## 输出标准：
            ### 完整旅行规划必须包含：
            - **航班预订建议**: 具体航班信息、时间、价格、预订链接
            - **住宿推荐**: 酒店信息、地址、价格、特色、预订建议
            - **详细行程**: 按天分解的活动安排，包括时间、地点、费用
            - **交通规划**: 机场接送、景点间交通、当地交通建议
            - **餐饮推荐**: 特色餐厅、美食推荐、用餐预算
            - **预算明细**: 详细的费用分解和预算控制建议
            - **实用信息**: 天气预报、重要提醒、紧急联系方式
            - **备选方案**: 每个主要环节的备用选择

            ### 针对性回答应包含：
            - **直接回答**: 针对用户问题的直接回答
            - **详细信息**: 提供相关的详细信息和建议
            - **替代方案**: 如果涉及修改，提供具体的替代选择
            - **实用提示**: 相关的注意事项和建议

            ## 质量要求：
            - **准确性**: 所有信息都经过搜索验证，确保准确可靠
            - **实用性**: 提供具体可执行的预订和行动指导
            - **个性化**: 充分体现用户的偏好和需求
            - **相关性**: 针对用户的具体问题进行回答
            - **时间合理**: 行程安排时间充裕且高效
            - **完整性**: 涵盖用户询问的所有重要方面

            ## 注意事项：
            - 使用搜索工具获取最新、准确的信息
            - 考虑当地的季节性因素和营业时间
            - 基于已有计划上下文进行针对性回答
            - 保持预算透明和可控
            - 提供实用且可执行的建议
            """,
            goal="""为用户提供完整、准确、个性化的旅行规划方案，确保用户获得最佳的旅行体验。"""
        )
        
        # 运行智能体
        result = await travel_agent.arun(message)
        
        # 获取响应内容
        if hasattr(result, 'content'):
            return result.content
        elif hasattr(result, 'messages') and result.messages:
            return result.messages[-1].content if hasattr(result.messages[-1], 'content') else str(result.messages[-1])
        else:
            return str(result)  
    
# -------------------- Streamlit 应用 --------------------
    
# 为 API 密钥添加侧边栏
with st.sidebar:
    st.header("🔑 API 密钥配置")
    st.markdown("请输入您的 API 密钥以使用旅行规划助手。")
    
    # 模型提供商选择
    if 'model_provider' not in st.session_state:
        st.session_state.model_provider = "OpenAI"
    
    st.session_state.model_provider = st.selectbox(
        "🤖 选择AI模型提供商",
        ["OpenAI", "Gemini"],
        index=["OpenAI", "Gemini"].index(st.session_state.model_provider),
        help="选择您喜欢的AI模型提供商"
    )
    
    # 如果会话状态中不存在 API 密钥，则初始化（使用环境变量作为默认值）
    if 'searchapi_key' not in st.session_state:
        st.session_state.searchapi_key = os.environ.get("SEARCHAPI_API_KEY", "")
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = os.environ.get("OPENAI_API_KEY", "")
    if 'gemini_key' not in st.session_state:
        st.session_state.gemini_key = ""

    # API 密钥输入字段
    st.session_state.searchapi_key = st.text_input(
        "SearchAPI 密钥",
        value=st.session_state.searchapi_key,
        type="password",
        help="用于访问Google搜索、地图、酒店、航班等所有搜索功能"
    )
    
    # 根据选择的模型提供商显示相应的API密钥输入
    if st.session_state.model_provider == "OpenAI":
        st.session_state.openai_key = st.text_input(
            "OpenAI API 密钥",
            value=st.session_state.openai_key,
            type="password",
            help="用于GPT模型的API访问"
        )
    elif st.session_state.model_provider == "Gemini":
        st.session_state.gemini_key = st.text_input(
            "Gemini API 密钥",
            value=st.session_state.gemini_key,
            type="password",
            help="用于Google Gemini模型的API访问"
        )
    
    # 检查是否填写了所有必需的 API 密钥
    required_keys = [
        st.session_state.searchapi_key
    ]
    
    # 根据选择的模型添加相应的API密钥检查
    if st.session_state.model_provider == "OpenAI":
        required_keys.append(st.session_state.openai_key)
    elif st.session_state.model_provider == "Gemini":
        required_keys.append(st.session_state.gemini_key)
    
    all_keys_filled = all(required_keys)

    if not all_keys_filled:
        st.warning("⚠️ 请填写所有必需的 API 密钥以使用旅行规划助手。")
    else:
        st.success(f"✅ 所有 API 密钥已配置完成！当前使用：{st.session_state.model_provider}")
    
    # 显示当前选择的模型信息
    if st.session_state.model_provider == "OpenAI":
        st.info("🤖 OpenAI GPT-4o-mini")
        st.caption("✨ 特点：强大的语言理解、精准的信息搜索、专业的行程规划")
    elif st.session_state.model_provider == "Gemini":
        st.info("🌟 Google Gemini 2.0 Flash")
        st.caption("✨ 特点：最新AI技术、多模态支持、创新性旅行建议")
    
    # 添加帮助链接
    with st.expander("📋 如何获取 API 密钥？"):
        st.markdown("""
        **SearchAPI 密钥获取步骤：**
        1. 访问 [SearchAPI.io](https://www.searchapi.io/)
        2. 注册账户并登录
        3. 在控制台中获取您的API密钥
        4. 复制并保存密钥
        
        **SearchAPI提供的功能：**
        - ✅ Google 搜索结果
        - ✅ Google 地图搜索
        - ✅ Google 酒店搜索
        - ✅ Google 航班搜索
        - ✅ 地点评论和评级
        - ✅ 视频搜索
        """)
        
        if st.session_state.model_provider == "OpenAI":
            st.markdown("""
            **OpenAI API 密钥获取步骤：**
            1. 访问 [OpenAI API Keys](https://platform.openai.com/api-keys)
            2. 登录或注册账户
            3. 点击 "Create new secret key"
            4. 复制并保存密钥
            
            **模型特点：**
            - 🧠 GPT-4o-mini：强大的语言理解和生成能力
            - � 精准搜索：准确理解用户需求，搜索相关信息
            - 📋 专业规划：基于搜索结果制定详细行程
            """)
        elif st.session_state.model_provider == "Gemini":
            st.markdown("""
            **Google Gemini API 密钥获取步骤：**
            1. 访问 [Google AI Studio](https://aistudio.google.com/apikey)
            2. 登录 Google 账户
            3. 点击 "Create API Key"
            4. 复制并保存密钥
            """)
    
    with st.expander("📦 PDF功能说明"):
        st.markdown("""
        **PDF下载功能：**
        - 自动生成完整的旅行计划PDF
        - 包含所有详细信息和推荐
        - 方便保存和分享
        
        **如果PDF功能不可用：**
        ```bash
        pip install fpdf2
        ```
        """)

# 标题和描述
st.title("✈️ AI 旅行规划助手")
st.markdown("""
这个 AI 驱动的旅行规划助手使用先进的**单智能体架构**，集成多种AI模型（OpenAI GPT 和 Google Gemini），通过SearchAPI.io提供全面的旅行服务：

### 🤖 AI 旅行规划专家
- **🧠 智能整合**: 单个全能智能体，集成信息收集和行程规划功能
- **🔍 全方位搜索**: 自动搜索航班、酒店、景点、餐厅等所有旅行信息
- **📋 智能规划**: 基于搜索结果自动制定个性化行程方案

### ✨ 核心功能特色
- 🤖 灵活模型选择：支持OpenAI GPT-4o-mini 或 Google Gemini 2.0
- 🗺️ 地图搜索和地点发现（通过SearchAPI的Google Maps功能）
- 🏨 酒店和住宿搜索
- ✈️ 航班信息和价格比较
- 📍 地点评论和评级
- 🔍 综合旅行信息搜索
- ⏰ 智能时间管理和行程规划
- 🎯 个性化推荐系统
- 💰 预算控制和成本优化
""")

# 创建两列用于输入
col1, col2 = st.columns(2)

with col1:
    # 出发地和目的地
    source = st.text_input("出发地", placeholder="输入您的出发城市")
    destination = st.text_input("目的地", placeholder="输入您的目的地城市")
    
    # 旅行日期
    travel_dates = st.date_input(
        "旅行日期",
        [date.today(), date.today()],
        min_value=date.today(),
        help="选择您的旅行日期"
    )

with col2:
    # 预算
    budget = st.number_input(
        "预算（美元）",
        min_value=0,
        max_value=10000,
        step=100,
        help="输入您的旅行总预算"
    )
    
    # 旅行偏好
    travel_preferences = st.multiselect(
        "旅行偏好",
        ["冒险", "休闲", "观光", "文化体验", 
         "海滩", "山区", "豪华", "经济实惠", "美食",
         "购物", "夜生活", "家庭友好"],
        help="选择您的旅行偏好"
    )

# 其他偏好设置
st.subheader("其他偏好设置")
col3, col4 = st.columns(2)

with col3:
    accommodation_type = st.selectbox(
        "首选住宿类型",
        ["任何", "酒店", "青年旅社", "公寓", "度假村"],
        help="选择您首选的住宿类型"
    )
    
    transportation_mode = st.multiselect(
        "首选交通方式",
        ["火车", "巴士", "飞机", "租车"],
        help="选择您首选的交通方式"
    )

with col4:
    dietary_restrictions = st.multiselect(
        "饮食限制",
        ["无", "素食", "纯素", "无麸质", "清真", "犹太洁食"],
        help="选择任何饮食限制"
    )

# 提交按钮和重置按钮
col_submit, col_reset = st.columns([3, 1])

with col_submit:
    submit_button = st.button("🚀 启动AI规划助手", type="primary", disabled=not all_keys_filled)

with col_reset:
    if st.session_state.get('travel_plan'):
        if st.button("🔄 重新规划", help="清除当前计划，开始新的规划"):
            st.session_state['travel_plan'] = None
            st.session_state['travel_context'] = {}
            st.session_state['messages'] = []
            st.rerun()

if submit_button:
    if not source or not destination:
        st.error("请输入出发地和目的地城市。")
    elif not travel_preferences:
        st.warning("建议选择一些旅行偏好以获得更好的推荐。")
    else:
        # 显示智能体状态
        display_agent_status()
        
        # 创建进度跟踪
        st.markdown("### 🔄 AI规划进度")
        progress_tracker = create_progress_tracker()
        
        # 开始处理
        with st.spinner("🤖 AI旅行规划专家正在为您制定完美的旅行方案..."):
            try:
                # 更新进度
                progress_tracker(1, 4, "正在初始化AI旅行规划专家...")
                
                # 为智能体构建详细消息
                message = f"""
                请为我制定一个完整的旅行规划方案：
                
                【基本信息】:
                - 出发地：{source}
                - 目的地：{destination}
                - 旅行日期：{travel_dates[0]} 到 {travel_dates[1]}
                - 预算：${budget} 美元
                - 旅行偏好：{', '.join(travel_preferences)}
                - 住宿类型偏好：{accommodation_type}
                - 交通方式偏好：{', '.join(transportation_mode)}
                - 饮食限制：{', '.join(dietary_restrictions)}
                
                【请提供以下完整信息】:
                1. 目的地概况和必游景点推荐
                2. 航班搜索和预订建议（具体航班信息和价格）
                3. 住宿推荐和预订建议（具体酒店信息和价格）
                4. 详细的日程安排（按天分解，包括时间、地点、活动）
                5. 当地交通和路线规划
                6. 餐厅推荐和美食指南
                7. 详细的预算分配和费用估算
                8. 实用信息（天气、注意事项、紧急联系方式等）
                9. 备选方案和应急计划
                
                请确保所有推荐都在预算范围内，并充分考虑我的偏好和限制条件。
                """
                
                # 更新进度
                progress_tracker(2, 4, "正在搜索旅行信息...")
                
                # 运行智能体
                response = asyncio.run(run_travel_agent(message))
                
                # 保存旅行计划到会话状态
                st.session_state['travel_plan'] = response
                st.session_state['travel_context'] = {
                    'source': source,
                    'destination': destination,
                    'travel_dates': travel_dates,
                    'budget': budget,
                    'preferences': travel_preferences,
                    'accommodation': accommodation_type,
                    'transportation': transportation_mode,
                    'dietary_restrictions': dietary_restrictions
                }
                
                # 更新进度
                progress_tracker(3, 4, "正在制定行程方案...")
                
                # 更新进度
                progress_tracker(4, 4, "AI规划完成！正在生成最终方案...")
                
                # 显示响应
                st.success("✅ AI旅行规划专家已为您制定完美的旅行方案！")
                
                # 添加AI说明
                st.info(f"� **AI模型**: {st.session_state.model_provider} - 集成信息搜索和行程规划功能")
                
                # 显示简化版本
                if len(response) > 2000:
                    st.markdown("### 旅行计划预览")
                    st.markdown(response[:2000] + "...")
                    st.info("📄 完整的旅行计划请下载PDF查看")
                else:
                    st.markdown(response)
                
                # 生成PDF下载链接
                try:
                    pdf_bytes = create_travel_plan_pdf(
                        response, 
                        source, 
                        destination, 
                        travel_dates, 
                        budget
                    )
                    
                    st.markdown("---")
                    st.markdown("### 📥 下载选项")
                    
                    if pdf_bytes:
                        filename = f"travel_plan_{source}_{destination}_{travel_dates[0]}.pdf"
                        download_link = create_download_link(pdf_bytes, filename)
                        if download_link:
                            st.markdown(download_link, unsafe_allow_html=True)
                            st.caption("点击上方链接下载PDF旅行计划")
                    
                    # 提供文本版本下载作为备用
                    text_filename = f"travel_plan_{source}_{destination}_{travel_dates[0]}.txt"
                    text_download_link = create_text_download_link(response, text_filename)
                    if text_download_link:
                        st.markdown(text_download_link, unsafe_allow_html=True)
                        st.caption("或下载文本版本（支持中文）")
                        
                except Exception as e:
                    st.warning(f"PDF生成遇到问题: {str(e)}")
                    # 至少提供文本下载
                    try:
                        st.markdown("---")
                        st.markdown("### 📥 下载选项")
                        text_filename = f"travel_plan_{source}_{destination}_{travel_dates[0]}.txt"
                        text_download_link = create_text_download_link(response, text_filename)
                        if text_download_link:
                            st.markdown(text_download_link, unsafe_allow_html=True)
                            st.caption("下载文本版旅行计划")
                    except:
                        st.info("您可以复制上方的文本内容保存")
                
            except Exception as e:
                st.error(f"规划旅行时发生错误：{str(e)}")
                st.info("请重试，如果问题持续存在，请联系技术支持。")

# ========== 多轮对话支持 ===========
# 初始化对话历史和旅行计划状态
if 'messages' not in st.session_state:
    st.session_state['messages'] = []  # [{role: 'user'/'assistant', content: '...'}]
if 'travel_plan' not in st.session_state:
    st.session_state['travel_plan'] = None  # 存储主要的旅行计划
if 'travel_context' not in st.session_state:
    st.session_state['travel_context'] = {}  # 存储旅行上下文信息

st.markdown('---')
st.header('💬 AI 旅行对话区（多轮提问/追问）')

# 显示当前旅行计划状态
if st.session_state['travel_plan']:
    with st.expander("📋 当前旅行计划概要", expanded=False):
        ctx = st.session_state['travel_context']
        st.markdown(f"""
        **🗺️ 路线**: {ctx.get('source', '未设定')} → {ctx.get('destination', '未设定')}  
        **📅 日期**: {ctx.get('travel_dates', ['未设定', '未设定'])[0]} 到 {ctx.get('travel_dates', ['未设定', '未设定'])[1]}  
        **💰 预算**: ${ctx.get('budget', 0)} 美元  
        **🎯 偏好**: {', '.join(ctx.get('preferences', []))}
        
        *您可以针对此旅行计划进行具体提问，比如询问某个景点的详细信息、更改行程安排、增加活动等*
        """)

# 展示历史消息
for msg in st.session_state['messages']:
    if msg['role'] == 'user':
        st.markdown(f"**🙋 用户：** {msg['content']}")
    else:
        st.markdown(f"**🤖 AI：** {msg['content']}")

# 聊天输入框
if st.session_state['travel_plan']:
    placeholder_text = "针对您的旅行计划提问（如：第二天的行程太紧张了，能否调整？推荐一些当地特色餐厅？）"
else:
    placeholder_text = "请先在上方生成旅行攻略，然后可以在这里进行追问"

user_input = st.text_input('请输入您的问题或追问', 
                          placeholder=placeholder_text, 
                          key='chat_input',
                          disabled=not st.session_state['travel_plan'])

# 发送按钮
if st.button('发送', key='chat_send', disabled=not st.session_state['travel_plan']) and user_input.strip():
    st.session_state['messages'].append({'role': 'user', 'content': user_input.strip()})
    with st.spinner('🤖 AI正在基于您的旅行计划回答...'):
        try:
            # 构建包含旅行计划上下文的消息
            context_message = f"""
            【当前旅行计划上下文】：
            {st.session_state['travel_plan']}
            
            【旅行基本信息】：
            - 出发地：{st.session_state['travel_context'].get('source', '未设定')}
            - 目的地：{st.session_state['travel_context'].get('destination', '未设定')}
            - 旅行日期：{st.session_state['travel_context'].get('travel_dates', ['未设定', '未设定'])[0]} 到 {st.session_state['travel_context'].get('travel_dates', ['未设定', '未设定'])[1]}
            - 预算：${st.session_state['travel_context'].get('budget', 0)} 美元
            - 旅行偏好：{', '.join(st.session_state['travel_context'].get('preferences', []))}
            
            【用户追问】：{user_input.strip()}
            
            请基于上述旅行计划和用户的具体问题进行针对性回答。如果用户询问的是计划中已有的内容，请提供更详细的信息；如果用户想要修改或补充计划，请给出具体的建议和替代方案。保持回答的相关性和实用性。
            """
            
            # 调用agent进行回答
            response = asyncio.run(run_travel_agent(context_message))
            st.session_state['messages'].append({'role': 'assistant', 'content': response})
            st.rerun()  # 刷新页面显示新消息
        except Exception as e:
            st.session_state['messages'].append({'role': 'assistant', 'content': f'发生错误：{str(e)}'})
            st.rerun()

# 清理对话历史按钮
if st.session_state['messages']:
    if st.button('🗑️ 清除对话历史', key='clear_chat'):
        st.session_state['messages'] = []
        st.rerun()


