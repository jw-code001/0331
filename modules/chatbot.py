
# pip install langchain langchain-core langchain-community
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

class SkinChatbot:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        self.system_prompt = SystemMessage(content="""
            당신은 피부과 및 에스테틱 전문 마케팅 컨설턴트입니다. 
            사용자의 설문 데이터를 바탕으로 비즈니스 전략을 제안하거나, 
            피부 고민에 대한 전문적인 조언을 친절하게 제공하세요.
        """)

    def get_response(self, user_query, chat_history):
        messages = [self.system_prompt]
        # 이전 대화 기록 추가
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=user_query))
        response = self.llm.invoke(messages)
        return response.content