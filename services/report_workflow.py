import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from rag.rag_service import get_rag_service
from model.factory import chat_model
from schemas.app_models import ReportRequest, ReportResponse, UserContext
from services.business_service import BusinessService
from utils.llm_utils import llm_retry
from utils.logger_handler import logger
from utils.prompt_loader import load_report_workflow_prompt


class ReportWorkflowService:
    def __init__(self, business_service: BusinessService):
        self.business_service = business_service
        self.prompt = PromptTemplate.from_template(load_report_workflow_prompt())
        self.chain = self.prompt | chat_model | StrOutputParser()

    def generate_report(
        self,
        request: ReportRequest,
        user_context: UserContext | None = None,
    ) -> ReportResponse:
        effective_user_context = user_context or request.user_context
        if effective_user_context is None:
            raise ValueError("User context is required to generate a report.")

        logger.info("report_generate_start", extra={
            "user_id": effective_user_context.user_id,
            "requested_month": request.month,
        })

        profile = self.business_service.get_user_profile(effective_user_context)
        weather = self.business_service.get_weather(effective_user_context.city)

        preferred_month = request.month or self.business_service.get_current_month()
        lookup_result = self.business_service.resolve_usage_record(
            effective_user_context.user_id,
            preferred_month=preferred_month,
        )

        logger.info("report_data_collected", extra={
            "resolved_month": lookup_result.resolved_month,
            "used_latest_available": lookup_result.used_latest_available,
        })

        rag_insights = self._collect_rag_insights(lookup_result.usage_record)
        report = self._invoke_chain(
            {
                "user_profile": profile.to_prompt_text(),
                "requested_month": preferred_month,
                "resolved_month": lookup_result.resolved_month,
                "used_latest_available": "是" if lookup_result.used_latest_available else "否",
                "weather": weather.to_prompt_text(),
                "usage_record": lookup_result.usage_record.to_prompt_text(),
                "rag_insights": rag_insights,
            }
        )

        logger.info("report_generate_done", extra={
            "resolved_month": lookup_result.resolved_month,
        })

        return ReportResponse(
            report=report,
            user_context=effective_user_context,
            requested_month=preferred_month,
            resolved_month=lookup_result.resolved_month,
            used_latest_available=lookup_result.used_latest_available,
        )

    @llm_retry(max_retries=2, backoff_seconds=1.0)
    def _invoke_chain(self, inputs: dict) -> str:
        return self.chain.invoke(inputs)

    def _collect_rag_insights(self, usage_record) -> str:
        queries = self._build_rag_queries(usage_record)
        insights = []
        rag_service = get_rag_service()
        for query in queries:
            insights.append(f"问题：{query}\n建议：{rag_service.rag_summarize(query)}")
        return "\n\n".join(insights)

    def _build_rag_queries(self, usage_record) -> list[str]:
        queries = [
            f"{self._trim_for_query(usage_record.consumables)} 保养建议",
            f"{self._trim_for_query(usage_record.efficiency)} 清洁效率优化建议",
        ]

        comparison_text = usage_record.comparison.strip()
        if comparison_text:
            queries.append(f"{self._trim_for_query(comparison_text)} 改进建议")

        deduped_queries = []
        for query in queries:
            if query not in deduped_queries:
                deduped_queries.append(query)
        return deduped_queries[:3]

    @staticmethod
    def _trim_for_query(text: str) -> str:
        compact = re.sub(r"\s+", " ", text.replace("\\n", " ").replace("\n", " ")).strip()
        return compact[:80]
