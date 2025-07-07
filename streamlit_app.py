"""
AI旅行规划助手 - Streamlit前端界面
处理用户界面、输入验证、文件下载等前端功能
"""

import asyncio
import os
import re
from datetime import date
from fpdf import FPDF
import io
import base64
import streamlit as st

# 导入智能体模块
from travel_agent import (
    TravelPlanningAgent, 
    run_travel_agent, 
    build_travel_message, 
    build_context_message
)

# 导入提示词模块
from travel_prompts import QUICK_QUESTIONS

# 配置页面 - 必须是第一个 Streamlit 命令
st.set_page_config(
    page_title="AI 旅行规划助手",
    page_icon="✈️",
    layout="wide"
)

# 设置默认的API密钥环境变量
os.environ.setdefault("SEARCHAPI_API_KEY", "5722Vw5rYoJTVHyffqNph3F4")
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
            st.markdown("### 🛠️ 工具集") 
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


def setup_sidebar():
    """设置侧边栏API密钥配置"""
    with st.sidebar:
        st.header("🔑 API 密钥配置")
        st.markdown("请输入您的 API 密钥以使用旅行规划助手。")
        
        # 模型提供商选择
        st.session_state.model_provider = st.selectbox(
            "🤖 选择AI模型提供商",
            ["OpenAI", "Gemini"],
            index=["OpenAI", "Gemini"].index(st.session_state.model_provider),
            help="选择您喜欢的AI模型提供商"
        )

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
        required_keys = [st.session_state.searchapi_key]
        
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
                - 🔍 精准搜索：准确理解用户需求，搜索相关信息
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
    
    return all_keys_filled


