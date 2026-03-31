
# 동기화(Sync) 전략
# 시트 내용이 변경될 때마다 벡터 DB를 업데이트

import os # os랑 소통하는 놈이 최중요 파일
import re
import pandas as pd
# 성공했던 모델을 쓰기 위해 추가 (9~11 구글의 (과금)정책의 변경에 따라 에러 발생 잘될거임 !!)
from langchain_huggingface import HuggingFaceEmbeddings  # 무료라서 저품질... vector db는 돈내고 써야함...
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

class SkinVectorDB:
    def __init__(self):
        # --- [성공 포인트 1] 검증된 임베딩 모델로 교체 ---
        # Google 임베딩 대신, 이전에 성공했던 모델을 사용하여 404 에러를 원천 차단합니다.
        self.model_name = "jhgan/ko-sroberta-multitask"
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name
        )
        
        # 저장 경로
        self.persist_directory = os.path.join(os.getcwd(), "chroma_db")

    def clean_text(self, text):
        # --- [성공 포인트 2] 이전 파일의 '최적화 세탁기' 로직 그대로 이식 ---
        # 유니코드 대리쌍(Surrogate)과 제어문자를 제거하여 임베딩 시 발생할 수 있는 치명적인 에러를 방지합니다.
        if not isinstance(text, str):
            text = str(text)
        
        # 1. 유니코드 대리쌍(Surrogate) 제거
        cleaned = re.sub(r'[\ud800-\udfff]', '', text)
        
        # 2. 제어문자 제거
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
        
        # 3. 필수 문장부호 제외 특수기호 공백 치환
        cleaned = re.sub(r'[^\w\s.,?!%()~-]', ' ', cleaned)
        
        # 4. 다중 공백 압축
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

    def upsert_survey_data(self, df):
        if df.empty:
            return "저장할 데이터가 없습니다."

        documents = []
        for idx, row in df.iterrows():
            # 데이터 결합
            content = f"사용자 ID: {row[0]}\n"
            for col, val in row.items():
                content += f"{col}: {val}\n"
            
            # 🔥 저장 전 세탁기 가동 (성공 로직 적용)
            # 저장 직전에 clean_text를 거치도록 설계되어 DB에 깨끗한 데이터만
            cleaned_content = self.clean_text(content)
            
            doc = Document(
                page_content=cleaned_content, 
                metadata={"user_id": str(row[0])}
            )
            documents.append(doc)

        # Chroma DB 저장
        vector_db = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        return f"✅ {len(documents)}건의 데이터가 정제되어 벡터 DB에 저장되었습니다."

    def query_similar_data(self, query, k=3):
        # 검색어도 정제해서 비교
        cleaned_query = self.clean_text(query)
        vector_db = Chroma(
            persist_directory=self.persist_directory, 
            embedding_function=self.embeddings
        )
        return vector_db.similarity_search(cleaned_query, k=k)

if __name__ == "__main__":
    vdb = SkinVectorDB()
    print("✅ 성공 로직 이식 완료 (jhgan/ko-sroberta-multitask 사용)")

    test_data = pd.DataFrame([
        ["user_01", "30대", "여성", "여드름", "비용 부담 ◦ ▪ *", "브랜드A", "얼굴", "월 2회", "10만원", "5만원", "전문성", "없음"]
    ])
    
    print("🚀 정제 및 동기화 시작...")
    result = vdb.upsert_survey_data(test_data)
    print(result)

    print("\n🔍 검색 테스트: '비용이 고민이에요'")
    search_result = vdb.query_similar_data("비용이 고민이에요", k=1)
    
    if search_result:
        print(f"찾은 결과: {search_result[0].page_content[:50]}...")