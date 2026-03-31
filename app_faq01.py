import streamlit as st
import pandas as pd
from modules.data_manager import SheetManager
from modules.visualizer import SkinVisualizer
from pages.form.normal import show_normal_form
from modules.chatbot import SkinChatbot

# --- [데이터 및 리소스 캐싱] ---
@st.cache_data(ttl=300)
def load_data():
    try:
        db = SheetManager()
        return db.get_all_responses_df()
    except Exception as e:
        st.error(f"데이터 연결 실패: {e}")
        return pd.DataFrame()

@st.cache_resource
def get_chatbot():
    return SkinChatbot()

@st.cache_data
def get_visualizer(df):
    return SkinVisualizer(df)

# --- [상단 스타일 및 FAQ 렌더링 함수] ---
def render_sidebar_faq():
    """사이드바 하단에 항상 노출되는 FAQ 섹션"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💡 실험 데이터 FAQ")
    
    faqs = [
        ("데이터는 실시간인가요?", "구글 시트와 연동되어 실시간으로 반영됩니다."),
        ("분석 대상 문항은?", "피부 고민 등 총 12개 주요 문항을 분석합니다."),
        ("데이터 정제 방식은?", "clean_text 로직이 특수문자를 자동 제거합니다."),
        ("답변의 근거는?", "시트의 응답 데이터를 벡터화하여 분석합니다."),
        ("주관식 의견 분석은?", "AI가 텍스트 내용을 요약하여 결과에 반영합니다."),
        ("보안은 안전한가요?", "Google OAuth 2.0 인증으로 안전하게 관리됩니다."),
        ("업데이트 주기?", "캐시 설정에 따라 5분마다 자동 갱신됩니다."),
        ("오류 발생 시?", "데이터 매니저 모듈의 연결 상태를 확인하세요.")
    ]

    for q, a in faqs:
        with st.sidebar.expander(f"Q. {q}"):
            st.write(a)

def render_chatbot_ui():
    # 1. CSS Injection
    st.markdown("""
        <style>
        .st-emotion-cache-hqmjvr { max-height: 200px; }
        </style>
    """, unsafe_allow_html=True)

    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 2. 플로팅 버튼 (우측 하단)
    if st.button("💬", key="chat_button"):
        st.session_state.chat_open = not st.session_state.chat_open

    # 3. 채팅창 (열렸을 때만 사이드바 상단에 표시)
    if st.session_state.chat_open:
        with st.sidebar:
            st.title("🤖 AI 마케팅 어드바이저")
            chat_container = st.container(height=400)

            if not st.session_state.messages:
                welcome = "분석 준비 완료! **무엇을 도와드릴까요?**"
                st.session_state.messages.append({"role": "assistant", "content": welcome})

            for message in st.session_state.messages:
                with chat_container.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("메시지 입력...", key="chat_input_widget"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_container.chat_message("user"):
                    st.markdown(prompt)

                with chat_container.chat_message("assistant"):
                    with st.spinner("분석 중..."):
                        bot = get_chatbot()
                        response = bot.get_response(prompt, st.session_state.messages[:-1])
                        st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.divider()

def render_business_summary(df):
    st.subheader("📝 문항별 응답 요약")    
    if df.empty:
        st.info("데이터가 없습니다.")
        return

    summary_list = []
    for i, col_name in enumerate(df.columns[1:], 1):
        if "주로 사용" in col_name or "바라는 점" in col_name:
            top_val, count = "주관식", f"{df[col_name].nunique()}건"
        else:
            series = df[col_name].str.split(', ').explode()
            top_choice = series.value_counts()
            top_val = top_choice.index[0] if not top_choice.empty else "-"
            count = f"{top_choice.values[0]}명" if not top_choice.empty else "0명"

        summary_list.append({
            "번호": f"Q{i}",
            "질문 요약": col_name[:25] + "...",
            "최다 답변": top_val,
            "응답수": count
        })
    # width='stretch'를 사용하여 경고 해결
    st.table(pd.DataFrame(summary_list))

def render_visual_dashboard(df):
    st.subheader("📊 실시간 데이터 시각화")
    viz = get_visualizer(df)
    
    # 시각화 라이브러리 내부의 use_container_width=True를 
    # width='stretch'로 변경해야 경고가 완전히 사라집니다.
    col1, col2 = st.columns(2)
    with col1:
        viz.plot_target_distribution()
    with col2:
        viz.plot_skin_concerns()
    
    st.divider()
    viz.plot_visit_vs_reason()

# --- [메인 실행부] ---
def main():
    st.set_page_config(page_title="Skin AI Analysis", layout="wide")
    
    df = load_data()

    # 사이드바 상단 메뉴
    st.sidebar.title("🧭 Navigation")
    menu = st.sidebar.selectbox("Go to", ["Home", "Normal Survey", "AI Prediction"])

    if menu == "Home":
        st.write("# 🏠 Dashboard Home")
        if not df.empty:
            render_business_summary(df) 
            st.write("---")
            render_visual_dashboard(df)
        else:
            st.info("수집된 데이터가 없습니다.")
        
    elif menu == "Normal Survey":
        show_normal_form()

    elif menu == "AI Prediction":
        st.write("## 🤖 AI 분석 리포트 (준비 중)")

    # 1. 챗봇 UI (버튼 클릭 시 사이드바 상단에 나타남)
    render_chatbot_ui()
    
    # 2. FAQ UI (사이드바 하단에 항상 고정)
    render_sidebar_faq()

if __name__ == "__main__":
    main()