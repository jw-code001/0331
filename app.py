import streamlit as st
import pandas as pd
from modules.data_manager import SheetManager
from modules.visualizer import SkinVisualizer
from pages.form.normal import show_normal_form
# app.py 상단에 추가
from modules.chatbot import SkinChatbot


@st.cache_data(ttl=300)
def load_data():
    db = SheetManager()
    return db.get_all_responses_df()

@st.cache_resource
def get_chatbot():
    return SkinChatbot()

@st.cache_data
def get_visualizer(df):
    return SkinVisualizer(df)

def render_chatbot_ui():
    # 1. CSS Injection: 오른쪽 하단 플로팅 버튼 및 채팅창 스타일
    st.markdown("""
        <style>
        .floating-chat {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background-color: #FF4B4B;
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 60px;
            font-size: 30px;
            cursor: pointer;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
            z-index: 9999;
        }
        .st-emotion-cache-hqmjvr{
          max-height:200px;
        
        }
        </style>
    """, unsafe_allow_html=True)

    # 세션 상태 초기화
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 플로팅 버튼
    if st.button("💬", key="chat_button"):
        st.session_state.chat_open = not st.session_state.chat_open

    # 3. 채팅창 사이드바
    if st.session_state.chat_open:
        with st.sidebar:
            st.title("🤖 AI 마케팅 어드바이저")
            
            # --- [FAQ 섹션] 벡터 DB 관련 정보 제공 ---
            with st.expander("📌 벡터 DB & 데이터 동기화 FAQ", expanded=True):
                st.markdown("""
                * **Q. 데이터가 실시간인가요?** 설문 제출 또는 동기화 시점에 `vector_db`에 정제되어 저장됩니다.
                * **Q. 특수문자 처리는요?** 내부 `clean_text` 로직이 불필요한 기호를 자동 제거합니다.
                * **Q. 답변의 기준은?** 구글 시트의 질문/응답 데이터를 임베딩하여 분석합니다.
                """)
            
            st.info("데이터를 기반으로 궁금한 점을 물어보세요!")
            st.divider()

            # 채팅 히스토리 및 인터페이스
            chat_container = st.container(height=400)

            # 첫 방문 시 웰컴 메시지
            if not st.session_state.messages:
                welcome = "분석 준비가 완료되었습니다. **다른 질문이 있으신가요?**"
                st.session_state.messages.append({"role": "assistant", "content": welcome})

            for message in st.session_state.messages:
                with chat_container.chat_message(message["role"]):
                    st.markdown(message["content"])

            # 채팅 입력 및 처리
            if prompt := st.chat_input("메시지를 입력하세요...", key="chat_input_widget"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_container.chat_message("user"):
                    st.markdown(prompt)

                with chat_container.chat_message("assistant"):
                    with st.spinner("데이터 분석 중..."):
                        bot = get_chatbot() #
                        response = bot.get_response(prompt, st.session_state.messages[:-1]) #
                        st.markdown(response)
                        st.caption("💡 다른 질문이 있으신가요? 언제든 말씀해 주세요.")
                
                st.session_state.messages.append({"role": "assistant", "content": response})


    

# --- [함수 1] 구글 응답 결과 요약 보고서 (매개변수 df 추가) ---
def render_business_summary(df): # (수정) df를 인자로 받도록 변경
    st.subheader("📝 문항별 응답 요약 (Top Selection)")    
    
    if df.empty:
        st.info("데이터가 충분하지 않습니다.")
        return

    summary_list = []
    
    # 12개 질문에 대해 순회 (인덱스 1부터 시작)
    for i in range(1, len(df.columns)):
        col_name = df.columns[i]
        
        # 주관식/객관식 판별 및 통계 로직
        if "주로 사용" in col_name or "바라는 점" in col_name:
            top_val = "주관식 응답"
            count = f"{df[col_name].nunique()}개의 다양한 의견"
        else:
            series = df[col_name].str.split(', ').explode()
            top_choice = series.value_counts()
            
            if not top_choice.empty:
                top_val = top_choice.index[0]
                count = f"{top_choice.values[0]}명 선택"
            else:
                top_val = "-"
                count = "0명"

        summary_list.append({
            "문항 번호": f"Q{i}",
            "질문 내용 요약": col_name[:25] + "..." if len(col_name) > 25 else col_name,
            "최다 선택 답변": top_val,
            "응답 수": count
        })

    summary_df = pd.DataFrame(summary_list)
    st.table(summary_df)



# --- [함수 2] 시각화 대시보드 ---
def render_visual_dashboard(df):
    st.subheader("📊 실시간 데이터 시각화")
    #캐싱기능 추가 함수사용
    viz = get_visualizer(df)
    
    col1, col2 = st.columns(2)
    with col1:
        viz.plot_target_distribution()
    with col2:
        viz.plot_skin_concerns()
        
    st.divider()
    viz.plot_visit_vs_reason()
    
    st.divider()
    col3, col4 = st.columns(2)
    with col3:
        viz.plot_cost_analysis()
    with col4:
        viz.plot_selection_criteria()

# --- 메인 실행부 ---
def main():
    st.set_page_config(page_title="Skin AI Analysis", layout="wide")
    # 데이터 로드
    try:
        df = load_data()
    except Exception as e:
        st.error(f"데이터 연결 실패: {e}")
        df = pd.DataFrame() 

    # 사이드바 메뉴
    st.sidebar.title("🧭 Navigation")
    menu = st.sidebar.selectbox("Go to", ["Home", "Normal Survey", "AI Prediction"])

    if menu == "Home":
        st.write("# 🏠 Dashboard Home")
        
        if not df.empty:
            # (수정) 함수 호출 시 로드한 df를 전달합니다.
            render_business_summary(df) 
            st.write("---")
            render_visual_dashboard(df)
        else:
            st.info("수집된 데이터가 없습니다. 설문을 먼저 진행해주세요.")
        
    elif menu == "Normal Survey":
        show_normal_form()

    elif menu == "AI Prediction":
        st.write("## 🤖 AI 분석 리포트 (준비 중)")
    # 🔥 쳇봇 UI를 메인 루프 마지막에 한 번만 호출
    render_chatbot_ui()

if __name__ == "__main__":
    main()
    