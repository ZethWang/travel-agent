"""
双智能体旅行规划团队配置文件
Team Configuration for Dual-Agent Travel Planning System
"""

# 智能体配置
AGENT_CONFIGS = {
    "research_agent": {
        "name": "旅行信息收集专家",
        "role": "Research Specialist",
        "description": "专门负责搜索、收集和验证旅行相关数据",
        "primary_tools": [
            "search_google_maps",
            "search_google_flights", 
            "search_google_hotels",
            "search_google",
            "get_current_time"
        ],
        "goal": """作为旅行信息收集专家，我专门负责：
        1. 搜索和收集目的地相关信息（景点、文化、气候等）
        2. 查找航班信息和价格比较
        3. 搜索酒店和住宿选项
        4. 收集餐厅和美食推荐
        5. 获取交通信息和路线规划
        6. 搜索当地活动和体验项目
        我会提供详细、准确的数据供规划专家使用。""",
        "instructions": [
            "优先使用Google Maps搜索目的地信息",
            "收集多个航班选项以供比较",
            "搜索不同价位和类型的住宿",
            "注意用户的饮食限制和偏好",
            "收集最新的旅行信息和评价"
        ]
    },
    
    "planning_agent": {
        "name": "行程规划专家", 
        "role": "Planning Specialist",
        "description": "专门负责整合信息、制定计划和优化行程",
        "primary_tools": [
            "search_google_maps",  # 用于路线验证
            "get_current_time",    # 用于时间规划
        ],
        "goal": """作为行程规划专家，我专门负责：
        1. 分析用户需求和偏好
        2. 整合信息收集专家提供的数据
        3. 制定详细的日程安排
        4. 进行预算规划和成本控制
        5. 优化行程路线和时间安排
        6. 提供个性化建议和备选方案
        7. 生成完整的旅行计划文档
        我会基于收集到的信息创建最优的旅行方案。""",
        "instructions": [
            "根据用户预算进行合理分配",
            "考虑交通时间和路线优化", 
            "平衡观光和休息时间",
            "提供备选方案应对突发情况",
            "确保行程的可行性和实用性"
        ]
    }
}

# 团队协作配置
TEAM_CONFIG = {
    "show_chain_of_thought": True,  # 显示思维链
    "max_iterations": 5,            # 最大协作轮次
    "collaboration_mode": "parallel_then_integrate",  # 协作模式
    "quality_check": True,          # 启用质量检查
}

# 工作流程配置
WORKFLOW_CONFIG = {
    "phases": [
        {
            "name": "需求分析",
            "description": "解析用户需求并分解任务",
            "duration": "1-2分钟",
            "agents": ["research_agent", "planning_agent"]
        },
        {
            "name": "信息收集", 
            "description": "并行收集旅行相关数据",
            "duration": "2-3分钟",
            "agents": ["research_agent"],
            "parallel_tasks": [
                "目的地信息搜索",
                "航班信息收集", 
                "酒店选项搜索",
                "餐厅和活动搜索"
            ]
        },
        {
            "name": "方案规划",
            "description": "整合信息并制定旅行方案", 
            "duration": "2-3分钟",
            "agents": ["planning_agent"],
            "tasks": [
                "数据分析和整合",
                "行程安排制定",
                "预算规划",
                "路线优化"
            ]
        },
        {
            "name": "协作优化",
            "description": "两个智能体协作优化最终方案",
            "duration": "1-2分钟", 
            "agents": ["research_agent", "planning_agent"]
        }
    ]
}

# 质量控制配置
QUALITY_CONFIG = {
    "validation_rules": [
        "检查航班日期的有效性",
        "验证酒店可预订性", 
        "确保预算分配合理",
        "检查行程时间安排",
        "验证地点信息准确性"
    ],
    "fallback_strategies": [
        "如果航班搜索失败，提供通用航班建议",
        "如果酒店搜索无结果，推荐知名连锁酒店",
        "如果预算超支，提供经济替代方案"
    ]
}

# 性能监控配置
PERFORMANCE_CONFIG = {
    "metrics": [
        "总处理时间",
        "API调用次数", 
        "信息收集完整度",
        "方案可行性评分",
        "用户满意度"
    ],
    "optimization_targets": [
        "减少处理时间",
        "提高信息准确性",
        "增强方案个性化",
        "改善用户体验"
    ]
}

# 错误处理配置
ERROR_HANDLING = {
    "api_failures": {
        "retry_count": 3,
        "fallback_message": "部分信息获取失败，已提供替代建议"
    },
    "timeout_handling": {
        "max_wait_time": 30,  # 秒
        "timeout_message": "处理时间较长，正在优化方案..."
    },
    "data_validation": {
        "required_fields": ["目的地", "日期", "预算"],
        "validation_message": "请确保所有必填信息完整"
    }
}
