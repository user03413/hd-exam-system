"""火电机组考核系统 - Agent入口"""
import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver
from tools.sync_tool import sync_to_github

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]  # type: ignore

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

def build_agent(ctx=None):
    """构建Agent实例"""
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    # 系统提示词
    system_prompt = """你是火电机组考核系统的智能助手，帮助学生和管理员使用系统。

## 功能说明

1. **同步题库**: 当用户发送"同步题库"时，调用 sync_to_github 工具将代码推送到GitHub仓库

2. **常规问答**: 帮助用户理解热工自动化相关知识

## 重要规则

- 用户说"同步题库"或类似意思时，必须调用 sync_to_github 工具
- 其他问题用简洁清晰的语言回答"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[sync_to_github],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
