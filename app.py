import os
import time

import httpx
import streamlit as st


API_BASE_URL = os.getenv("AGENT_API_BASE_URL", "https://127.0.0.1")
DEFAULT_BEARER_TOKEN = os.getenv("AGENT_DEMO_BEARER_TOKEN", "")


def build_headers(token: str) -> dict[str, str]:
    token = token.strip()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def get_json(path: str, token: str) -> dict:
    response = httpx.get(
        f"{API_BASE_URL}{path}",
        headers=build_headers(token),
        timeout=10.0,
        verify=False,  # 自签证书
    )
    response.raise_for_status()
    return response.json()


def post_json(path: str, payload: dict, token: str) -> dict:
    response = httpx.post(
        f"{API_BASE_URL}{path}",
        json=payload,
        headers=build_headers(token),
        timeout=120.0,
        verify=False,  # 自签证书
    )
    response.raise_for_status()
    return response.json()


st.title("扫地机器人企业客服 Demo")
st.caption(f"当前 API: {API_BASE_URL}")
st.divider()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

with st.sidebar:
    st.subheader("登录态")
    bearer_token = st.text_input("Bearer Token", value=DEFAULT_BEARER_TOKEN, type="password")
    report_requested = st.button("生成本期使用报告", use_container_width=True)

current_user = None
auth_error = None
if bearer_token.strip():
    try:
        current_user = get_json("/auth/me", bearer_token)
    except httpx.HTTPError as exc:
        auth_error = str(exc)

with st.sidebar:
    if current_user:
        st.success("鉴权成功")
        st.json(current_user)
    elif auth_error:
        st.error(auth_error)
    else:
        st.info("请输入 Bearer Token 后开始使用。")


for message in st.session_state["messages"]:
    st.chat_message(message["role"]).write(message["content"])


def append_assistant_message(content: str):
    st.session_state["messages"].append({"role": "assistant", "content": content})


if report_requested:
    if not bearer_token.strip():
        st.error("请输入 Bearer Token。")
    else:
        with st.spinner("正在生成报告..."):
            try:
                result = post_json("/api/report", {}, bearer_token)
                report_text = result["report"]
                if result.get("used_latest_available"):
                    report_text = (
                        f"注：当前自然月无数据，系统已自动回退到最近可用月份 {result['resolved_month']}。\n\n"
                        f"{report_text}"
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

    if not bearer_token.strip():
        st.error("请输入 Bearer Token。")
    else:
        with st.spinner("智能客服思考中..."):
            try:
                result = post_json(
                    "/api/chat",
                    {
                        "message": prompt,
                    },
                    bearer_token,
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
