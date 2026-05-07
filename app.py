import os
import time

import httpx
import streamlit as st

API_BASE_URL = os.getenv("AGENT_API_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_USER_IDS = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010"]
DEFAULT_CITIES = ["深圳", "合肥", "杭州"]


def fetch_user_ids() -> list[str]:
    try:
        response = httpx.get(f"{API_BASE_URL}/business/users", timeout=5.0)
        response.raise_for_status()
        return response.json()
    except Exception:
        return DEFAULT_USER_IDS


def post_json(path: str, payload: dict) -> dict:
    response = httpx.post(f"{API_BASE_URL}{path}", json=payload, timeout=120.0)
    response.raise_for_status()
    return response.json()


st.title("扫地机器人企业客服 Demo")
st.caption(f"当前 API: {API_BASE_URL}")
st.divider()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

user_ids = fetch_user_ids()

with st.sidebar:
    st.subheader("请求上下文")
    selected_user_id = st.selectbox("用户 ID", user_ids, index=0)
    selected_city = st.selectbox("所在城市", DEFAULT_CITIES, index=0)
    report_requested = st.button("生成本期使用报告", use_container_width=True)


for message in st.session_state["messages"]:
    st.chat_message(message["role"]).write(message["content"])


def append_assistant_message(content: str):
    st.session_state["messages"].append({"role": "assistant", "content": content})


if report_requested:
    with st.spinner("正在生成报告..."):
        try:
            result = post_json(
                "/api/report",
                {
                    "user_context": {
                        "user_id": selected_user_id,
                        "city": selected_city,
                    }
                },
            )
            report_text = result["report"]
            if result.get("used_latest_available"):
                report_text = (
                    f"注：当前自然月无数据，系统已自动回退到最近可用月份 {result['resolved_month']}。\n\n"
                    + report_text
                )

            st.chat_message("assistant").write(report_text)
            append_assistant_message(report_text)
            st.rerun()
        except httpx.HTTPError as exc:
            st.error(f"报告服务调用失败：{exc}")


prompt = st.chat_input("请输入你的问题")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.spinner("智能客服思考中..."):
        try:
            result = post_json(
                "/api/chat",
                {
                    "message": prompt,
                    "user_context": {
                        "user_id": selected_user_id,
                        "city": selected_city,
                    },
                },
            )
            reply = result["reply"]

            def stream_text(text: str):
                for char in text:
                    time.sleep(0.008)
                    yield char

            st.chat_message("assistant").write_stream(stream_text(reply))
            append_assistant_message(reply)
            st.rerun()
        except httpx.HTTPError as exc:
            st.error(f"聊天服务调用失败：{exc}")
