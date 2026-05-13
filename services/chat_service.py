import re

from agent.react_agent import ReactAgent
from schemas.app_models import ChatRequest, ChatResponse, ReportRequest, UserContext
from services.business_service import BusinessService
from services.report_workflow import ReportWorkflowService
from utils.logger_handler import logger


REPORT_KEYWORDS = ("报告", "使用记录", "保养建议", "月报")


class ChatService:
    def __init__(self, business_service: BusinessService):
        self.business_service = business_service
        self.report_workflow = ReportWorkflowService(business_service)

    def handle(self, request: ChatRequest, user_context: UserContext) -> ChatResponse:
        logger.info("chat_handle_start", extra={
            "user_id": user_context.user_id,
            "mode": "report" if self._is_report_request(request.message) else "agent",
        })
        explicit_month = self._extract_month(request.message)
        if self._is_report_request(request.message):
            report = self.report_workflow.generate_report(
                ReportRequest(month=explicit_month),
                user_context=user_context,
            )
            return ChatResponse(
                mode="report_workflow",
                reply=report.report,
                user_context=user_context,
                report_month=report.resolved_month,
                used_latest_available=report.used_latest_available,
            )

        agent = ReactAgent(self.business_service, user_context)
        reply = "".join(agent.execute_stream(request.message)).strip()
        return ChatResponse(
            mode="agent",
            reply=reply,
            user_context=user_context,
        )

    @staticmethod
    def _is_report_request(message: str) -> bool:
        return any(keyword in message for keyword in REPORT_KEYWORDS)

    @staticmethod
    def _extract_month(message: str) -> str | None:
        match = re.search(r"(20\d{2}-\d{2})", message)
        return match.group(1) if match else None
