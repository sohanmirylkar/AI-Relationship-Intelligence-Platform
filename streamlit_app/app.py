import os
from io import BytesIO

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_BASE = os.getenv("IRIP_API_BASE", "http://localhost:8000/api/v1")

st.set_page_config(page_title="IRIP", layout="wide", page_icon="IR")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    [data-testid="stSidebar"] {background: #0f172a;}
    [data-testid="stSidebar"] * {color: #f8fafc;}
    div[data-testid="stMetricValue"] {font-size: 1.6rem;}
    .small-note {color: #64748b; font-size: 0.85rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def api(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state['token']}"
    response = requests.request(method, f"{API_BASE}{path}", headers=headers, timeout=60, **kwargs)
    if response.status_code >= 400:
        st.error(f"{response.status_code}: {response.text}")
        response.raise_for_status()
    return response.json()


def login_panel():
    if st.session_state.get("token"):
        return
    st.sidebar.subheader("Sign in")
    username = st.sidebar.text_input("Username", value="analyst")
    password = st.sidebar.text_input("Password", value="indago-demo", type="password")
    if st.sidebar.button("Sign in", use_container_width=True):
        response = requests.post(
            f"{API_BASE}/auth/token",
            data={"username": username, "password": password, "scope": "meeting:run research:run crm:sync"},
            timeout=30,
        )
        if response.ok:
            payload = response.json()
            st.session_state["token"] = payload["access_token"]
            st.session_state["scopes"] = payload["scopes"]
            st.rerun()
        st.sidebar.error(response.text)
    st.stop()


def module_header(title: str, caption: str):
    left, right = st.columns([0.72, 0.28])
    with left:
        st.title(title)
        st.caption(caption)
    with right:
        st.metric("Mode", "Human review")


def assistant_panel(current_page: str):
    st.sidebar.divider()
    with st.sidebar.expander("IRIP Copilot", expanded=True):
        if "assistant_messages" not in st.session_state:
            st.session_state["assistant_messages"] = [
                {
                    "role": "assistant",
                    "content": "Tell me what you are trying to do, and I’ll guide the next step.",
                }
            ]
        for message in st.session_state["assistant_messages"][-4:]:
            st.chat_message(message["role"]).markdown(message["content"])
        prompt = st.chat_input("Ask about this workflow")
        if prompt:
            st.session_state["assistant_messages"].append({"role": "user", "content": prompt})
            recent_state = {
                "meeting_result": st.session_state.get("meeting_result"),
                "crm_preflight": st.session_state.get("crm_preflight"),
                "crm_sync": st.session_state.get("crm_sync"),
                "research_result": st.session_state.get("research_result"),
                "deliverable": st.session_state.get("deliverable"),
                "prompt_result": st.session_state.get("prompt_result"),
            }
            payload = api(
                "POST",
                "/assistant/chat",
                json={
                    "message": prompt,
                    "current_page": current_page,
                    "recent_state": recent_state,
                    "conversation": st.session_state["assistant_messages"][-8:],
                },
            )
            answer = payload["answer_markdown"]
            if payload.get("suggested_next_steps"):
                steps = "\n".join(f"- {step}" for step in payload["suggested_next_steps"][:3])
                answer = f"{answer}\n\n**Suggested next steps**\n{steps}"
            st.session_state["assistant_messages"].append(
                {"role": "assistant", "content": answer}
            )
            st.rerun()


login_panel()

st.sidebar.title("IRIP")
page = st.sidebar.radio(
    "Workspace",
    [
        "Meeting Intelligence",
        "Investor Research",
        "CRM Autopilot",
        "Token Optimizer",
        "Deliverables Generator",
        "Relationship Graph",
        "Knowledge Base",
        "Dashboard",
    ],
)
if st.sidebar.button("Sign out", use_container_width=True):
    st.session_state.clear()
    st.rerun()

assistant_panel(page)


if page == "Meeting Intelligence":
    module_header("Meeting Intelligence", "Extract summary, action items, entities, confidence, and CRM-ready updates.")
    left, middle, right = st.columns([0.34, 0.38, 0.28])
    with left:
        company_hint = st.text_input("Company hint", value="Blackstone")
        interaction_date = st.date_input("Interaction date")
        attendees = st.text_input("Attendees", value="Jane Doe, Analyst Demo User")
        uploaded = st.file_uploader("Transcript or notes", type=["txt", "md", "json"])
        default_text = """Meeting with Jane Doe, CIO at Blackstone. Discussed residential mortgage finance allocation appetite and interest in asset-based credit. Jane asked for a follow-up deck and a second call with the investment team. Action: send follow-up deck and schedule second call."""
        text = st.text_area("Notes", value=uploaded.read().decode("utf-8", errors="ignore") if uploaded else default_text, height=270)
        if st.button("Run extraction", use_container_width=True):
            st.session_state["meeting_result"] = api(
                "POST",
                "/meetings/extract",
                json={
                    "transcript_text": text,
                    "company_hint": company_hint,
                    "attendees": [a.strip() for a in attendees.split(",") if a.strip()],
                    "interaction_date": str(interaction_date),
                },
            )
    result = st.session_state.get("meeting_result")
    with middle:
        st.subheader("AI Draft")
        if result:
            st.write(result["summary"])
            st.markdown("#### Action Items")
            st.dataframe(pd.DataFrame(result["action_items"]), use_container_width=True, hide_index=True)
            st.markdown("#### Entities")
            st.json(result["extracted_entities"])
        else:
            st.info("Run extraction to populate the analyst review draft.")
    with right:
        st.subheader("Validation")
        if result:
            st.json(result["confidence"])
            st.markdown("#### CRM Payload")
            st.json(result["crm_payload"])
            if st.button("Preflight CRM", use_container_width=True):
                st.session_state["crm_preflight"] = api(
                    "POST",
                    "/crm/preflight",
                    json={"target_object": "Interaction", "mode": "csv_export", "records": [result["crm_payload"]]},
                )
            if st.session_state.get("crm_preflight"):
                st.json(st.session_state["crm_preflight"])
        else:
            st.caption("Confidence, duplicate warnings, and field status appear here.")

elif page == "Investor Research":
    module_header("Investor Research", "Generate a cited pre-meeting brief from internal knowledge and approved notes.")
    left, middle, right = st.columns([0.32, 0.44, 0.24])
    with left:
        company = st.text_input("Target firm", value="Blackstone")
        sources = st.text_area("Approved sources", value="Analyst notes; internal CRM history")
        notes = st.text_area("Analyst notes", height=220)
        if st.button("Generate memo", use_container_width=True):
            st.session_state["research_result"] = api(
                "POST",
                "/research/company",
                json={
                    "company_name": company,
                    "approved_sources": [s.strip() for s in sources.split(";") if s.strip()],
                    "notes": notes,
                },
            )
    with middle:
        st.subheader("Research Memo")
        result = st.session_state.get("research_result")
        if result:
            st.markdown(result["memo_markdown"])
        else:
            st.info("Generate a memo to review source-backed talking points.")
    with right:
        if st.session_state.get("research_result"):
            st.subheader("Evidence")
            st.json(st.session_state["research_result"]["sources"])
            st.subheader("Confidence")
            st.json(st.session_state["research_result"]["confidence"])

elif page == "CRM Autopilot":
    module_header("CRM Autopilot", "Validate, deduplicate, map, and export Supabase-ready records.")
    payload = st.session_state.get("meeting_result", {}).get("crm_payload", {})
    edited = st.data_editor(pd.DataFrame([payload or {
        "ExternalSystemId": "meet_2026_06_16_blackstone_01",
        "CompanyName": "Blackstone",
        "ContactName": "Jane Doe",
        "MeetingDate": "2026-06-16",
        "Summary": "Discussed allocation appetite.",
        "NextAction": "Send follow-up deck.",
        "Owner": "Analyst Demo User",
    }]), use_container_width=True, num_rows="dynamic")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Run preflight", use_container_width=True):
            st.session_state["crm_preflight"] = api(
                "POST",
                "/crm/preflight",
                json={"target_object": "Interaction", "mode": "csv_export", "records": edited.to_dict("records")},
            )
    with c2:
        if st.button("Export CSV", use_container_width=True):
            st.session_state["crm_sync"] = api(
                "POST",
                "/crm/sync",
                json={"target_object": "Interaction", "mode": "csv_export", "records": edited.to_dict("records")},
            )
    with c3:
        if st.button("Sync to Supabase", use_container_width=True):
            st.session_state["crm_sync"] = api(
                "POST",
                "/crm/sync",
                json={
                    "target_object": "Interaction",
                    "mode": "supabase_sync",
                    "records": edited.to_dict("records"),
                },
            )
    left, right = st.columns(2)
    with left:
        st.subheader("Preflight")
        st.json(st.session_state.get("crm_preflight", {}))
    with right:
        st.subheader("Sync Log")
        st.json(st.session_state.get("crm_sync", {}))

elif page == "Token Optimizer":
    module_header("Token Optimizer", "Estimate cost, rewrite prompts, route to cheaper viable models, and log savings.")
    prompt = st.text_area("Prompt or workflow", height=250, value="Please analyze this very long meeting transcript and create CRM fields, follow-up items, a brief, and a clean summary for the investor relations team.")
    c1, c2, c3, c4 = st.columns(4)
    model = c1.selectbox("Model", ["claude-sonnet-4-6", "claude-haiku-4-5", "claude-opus-4-8", "gpt-5.5"])
    output_tokens = c2.number_input("Output tokens", value=1200, min_value=50, step=50)
    cached = c3.number_input("Cached input", value=0, min_value=0, step=50)
    runs = c4.number_input("Monthly runs", value=100, min_value=1, step=10)
    if st.button("Optimize", use_container_width=True):
        st.session_state["prompt_result"] = api(
            "POST",
            "/prompts/optimize",
            json={
                "prompt": prompt,
                "model": model,
                "expected_output_tokens": int(output_tokens),
                "cached_input_tokens": int(cached),
                "monthly_runs": int(runs),
            },
        )
    result = st.session_state.get("prompt_result")
    if result:
        a, b, c = st.columns(3)
        a.metric("Original monthly", f"${result['original']['monthly_cost_usd']:.4f}")
        b.metric("Optimized monthly", f"${result['optimized']['monthly_cost_usd']:.4f}")
        c.metric("Savings", f"${result['estimated_savings_usd']:.4f}")
        st.text_area("Optimized prompt", value=result["optimized_prompt"], height=220)
        st.json(result["routing_recommendation"])

elif page == "Deliverables Generator":
    module_header("Deliverables Generator", "Create follow-up email, FAQ, one-pager, and pitch-outline drafts.")
    meeting = st.session_state.get("meeting_result", {})
    research = st.session_state.get("research_result", {})
    c1, c2 = st.columns([0.3, 0.7])
    with c1:
        dtype = st.selectbox("Deliverable", ["follow_up_email", "pitch_outline", "faq", "one_pager"])
        company = st.text_input("Company", value=meeting.get("crm_payload", {}).get("CompanyName", "Blackstone"))
        if st.button("Generate", use_container_width=True):
            st.session_state["deliverable"] = api(
                "POST",
                "/deliverables/generate",
                json={
                    "deliverable_type": dtype,
                    "company_name": company,
                    "meeting_summary": meeting.get("summary"),
                    "research_memo": research.get("memo_markdown"),
                    "crm_payload": meeting.get("crm_payload", {}),
                },
            )
    with c2:
        result = st.session_state.get("deliverable")
        if result:
            st.subheader(result["title"])
            st.markdown(result["content_markdown"])
        else:
            st.info("Generate a deliverable after extraction or research.")

elif page == "Relationship Graph":
    module_header("Relationship Graph", "Visualize firms, contacts, interactions, referrals, and opportunity context.")
    graph = api("GET", "/graph/all")
    nodes = pd.DataFrame(graph["nodes"])
    edges = pd.DataFrame(graph["edges"])
    c1, c2 = st.columns([0.45, 0.55])
    with c1:
        st.subheader("Nodes")
        st.dataframe(nodes, use_container_width=True, hide_index=True)
    with c2:
        st.subheader("Edges")
        st.dataframe(edges, use_container_width=True, hide_index=True)
    if not nodes.empty:
        fig = px.scatter(
            nodes.reset_index(),
            x="index",
            y=[1] * len(nodes),
            color="type",
            hover_name="label",
            title="Relationship projection",
        )
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True)

elif page == "Knowledge Base":
    module_header("Knowledge Base", "Upload approved documents, chunk them, and query source-backed snippets.")
    left, right = st.columns([0.34, 0.66])
    with left:
        upload = st.file_uploader("Approved document", type=["txt", "md", "json", "csv", "pdf", "docx", "xlsx"])
        if upload and st.button("Index document", use_container_width=True):
            files = {"file": (upload.name, BytesIO(upload.read()), upload.type or "application/octet-stream")}
            headers = {"Authorization": f"Bearer {st.session_state['token']}"}
            response = requests.post(f"{API_BASE}/ingest/document", headers=headers, files=files, timeout=90)
            if response.ok:
                st.session_state["last_upload"] = response.json()
            else:
                st.error(response.text)
        query = st.text_input("Ask the knowledge base", value="What is the current relationship context?")
        if st.button("Search", use_container_width=True):
            st.session_state["rag_result"] = api("POST", "/rag/query", json={"query": query, "top_k": 5})
    with right:
        st.subheader("Answer")
        result = st.session_state.get("rag_result")
        if result:
            st.write(result["answer"])
            st.subheader("Citations")
            st.dataframe(pd.DataFrame(result["citations"]), use_container_width=True, hide_index=True)
        else:
            st.info("Upload and index source material, then run a query.")

else:
    module_header("Dashboard", "Operational KPIs for time saved, cost saved, CRM quality, and graph coverage.")
    summary = api("GET", "/dashboard/summary")
    cards = st.columns(4)
    cards[0].metric("Meetings", summary["meetings_processed"])
    cards[1].metric("Fields avoided", summary["average_manual_fields_avoided"])
    cards[2].metric("Duplicate warnings", summary["duplicate_warnings_caught"])
    cards[3].metric("AI cost saved", f"${summary['estimated_ai_cost_saved']:.4f}")
    cards2 = st.columns(4)
    cards2[0].metric("CRM sync success", f"{summary['crm_sync_success_rate']:.0%}")
    cards2[1].metric("Token reduction", f"{summary['average_prompt_token_reduction']:.0%}")
    cards2[2].metric("Research minutes", summary["research_turnaround_minutes"])
    cards2[3].metric("Graph edges", summary["graph_coverage"]["edges"])
    activity = pd.DataFrame(summary["module_activity"])
    if not activity.empty:
        st.plotly_chart(px.bar(activity, x="module", y="count", title="Module activity"), use_container_width=True)
    st.json(summary["graph_coverage"])