def setup_input_form():
    """设置输入表单"""
    # 标题和描述
    st.title("✈️ AI 旅行规划助手")
    
    # 检查是否已有旅行计划
    if st.session_state.get('travel_plan'):
        st.success("🎉 您已有一个旅行计划！可以在下方对话区进行追问，或重新规划新的旅行。")
        
        # 显示当前计划概要
        with st.expander("📋 当前旅行计划概要", expanded=False):
            ctx = st.session_state.get('travel_context', {})
            travel_dates = ctx.get('travel_dates', ['未设定', '未设定'])
            start_date = travel_dates[0] if isinstance(travel_dates, list) and len(travel_dates) > 0 else '未设定'
            end_date = travel_dates[1] if isinstance(travel_dates, list) and len(travel_dates) > 1 else '未设定'
            
            st.markdown(f"""
            **🗺️ 路线**: {ctx.get('source', '未设定')} → {ctx.get('destination', '未设定')}  
            **📅 日期**: {start_date} 到 {end_date}  
            **💰 预算**: ${ctx.get('budget', 0)} 美元  
            **🎯 偏好**: {', '.join(ctx.get('preferences', []))}  
            **🏨 住宿偏好**: {ctx.get('accommodation', '未设定')}  
            **🚗 交通偏好**: {', '.join(ctx.get('transportation', []))}
            """)
    
    st.markdown("""
    这个 AI 驱动的旅行规划助手使用先进的**单智能体架构**，集成多种AI模型（OpenAI GPT 和 Google Gemini），通过SearchAPI.io提供全面的旅行服务：

    ### 🤖 AI 旅行规划专家
    - **🧠 智能整合**: 单个全能智能体，集成信息收集和行程规划功能
    - **🔍 全方位搜索**: 自动搜索航班、酒店、景点、餐厅等所有旅行信息
    - **📋 智能规划**: 基于搜索结果自动制定个性化行程方案
    - **💬 多轮对话**: 支持针对旅行计划的深度对话和实时调整

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
    - 💬 智能对话系统，支持计划修改和详细询问
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
    
    return {
        'source': source,
        'destination': destination,
        'travel_dates': travel_dates,
        'budget': budget,
        'travel_preferences': travel_preferences,
        'accommodation_type': accommodation_type,
        'transportation_mode': transportation_mode,
        'dietary_restrictions': dietary_restrictions
    }


def handle_travel_planning(form_data, all_keys_filled):
    """处理旅行规划请求"""
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
        if not form_data['source'] or not form_data['destination']:
            st.error("请输入出发地和目的地城市。")
        elif not form_data['travel_preferences']:
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
                    # 构建消息
                    message = build_travel_message(
                        form_data['source'],
                        form_data['destination'],
                        form_data['travel_dates'],
                        form_data['budget'],
                        form_data['travel_preferences'],
                        form_data['accommodation_type'],
                        form_data['transportation_mode'],
                        form_data['dietary_restrictions']
                    )
                    
                    # 运行智能体
                    response = asyncio.run(run_travel_agent(
                        message,
                        model_provider=st.session_state.model_provider,
                        openai_key=st.session_state.openai_key,
                        gemini_key=st.session_state.gemini_key,
                        searchapi_key=st.session_state.searchapi_key,
                        progress_callback=progress_tracker
                    ))
                    
                    # 保存旅行计划到会话状态
                    st.session_state['travel_plan'] = response
                    st.session_state['travel_context'] = {
                        'source': form_data['source'],
                        'destination': form_data['destination'],
                        'travel_dates': form_data['travel_dates'],
                        'budget': form_data['budget'],
                        'preferences': form_data['travel_preferences'],
                        'accommodation': form_data['accommodation_type'],
                        'transportation': form_data['transportation_mode'],
                        'dietary_restrictions': form_data['dietary_restrictions']
                    }
                    
                    # 显示响应
                    st.success("✅ AI旅行规划专家已为您制定完美的旅行方案！")
                    
                    # 添加AI说明
                    st.info(f"🤖 **AI模型**: {st.session_state.model_provider} - 集成信息搜索和行程规划功能")
                    
                    # 显示完整的旅行计划
                    with st.expander("📋 完整旅行计划", expanded=True):
                        st.markdown(response)
                    
                    # 生成下载选项
                    generate_download_options(response, form_data)
                    
                    # 显示提示信息
                    st.markdown("---")
                    st.info("💬 **接下来您可以：**\n- 在下方对话区询问旅行计划的具体细节\n- 请求修改某些安排\n- 获取更多推荐信息\n- 询问实用的旅行贴士")
                    
                except Exception as e:
                    st.error(f"规划旅行时发生错误：{str(e)}")
                    st.info("请重试，如果问题持续存在，请联系技术支持。")


def generate_download_options(response, form_data):
    """生成下载选项"""
    try:
        pdf_bytes = create_travel_plan_pdf(
            response, 
            form_data['source'], 
            form_data['destination'], 
            form_data['travel_dates'], 
            form_data['budget']
        )
        
        st.markdown("---")
        st.markdown("### 📥 下载选项")
        
        if pdf_bytes:
            filename = f"travel_plan_{form_data['source']}_{form_data['destination']}_{form_data['travel_dates'][0]}.pdf"
            download_link = create_download_link(pdf_bytes, filename)
            if download_link:
                st.markdown(download_link, unsafe_allow_html=True)
                st.caption("点击上方链接下载PDF旅行计划")
        
        # 提供文本版本下载作为备用
        text_filename = f"travel_plan_{form_data['source']}_{form_data['destination']}_{form_data['travel_dates'][0]}.txt"
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
            text_filename = f"travel_plan_{form_data['source']}_{form_data['destination']}_{form_data['travel_dates'][0]}.txt"
            text_download_link = create_text_download_link(response, text_filename)
            if text_download_link:
                st.markdown(text_download_link, unsafe_allow_html=True)
                st.caption("下载文本版旅行计划")
        except:
            st.info("您可以复制上方的文本内容保存")


def setup_chat_interface():
    """设置聊天界面"""
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
            travel_dates = ctx.get('travel_dates', ['未设定', '未设定'])
            start_date = travel_dates[0] if isinstance(travel_dates, list) and len(travel_dates) > 0 else '未设定'
            end_date = travel_dates[1] if isinstance(travel_dates, list) and len(travel_dates) > 1 else '未设定'
            
            st.markdown(f"""
            **🗺️ 路线**: {ctx.get('source', '未设定')} → {ctx.get('destination', '未设定')}  
            **📅 日期**: {start_date} 到 {end_date}  
            **💰 预算**: ${ctx.get('budget', 0)} 美元  
            **🎯 偏好**: {', '.join(ctx.get('preferences', []))}
            
            *您可以针对此旅行计划进行具体提问，比如询问某个景点的详细信息、更改行程安排、增加活动等*
            """)

    # 对话历史显示区域
    chat_container = st.container()
    
    with chat_container:
        if st.session_state['messages']:
            st.markdown("### 📝 对话历史")
            # 使用 Streamlit 的聊天消息组件
            for i, msg in enumerate(st.session_state['messages']):
                if msg['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(msg['content'])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg['content'])
        else:
            if st.session_state['travel_plan']:
                st.info("💡 开始对话吧！您可以询问旅行计划的任何细节，或者请求修改建议。")
            else:
                st.info("💡 请先在上方生成旅行攻略，然后可以在这里进行多轮对话。")

    # 聊天输入区域
    st.markdown("### 💭 发送消息")
    
    # 快捷问题按钮
    if st.session_state['travel_plan']:
        st.markdown("**💡 快捷问题示例（点击即可发送）：**")
        
        # 使用更多的快捷问题选项
        col1, col2, col3, col4 = st.columns(4)
        
        quick_questions_list = list(QUICK_QUESTIONS.items())
        
        with col1:
            if st.button("📍 景点详情", key="quick_1"):
                st.session_state['quick_question'] = quick_questions_list[0][1]  # 景点详情
                st.rerun()
                
        with col2:
            if st.button("🍽️ 餐厅推荐", key="quick_2"):
                st.session_state['quick_question'] = quick_questions_list[1][1]  # 餐厅推荐
                st.rerun()
                
        with col3:
            if st.button("🚗 交通建议", key="quick_3"):
                st.session_state['quick_question'] = quick_questions_list[2][1]  # 交通建议
                st.rerun()
                
        with col4:
            if st.button("💰 预算优化", key="quick_4"):
                st.session_state['quick_question'] = quick_questions_list[3][1]  # 预算优化
                st.rerun()
        
        # 第二行快捷问题
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            if st.button("📅 行程调整", key="quick_5"):
                st.session_state['quick_question'] = quick_questions_list[4][1]  # 行程调整
                st.rerun()
                
        with col6:
            if st.button("🏛️ 当地文化", key="quick_6"):
                st.session_state['quick_question'] = quick_questions_list[5][1]  # 当地文化
                st.rerun()
                
        with col7:
            if st.button("🌤️ 天气装备", key="quick_7"):
                st.session_state['quick_question'] = quick_questions_list[6][1]  # 天气装备
                st.rerun()
                
        with col8:
            if st.button("🛡️ 安全须知", key="quick_8"):
                st.session_state['quick_question'] = quick_questions_list[7][1]  # 安全须知
                st.rerun()
        
        # 处理快捷问题
        if 'quick_question' in st.session_state and st.session_state['quick_question']:
            handle_chat_message(st.session_state['quick_question'])
            st.session_state['quick_question'] = None

    # 文本输入框
    if st.session_state['travel_plan']:
        placeholder_text = "输入您的问题或要求（如：第二天的行程太紧张了，能否调整？推荐一些当地特色餐厅？住宿可以升级吗？）"
    else:
        placeholder_text = "请先在上方生成旅行攻略，然后可以在这里进行追问"

    # 使用 chat_input 组件，它会自动处理输入清空
    if st.session_state['travel_plan']:
        user_input = st.chat_input(placeholder_text)
        
        # 处理用户输入
        if user_input:
            handle_chat_message(user_input.strip())
    else:
        st.info("💡 请先在上方生成旅行攻略，然后可以在这里进行多轮对话。")

    # 对话管理按钮
    if st.session_state['messages'] or st.session_state['travel_plan']:
        st.markdown("### 🛠️ 对话管理")
        col_clear, col_export, col_reset = st.columns(3)
        
        with col_clear:
            if st.button('🗑️ 清除对话历史', key='clear_chat'):
                st.session_state['messages'] = []
                st.rerun()
                
        with col_export:
            if st.session_state['messages']:
                if st.button('📤 导出对话', key='export_chat'):
                    export_chat_history()
                    
        with col_reset:
            if st.button('🔄 重新开始规划', key='reset_all'):
                st.session_state['travel_plan'] = None
                st.session_state['travel_context'] = {}
                st.session_state['messages'] = []
                st.rerun()


def handle_chat_message(user_message):
    """处理聊天消息"""
    # 添加用户消息到历史
    st.session_state['messages'].append({'role': 'user', 'content': user_message})
    
    # 显示处理状态
    with st.spinner('🤖 AI正在基于您的旅行计划思考回答...'):
        try:
            # 构建包含旅行计划上下文的消息
            context_message = build_context_message(
                st.session_state['travel_plan'],
                st.session_state['travel_context'],
                user_message
            )
            
            # 调用agent进行回答
            response = asyncio.run(run_travel_agent(
                context_message,
                model_provider=st.session_state.model_provider,
                openai_key=st.session_state.openai_key,
                gemini_key=st.session_state.gemini_key,
                searchapi_key=st.session_state.searchapi_key
            ))
            
            # 添加AI回复到历史
            st.session_state['messages'].append({'role': 'assistant', 'content': response})
            
            # 刷新页面显示新消息
            st.rerun()
            
        except Exception as e:
            error_msg = f'抱歉，处理您的问题时发生错误：{str(e)}\n\n请重试，或者重新表述您的问题。'
            st.session_state['messages'].append({'role': 'assistant', 'content': error_msg})
            st.rerun()


def export_chat_history():
    """导出对话历史"""
    if not st.session_state['messages']:
        st.warning("没有对话历史可以导出。")
        return
    
    # 生成对话历史文本
    chat_text = "# AI旅行助手对话历史\n\n"
    
    # 添加旅行计划信息
    if st.session_state['travel_context']:
        ctx = st.session_state['travel_context']
        travel_dates = ctx.get('travel_dates', ['未设定', '未设定'])
        start_date = travel_dates[0] if isinstance(travel_dates, list) and len(travel_dates) > 0 else '未设定'
        end_date = travel_dates[1] if isinstance(travel_dates, list) and len(travel_dates) > 1 else '未设定'
        
        chat_text += f"## 旅行计划基本信息\n"
        chat_text += f"- 路线: {ctx.get('source', '未设定')} → {ctx.get('destination', '未设定')}\n"
        chat_text += f"- 日期: {start_date} 到 {end_date}\n"
        chat_text += f"- 预算: ${ctx.get('budget', 0)} 美元\n"
        chat_text += f"- 偏好: {', '.join(ctx.get('preferences', []))}\n\n"
    
    # 添加对话历史
    chat_text += "## 对话记录\n\n"
    for i, msg in enumerate(st.session_state['messages'], 1):
        role = "用户" if msg['role'] == 'user' else "AI助手"
        chat_text += f"### {i}. {role}\n{msg['content']}\n\n"
    
    # 创建下载链接
    try:
        b64 = base64.b64encode(chat_text.encode('utf-8')).decode()
        href = f'<a href="data:text/plain;charset=utf-8;base64,{b64}" download="chat_history.md">📄 下载对话历史 (Markdown格式)</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("对话历史已准备好下载！")
    except Exception as e:
        st.error(f"导出对话历史时发生错误：{str(e)}")


def init_session_state():
    """初始化会话状态"""
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'travel_plan' not in st.session_state:
        st.session_state['travel_plan'] = None
    if 'travel_context' not in st.session_state:
        st.session_state['travel_context'] = {}
    if 'model_provider' not in st.session_state:
        st.session_state.model_provider = "OpenAI"
    if 'searchapi_key' not in st.session_state:
        st.session_state.searchapi_key = os.environ.get("SEARCHAPI_API_KEY", "")
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = os.environ.get("OPENAI_API_KEY", "")
    if 'gemini_key' not in st.session_state:
        st.session_state.gemini_key = ""
    if 'quick_question' not in st.session_state:
        st.session_state['quick_question'] = None


def main():
    """主函数"""
    # 初始化会话状态
    init_session_state()
    
    # 设置侧边栏
    all_keys_filled = setup_sidebar()
    
    # 设置输入表单
    form_data = setup_input_form()
    
    # 如果已有旅行计划，显示查看选项
    if st.session_state.get('travel_plan'):
        st.markdown("---")
        st.header("📋 当前旅行计划")
        
        # 显示计划操作按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📖 查看完整计划", key="view_plan"):
                st.markdown("### 完整旅行计划")
                st.markdown(st.session_state['travel_plan'])
                
        with col2:
            if st.button("📥 下载计划", key="download_plan"):
                ctx = st.session_state.get('travel_context', {})
                generate_download_options(st.session_state['travel_plan'], ctx)
                
        with col3:
            if st.button("🔄 规划新旅行", key="new_plan"):
                # 保持当前输入表单的内容，但清除旅行计划
                st.session_state['travel_plan'] = None
                st.session_state['travel_context'] = {}
                st.session_state['messages'] = []
                st.info("已清除当前计划，请在上方填写新的旅行信息。")
    
    # 处理旅行规划
    handle_travel_planning(form_data, all_keys_filled)
    
    # 设置聊天界面
    setup_chat_interface()


if __name__ == "__main__":
    main()
