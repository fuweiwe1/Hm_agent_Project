from langchain.agents import create_agent

from agent.tools.agent_tools import build_agent_tools
from agent.tools.middleware import log_before_model, monitor_tool
from model.factory import chat_model
from schemas.app_models import UserContext
from services.business_service import BusinessService
from utils.prompt_loader import load_system_prompts


class ReactAgent:
    def __init__(self, business_service: BusinessService, user_context: UserContext):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=build_agent_tools(user_context, business_service),
            middleware=[monitor_tool, log_before_model],
        )

    def execute_stream(self, query: str):
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

        for chunk in self.agent.stream(input_dict, stream_mode="values"):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"
