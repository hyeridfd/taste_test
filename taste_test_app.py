import streamlit as st
import pandas as pd
from datetime import datetime
import json
import base64
import time

# ===== Supabase helpers ======================================
from supabase import create_client, Client

def peek_role(jwt: str):
    if not jwt or '.' not in jwt:
        return None, {"error":"invalid jwt"}
    payload = jwt.split('.')[1] + '=' * (-len(jwt.split('.')[1]) % 4)
    data = json.loads(base64.urlsafe_b64decode(payload))
    return data.get("role"), data

role, _ = peek_role(st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", ""))

@st.cache_resource
def get_supabase(version: str = "v1") -> Client | None:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

sb = get_supabase(version=st.secrets.get("SUPABASE_CLIENT_VERSION", "v1"))

def insert_taste_response(response_data: dict):
    """미각테스트 응답을 Supabase에 저장"""
    sb = get_supabase()
    if sb is None:
        raise RuntimeError("Supabase client not configured")
    
    row = {
        "이메일": response_data.get("email", ""),
        "성명": response_data.get("name", ""),
        "성별": response_data.get("gender", ""),
        "나이": response_data.get("age", 0),
        "신장": response_data.get("height", 0),
        "체중": response_data.get("weight", 0),
        "단맛선호": response_data.get("sweet_preference", ""),
        "짠맛선호": response_data.get("salty_preference", ""),
        "제출시간": response_data.get("제출시간", ""),
        "응답데이터": json.dumps(response_data, ensure_ascii=False)
    }
    sb.table("taste_mpti_responses").insert(row).execute()

def fetch_taste_responses_df() -> pd.DataFrame:
    """Supabase에서 미각테스트 응답 조회"""
    sb = get_supabase()
    if sb is None:
        return pd.DataFrame()
    res = sb.table("taste_mpti_responses").select("*").order("제출시간", desc=True).execute()
    return pd.DataFrame(res.data or [])

# ===================================================================
# 페이지 설정
st.set_page_config(
    page_title="평창 웰니스 클래스 - 미각 MPTI",
    page_icon="🍽️",
    layout="wide"
)

# CSS 스타일링 - 개선된 디자인
st.markdown("""
    <style>
    /* 전체 배경 - 자연스러운 연한 연두색 */
    .stApp {
        background: linear-gradient(180deg, 
            #F1F8F4 0%,
            #E8F5E9 25%,
            #E0F2E9 50%,
            #D7F0DD 75%,
            #E8F5E9 100%
        );
        background-attachment: fixed;
    }
    
    /* 메인 컨테이너 */
    .main {
        padding: 2rem;
        max-width: 1000px;
        margin: 0 auto;
    }
    
    /* 메인 블록 컨테이너 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 헤더 스타일 */
    h1 {
        color: #2E7D32;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    h2, h3 {
        color: #388E3C;
        font-weight: 600;
    }



    /* ========== 성별 선택용 심플 스타일 (gender_input) ========== */
    div[data-testid="stRadio"][data-baseweb="radio"] {
        background: rgba(255, 255, 255, 0.5);
        padding: 0.8rem;
        border-radius: 10px;
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div {
        display: flex;
        gap: 1rem;
        justify-content: flex-start;
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div > label {
        background: white;
        border: 2px solid #E0E0E0;
        border-radius: 8px;
        padding: 0.8rem 2.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
        flex: none;
        min-width: 100px;
        text-align: center;
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div > label:hover {
        border-color: #4CAF50;
        box-shadow: 0 3px 10px rgba(76, 175, 80, 0.15);
        transform: translateY(-1px);
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div > label:has(input:checked) {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border: 2px solid #4CAF50;
        box-shadow: 0 3px 12px rgba(76, 175, 80, 0.25);
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] input[type="radio"] {
        display: none;
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div > label > div {
        font-size: 1rem;
        font-weight: 600;
        color: #424242;
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div > label:has(input:checked) > div {
        color: #2E7D32;
    }
    
    /* ========== 시료 선택용 큰 스타일 (sweet_input, salty_input) ========== */
    /* 라디오 버튼 커스텀 스타일 */
    div[data-testid="stRadio"] > label {
        font-size: 1.15rem;
        font-weight: 600;
        color: #2E7D32;
        margin-bottom: 1.5rem;
    }
    
    /* 라디오 버튼 컨테이너 스타일 - 카드형 디자인 */
    div[data-testid="stRadio"] > div {
        background: transparent;
        padding: 1.5rem 1rem;
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        max-width: 100%;
        flex-wrap: wrap;
    }
    
    /* 각 라디오 버튼 아이템 - 비커/실린더 디자인 */
    div[data-testid="stRadio"] > div > label {
        background: white;
        border: 3px solid #E0E0E0;
        border-radius: 20px;
        padding: 2rem 1.5rem;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-width: 150px;
        min-height: 200px;
        position: relative;
        overflow: hidden;
    }
    
    /* 호버 효과 */
    div[data-testid="stRadio"] > div > label:hover {
        transform: translateY(-12px) scale(1.03);
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.2);
        border-color: #BDBDBD;
    }
    
    /* 배경 애니메이션 효과 */
    div[data-testid="stRadio"] > div > label::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, transparent 0%, rgba(66, 165, 245, 0.1) 100%);
        opacity: 0;
        transition: opacity 0.4s ease;
        z-index: 0;
    }
    
    div[data-testid="stRadio"] > div > label:hover::before {
        opacity: 1;
    }
    
    /* 선택된 라디오 버튼 - 강한 시각적 피드백 */
    div[data-testid="stRadio"] > div > label:has(input:checked) {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border: 4px solid #4CAF50;
        box-shadow: 0 16px 48px rgba(76, 175, 80, 0.4),
                    0 0 0 4px rgba(76, 175, 80, 0.1);
        transform: translateY(-16px) scale(1.08);
    }
    
    div[data-testid="stRadio"] > div > label:has(input:checked)::before {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.15) 0%, rgba(56, 142, 60, 0.1) 100%);
        opacity: 1;
    }
    
    /* 라디오 버튼 숨기기 */
    div[data-testid="stRadio"] input[type="radio"] {
        display: none;
    }
    
    /* 시료 번호 텍스트 스타일 */
    div[data-testid="stRadio"] > div > label > div {
        font-size: 3.5rem;
        font-weight: 800;
        color: #757575;
        margin-top: 1rem;
        line-height: 1;
        position: relative;
        z-index: 1;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.4s ease;
    }
    
    div[data-testid="stRadio"] > div > label:hover > div {
        color: #616161;
        transform: scale(1.1);
    }
    
    div[data-testid="stRadio"] > div > label:has(input:checked) > div {
        color: #2E7D32;
        font-size: 4rem;
        text-shadow: 3px 3px 6px rgba(46, 125, 50, 0.2);
        animation: pulse 0.6s ease-in-out;
    }
    
    /* 펄스 애니메이션 */
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.15); }
    }
    /* ========== 성별 선택용 심플 스타일 (gender_input) ========== */
    div[data-testid="stRadio"][data-baseweb="radio"] {
        background: rgba(255, 255, 255, 0.5);
        padding: 0.8rem;
        border-radius: 10px;
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div {
        display: flex;
        gap: 1rem;
        justify-content: flex-start;
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div > label {
        background: white;
        border: 2px solid #E0E0E0;
        border-radius: 8px;
        padding: 0.8rem 2.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
        flex: none;
        min-width: 100px;
        text-align: center;
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div > label:hover {
        border-color: #4CAF50;
        box-shadow: 0 3px 10px rgba(76, 175, 80, 0.15);
        transform: translateY(-1px);
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div > label:has(input:checked) {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border: 2px solid #4CAF50;
        box-shadow: 0 3px 12px rgba(76, 175, 80, 0.25);
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] input[type="radio"] {
        display: none;
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div > label > div {
        font-size: 1rem;
        font-weight: 600;
        color: #424242;
    }
    
    div[data-testid="stRadio"][data-baseweb="radio"] > div > label:has(input:checked) > div {
        color: #2E7D32;
    }
    
    /* 라디오 버튼 커스텀 스타일 */
    div[data-testid="stRadio"] > label {
        font-size: 1.15rem;
        font-weight: 600;
        color: #2E7D32;
        margin-bottom: 1.5rem;
    }
    
    /* 라디오 버튼 컨테이너 스타일 - 카드형 디자인 */
    div[data-testid="stRadio"] > div {
        background: transparent;
        padding: 1.5rem 1rem;
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        max-width: 100%;
        flex-wrap: wrap;
    }
    
    /* 각 라디오 버튼 아이템 - 비커/실린더 디자인 */
    div[data-testid="stRadio"] > div > label {
        background: white;
        border: 3px solid #E0E0E0;
        border-radius: 20px;
        padding: 2rem 1.5rem;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-width: 150px;
        min-height: 200px;
        position: relative;
        overflow: hidden;
    }
    
    /* 호버 효과 */
    div[data-testid="stRadio"] > div > label:hover {
        transform: translateY(-12px) scale(1.03);
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.2);
        border-color: #BDBDBD;
    }
    
    /* 배경 애니메이션 효과 */
    div[data-testid="stRadio"] > div > label::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, transparent 0%, rgba(66, 165, 245, 0.1) 100%);
        opacity: 0;
        transition: opacity 0.4s ease;
        z-index: 0;
    }
    
    div[data-testid="stRadio"] > div > label:hover::before {
        opacity: 1;
    }
    
    /* 선택된 라디오 버튼 - 강한 시각적 피드백 */
    div[data-testid="stRadio"] > div > label:has(input:checked) {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border: 4px solid #4CAF50;
        box-shadow: 0 16px 48px rgba(76, 175, 80, 0.4),
                    0 0 0 4px rgba(76, 175, 80, 0.1);
        transform: translateY(-16px) scale(1.08);
    }
    
    div[data-testid="stRadio"] > div > label:has(input:checked)::before {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.15) 0%, rgba(56, 142, 60, 0.1) 100%);
        opacity: 1;
    }
    
    /* 라디오 버튼 숨기기 */
    div[data-testid="stRadio"] input[type="radio"] {
        display: none;
    }
    
    /* 시료 번호 텍스트 스타일 */
    div[data-testid="stRadio"] > div > label > div {
        font-size: 3.5rem;
        font-weight: 800;
        color: #757575;
        margin-top: 1rem;
        line-height: 1;
        position: relative;
        z-index: 1;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.4s ease;
    }
    
    div[data-testid="stRadio"] > div > label:hover > div {
        color: #616161;
        transform: scale(1.1);
    }
    
    div[data-testid="stRadio"] > div > label:has(input:checked) > div {
        color: #2E7D32;
        font-size: 4rem;
        text-shadow: 3px 3px 6px rgba(46, 125, 50, 0.2);
        animation: pulse 0.6s ease-in-out;
    }
    
    /* 펄스 애니메이션 */
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.15); }
    }
    
    /* 시료 아이콘 추가 */
    div[data-testid="stRadio"] > div > label::after {
        content: '🧪';
        font-size: 3rem;
        position: absolute;
        top: 1.5rem;
        opacity: 0.3;
        transition: all 0.4s ease;
    }
    
    div[data-testid="stRadio"] > div > label:hover::after {
        opacity: 0.5;
        transform: scale(1.1) rotate(10deg);
    }
    
    div[data-testid="stRadio"] > div > label:has(input:checked)::after {
        opacity: 0.8;
        transform: scale(1.2) rotate(0deg);
    }
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #B2DFDB;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: white;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #4DB6AC;
        box-shadow: 0 0 0 3px rgba(77, 182, 172, 0.1);
    }
    
    /* 라벨 스타일 */
    .stTextInput > label,
    .stNumberInput > label {
        font-weight: 600;
        color: #2E7D32;
        font-size: 1.05rem;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        border-radius: 15px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1.05rem;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Primary 버튼 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%);
        color: white;
    }
    
    /* Secondary 버튼 */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #81C784 0%, #66BB6A 100%);
        color: white;
    }
    
    /* 섹션 헤더 */
    .section-header {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 2rem 0 1.5rem 0;
        border-left: 5px solid #4CAF50;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    
    /* 파란색 박스 - 단맛 */
    .blue-box {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        padding: 2rem;
        border-radius: 20px;
        border-left: 6px solid #2196F3;
        margin: 2rem 0;
        box-shadow: 0 6px 20px rgba(33, 150, 243, 0.25);
        animation: fadeIn 0.5s ease-in;
    }
    
    /* 빨간색 박스 - 짠맛 */
    .red-box {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        padding: 2rem;
        border-radius: 20px;
        border-left: 6px solid #F44336;
        margin: 2rem 0;
        box-shadow: 0 6px 20px rgba(244, 67, 54, 0.25);
        animation: fadeIn 0.5s ease-in;
    }
    
    /* 초록색 박스 - 완료 */
    .green-box {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #4CAF50;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);
    }
    
    /* 통계 카드 */
    .stat-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: #757575;
        font-size: 0.95rem;
        font-weight: 500;
    }
    
    /* 페이드 인 애니메이션 */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* 프로그레스 바 */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #66BB6A 0%, #43A047 100%);
        border-radius: 10px;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #E8F5E9 0%, #C8E6C9 100%);
    }
    
    /* 데이터프레임 스타일 */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* 선택 박스 */
    .stSelectbox > div > div {
        border-radius: 12px;
        border: 2px solid #B2DFDB;
    }
    
    /* 다운로드 버튼 */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%);
        color: white;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    
    /* 체크박스 */
    .stCheckbox {
        background: rgba(255, 255, 255, 0.7);
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    /* 구분선 */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            #C8E6C9 50%, 
            transparent 100%
        );
    }
    
    /* 성공 메시지 */
    .stSuccess {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-left: 5px solid #4CAF50;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* 경고 메시지 */
    .stWarning {
        background: linear-gradient(135deg, #FFF9C4 0%, #FFF59D 100%);
        border-left: 5px solid #FBC02D;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* 에러 메시지 */
    .stError {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border-left: 5px solid #F44336;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* 정보 메시지 */
    .stInfo {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        border-left: 5px solid #2196F3;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* 빈 공간 제거 */
    .element-container:has(> .stMarkdown > div > p:empty) {
        display: none;
    }
    
    /* 불필요한 여백 제거 */
    .block-container {
        padding-top: 3rem;
    }
    
    /* 반응형 디자인 */
    @media (max-width: 768px) {
        div[data-testid="stRadio"] > div {
            gap: 1rem;
        }
        
        div[data-testid="stRadio"] > div > label {
            min-width: 130px;
            min-height: 180px;
            padding: 1.5rem 1rem;
        }
        
        div[data-testid="stRadio"] > div > label > div {
            font-size: 3rem;
        }
        
        div[data-testid="stRadio"] > div > label:has(input:checked) > div {
            font-size: 3.5rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'page' not in st.session_state:
    st.session_state.page = 0
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False

# 관리자 비밀번호
ADMIN_PASSWORD = "admin123"

def page_intro():
    # 헤더 이미지 또는 타이틀
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem 0;">
        <h1 style="font-size: 3rem; color: #2E7D32; margin-bottom: 0.5rem;">
            🍽️ 평창 웰니스 클래스
        </h1>
        <p style="font-size: 1.3rem; color: #558B2F; font-weight: 500;">
            나의 미각탐험 ! MPTI
        </p>
        <p style="font-size: 1rem; color: #7CB342; font-style: italic;">
            My Personal Taste Index
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 🌿 안녕하세요!
    
    '평창 웰니스 클래스'에서 '미각 MPTI(맛 선호도 평가를 통한 나의 미각 MPTI 확인하기)' 프로그램을 기획한 
    **서울대학교 정밀푸드솔루션연구실**입니다.
    
    먼저 귀중한 시간을 내어 테스트에 참여해주셔서 진심으로 감사드립니다. 🙏
    
    본 테스트는 **단맛, 짠맛의 선호도**를 측정하기 위해 설계되었습니다.
    """)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #FFF9C4 0%, #FFF59D 100%); 
                padding: 1.5rem; border-radius: 15px; border-left: 5px solid #FBC02D; 
                margin: 1.5rem 0; box-shadow: 0 4px 15px rgba(251, 192, 45, 0.2);">
        <h4 style="color: #F57F17; margin-bottom: 1rem;">📋 테스트 안내</h4>
        <p style="font-size: 1.05rem; line-height: 1.8; color: #424242;">
            • <strong>⏱️ 소요 시간</strong>: 약 15~20분<br>
            • <strong>🔬 진행 방법</strong>: 시료를 3초간 입에 담고 뱉은 후 가장 높은 선호도의 시료를 하나만 체크<br>
            • <strong>✅ 참여 방법</strong>: 설문지를 제출하시는 것으로 연구 참여에 대한 동의 의사가 확인됩니다
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    본 테스트와 관련하여 궁금하신 점이나 문의사항이 있으시면, 
    아래에 제시된 연구자의 이메일로 문의해 주십시오.
    
    ---
    
    **📧 연구자 연락처**:
    - 류혜리 (fwm825@snu.ac.kr)
    - 유정연 (98you21@snu.ac.kr)
    """)
    
    st.markdown("### 📧 시작하기")
    email = st.text_input("이메일 주소를 입력해주세요 *", placeholder="example@email.com", key="email_input")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 테스트 시작하기", type="primary", use_container_width=True):
            if email and "@" in email:
                st.session_state.responses['email'] = email
                st.session_state.page = 1
                st.rerun()
            else:
                st.error("❌ 유효한 이메일 주소를 입력해주세요.")

def page_basic_info():
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1>📝 기본 정보</h1>
        <p style="color: #558B2F; font-size: 1.1rem;">다음 질문에 응답해 주시기 바랍니다</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 성명
    name = st.text_input("👤 성명 *", value=st.session_state.responses.get('name', ''), placeholder="홍길동", key="name_input")
    
    # 성별
    st.markdown("#### ⚥ 성별 *")
    gender = st.radio("성별 선택", ["남", "여"], 
                     index=0 if st.session_state.responses.get('gender', '남') == '남' else 1,
                     horizontal=True,
                     key="gender_input",
                     label_visibility="collapsed")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🎂 나이")
        age = st.number_input("나이 *", min_value=1, max_value=120, 
                             value=st.session_state.responses.get('age', 30),
                             label_visibility="collapsed",
                             key="age_input")
    
    with col2:
        st.markdown("#### 📏 신장")
        height = st.number_input("신장(cm) *", min_value=50, max_value=250, 
                                value=st.session_state.responses.get('height', 170),
                                label_visibility="collapsed",
                                key="height_input")
    
    with col3:
        st.markdown("#### ⚖️ 체중")
        weight = st.number_input("체중(kg) *", min_value=20, max_value=300, 
                                value=st.session_state.responses.get('weight', 70),
                                label_visibility="collapsed",
                                key="weight_input")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 이전", key="prev_basic"):
            st.session_state.page = 0
            st.rerun()
    
    with col2:
        if st.button("다음 단계로 →", type="primary", use_container_width=True, key="next_basic"):
            if name:
                st.session_state.responses['name'] = name
                st.session_state.responses['gender'] = gender
                st.session_state.responses['age'] = age
                st.session_state.responses['height'] = height
                st.session_state.responses['weight'] = weight
                st.session_state.page = 2
                st.rerun()
            else:
                st.error("❌ 모든 필수 항목을 입력해주세요.")

def page_sweet_preference():
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1>🍑 단맛 선호도 조사</h1>
        <p style="color: #1976D2; font-size: 1.1rem;">복숭아 음료 테스트</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); 
                padding: 2rem; border-radius: 20px; border-left: 6px solid #2196F3; 
                margin: 2rem 0; box-shadow: 0 6px 20px rgba(33, 150, 243, 0.25);">
        <h4 style="color: #1565C0; margin-bottom: 1rem;">🔵 파란 글씨 표시된 시료</h4>
        <p style="font-size: 1.05rem; line-height: 1.8;">
            <strong>• 복숭아 음료를 마신다고 생각하면서</strong>,<br>
            시료 순서대로 <strong>(1 → 2 → 3 → 4 → 5)</strong> 맛을 보고<br>
            <strong style="color: #1565C0;">가장 높은 선호도의 시료를 하나만 체크</strong>해주세요 ✓
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🧪 시료 선택")
    st.markdown("**음료수를 마신다고 생각했을 때, 가장 선호하는 시료를 선택해주세요 ***")
    
    # 라디오 버튼
    current_value = st.session_state.responses.get('sweet_preference', None)
    
    sweet_preference = st.radio(
        "시료 선택",
        options=["1", "2", "3", "4", "5"],
        index=None if current_value is None else ["1", "2", "3", "4", "5"].index(current_value),
        horizontal=True,
        key="sweet_input",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 이전", key="prev_sweet"):
            st.session_state.page = 1
            st.rerun()
    
    with col2:
        if st.button("다음 단계로 →", type="primary", key="next_sweet", use_container_width=True):
            if sweet_preference:
                st.session_state.responses['sweet_preference'] = sweet_preference
                st.session_state.page = 3
                st.rerun()
            else:
                st.error("❌ 시료를 선택해주세요.")

def page_salty_preference():
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1>🥣 짠맛 선호도 조사</h1>
        <p style="color: #D32F2F; font-size: 1.1rem;">콩나물국 테스트</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%); 
                padding: 2rem; border-radius: 20px; border-left: 6px solid #F44336; 
                margin: 2rem 0; box-shadow: 0 6px 20px rgba(244, 67, 54, 0.25);">
        <h4 style="color: #C62828; margin-bottom: 1rem;">🔴 빨간 글씨 표시된 시료</h4>
        <p style="font-size: 1.05rem; line-height: 1.8;">
            <strong>• 콩나물국을 먹는다고 생각하면서</strong>,<br>
            시료 순서대로 <strong>(1 → 2 → 3 → 4 → 5)</strong> 맛을 보고<br>
            <strong style="color: #C62828;">가장 높은 선호도의 시료를 하나만 체크</strong>해주세요 ✓
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🧪 시료 선택")
    st.markdown("**콩나물국을 먹는다고 생각했을 때, 가장 선호하는 시료를 선택해주세요 ***")
    
    # 라디오 버튼
    current_value = st.session_state.responses.get('salty_preference', None)
    
    salty_preference = st.radio(
        "시료 선택",
        options=["1", "2", "3", "4", "5"],
        index=None if current_value is None else ["1", "2", "3", "4", "5"].index(current_value),
        horizontal=True,
        key="salty_input",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 이전", key="prev_salty"):
            st.session_state.page = 2
            st.rerun()
    
    with col2:
        if st.button("✅ 제출하기", type="primary", key="submit", use_container_width=True):
            if salty_preference:
                st.session_state.responses['salty_preference'] = salty_preference
                st.session_state.page = 4
                st.rerun()
            else:
                st.error("❌ 시료를 선택해주세요.")

def page_complete():
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 3rem;">✅ 테스트 완료!</h1>
        <p style="color: #558B2F; font-size: 1.3rem; margin-top: 1rem;">소중한 시간 내어 참여해주셔서 감사합니다 🙏</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Supabase에 자동 저장
    if 'saved_to_db' not in st.session_state:
        response_data = {
            "제출시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **st.session_state.responses
        }
        
        # Supabase 저장 시도
        sb = get_supabase()
        if sb:
            try:
                insert_taste_response(response_data)
                st.session_state.saved_to_db = True
                st.success("**✅ 응답이 성공적으로 저장되었습니다!**")
            except Exception as e:
                st.warning(f"⚠️ 데이터베이스 저장 중 오류 발생: {e}")
                st.session_state.saved_to_db = False
        else:
            st.warning("⚠️ Supabase 연결이 설정되지 않았습니다. 로컬 다운로드만 가능합니다.")
            st.session_state.saved_to_db = False
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); 
                padding: 2rem; border-radius: 15px; border-left: 5px solid #4CAF50; 
                margin: 1.5rem 0; box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);">
        <h3 style="color: #2E7D32;">🎉 감사합니다!</h3>
        <p style="font-size: 1.05rem; line-height: 1.8; color: #424242;">
            귀하의 소중한 응답이 성공적으로 제출되었습니다.<br><br>
            본 연구에 참여해 주셔서 진심으로 감사드립니다.<br><br>
            여러분의 데이터는 정밀 식의학 연구 발전에 큰 도움이 될 것입니다. 💚
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 제출 정보 표시
    if st.session_state.get('saved_to_db', False):
        # BMI 계산
        height_m = st.session_state.responses.get('height', 170) / 100
        weight_kg = st.session_state.responses.get('weight', 70)
        bmi = weight_kg / (height_m ** 2)
        
        st.markdown("### 📋 제출 완료 요약")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            - **👤 이름**: {st.session_state.responses.get('name', '-')}
            - **📧 이메일**: {st.session_state.responses.get('email', '-')}
            - **🎂 나이**: {st.session_state.responses.get('age', '-')}세
            - **⚥ 성별**: {st.session_state.responses.get('gender', '-')}
            """)
        
        with col2:
            st.markdown(f"""
            - **📏 신장**: {st.session_state.responses.get('height', '-')}cm
            - **⚖️ 체중**: {st.session_state.responses.get('weight', '-')}kg
            - **📊 BMI**: {bmi:.1f}
            - **📅 제출**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """)
        
        st.markdown("---")
        
        st.markdown(f"""
        ### 🍽️ 미각 선호도 결과
        
        <div style="display: flex; justify-content: space-around; margin: 2rem 0;">
            <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); border-radius: 15px; flex: 1; margin: 0 1rem;">
                <div style="font-size: 2.5rem;">🍑</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #1565C0; margin: 0.5rem 0;">시료 {st.session_state.responses.get('sweet_preference', '-')}</div>
                <div style="color: #1976D2;">단맛 선호</div>
            </div>
            <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%); border-radius: 15px; flex: 1; margin: 0 1rem;">
                <div style="font-size: 2.5rem;">🥣</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #C62828; margin: 0.5rem 0;">시료 {st.session_state.responses.get('salty_preference', '-')}</div>
                <div style="color: #D32F2F;">짠맛 선호</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 액션 버튼들
    col1, col2 = st.columns(2)
    
    with col1:
        response_data = {
            "제출시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **st.session_state.responses
        }
        
        json_str = json.dumps(response_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 응답 데이터 다운로드",
            data=json_str,
            file_name=f"미각MPTI_{st.session_state.responses.get('name', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        if st.button("🔄 처음으로 돌아가기", use_container_width=True):
            st.session_state.page = 0
            st.session_state.responses = {}
            if 'saved_to_db' in st.session_state:
                del st.session_state.saved_to_db
            st.rerun()

def admin_login():
    """관리자 로그인 페이지"""
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1>🔐 관리자 로그인</h1>
    </div>
    """, unsafe_allow_html=True)
    
    password = st.text_input("🔑 비밀번호를 입력하세요", type="password", key="admin_password")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🚪 로그인", type="primary", use_container_width=True):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 올바르지 않습니다.")
    
    with col2:
        if st.button("↩️ 취소", use_container_width=True):
            st.session_state.admin_mode = False
            st.rerun()

def admin_page():
    """관리자 페이지"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 2rem; border-radius: 20px; text-align: center; margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
        <h1 style="color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🔧 관리자 대시보드</h1>
        <p style="font-size: 1.1rem; margin-top: 0.5rem;">미각 MPTI 응답 관리 시스템</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 로그아웃 버튼
    col1, col2, col3 = st.columns([4, 1, 1])
    with col3:
        if st.button("🚪 로그아웃"):
            st.session_state.admin_authenticated = False
            st.rerun()
    
    sb = get_supabase()
    df_db = fetch_taste_responses_df() if sb else pd.DataFrame()
    
    if not df_db.empty:
        # 통계 카드
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(df_db)}</div>
                <div class="stat-label">📊 총 응답 수</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            unique_users = df_db['이메일'].nunique() if '이메일' in df_db.columns else 0
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{unique_users}</div>
                <div class="stat-label">👥 참여자 수</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_age = int(df_db['나이'].mean()) if '나이' in df_db.columns else 0
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{avg_age}세</div>
                <div class="stat-label">🎂 평균 나이</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            today_str = datetime.now().strftime('%Y-%m-%d')
            today_count = df_db["제출시간"].astype(str).str.contains(today_str).sum() if "제출시간" in df_db.columns else 0
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{today_count}</div>
                <div class="stat-label">📅 오늘 응답</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # 응답 목록
        st.markdown("### 📊 응답 기록")
        
        # 표시할 컬럼 선택
        display_cols = ["성명", "이메일", "성별", "나이", "신장", "체중", "단맛선호", "짠맛선호", "제출시간"]
        available_cols = [col for col in display_cols if col in df_db.columns]
        
        st.dataframe(df_db[available_cols], use_container_width=True, height=400)
        
        # CSV 다운로드
        csv = df_db.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 전체 데이터 CSV 다운로드",
            data=csv,
            file_name=f"미각MPTI_전체응답_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # 개별 응답 상세보기
        st.markdown("### 🔍 개별 응답 상세보기")
        
        if '성명' in df_db.columns and '이메일' in df_db.columns:
            selected_option = st.selectbox(
                "참여자 선택",
                options=df_db.apply(lambda x: f"{x['성명']} ({x['이메일']})", axis=1).tolist(),
                key="admin_select"
            )
            
            if selected_option:
                selected_idx = df_db.apply(lambda x: f"{x['성명']} ({x['이메일']})", axis=1).tolist().index(selected_option)
                selected_row = df_db.iloc[selected_idx]
                
                # BMI 계산
                if '신장' in selected_row and '체중' in selected_row:
                    height_m = selected_row['신장'] / 100
                    bmi = selected_row['체중'] / (height_m ** 2)
                else:
                    bmi = 0
                
                st.markdown("""
                <div style="background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); 
                            padding: 2rem; border-radius: 15px; border-left: 5px solid #4CAF50; 
                            margin: 1.5rem 0; box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);">
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    - **👤 성명**: {selected_row.get('성명', '-')}
                    - **📧 이메일**: {selected_row.get('이메일', '-')}
                    - **⚥ 성별**: {selected_row.get('성별', '-')}
                    - **🎂 나이**: {selected_row.get('나이', '-')}세
                    """)
                
                with col2:
                    st.markdown(f"""
                    - **📏 신장**: {selected_row.get('신장', '-')}cm
                    - **⚖️ 체중**: {selected_row.get('체중', '-')}kg
                    - **📊 BMI**: {bmi:.1f}
                    - **📅 제출시간**: {selected_row.get('제출시간', '-')}
                    """)
                
                st.markdown("---")
                
                st.markdown(f"""
                #### 🍽️ 미각 선호도
                - **🍑 단맛 선호**: 시료 {selected_row.get('단맛선호', '-')}
                - **🥣 짠맛 선호**: 시료 {selected_row.get('짠맛선호', '-')}
                """)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 상세 응답 데이터 표시
                if '응답데이터' in selected_row and selected_row['응답데이터']:
                    try:
                        response_detail = json.loads(selected_row['응답데이터'])
                        with st.expander("📝 상세 응답 데이터 (JSON)"):
                            st.json(response_detail)
                    except:
                        st.warning("⚠️ 응답 데이터를 불러올 수 없습니다.")
    
    else:
        st.info("📝 아직 제출된 응답이 없습니다.")

# 메인 로직
def main():
    # 사이드바
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #2E7D32;">🌿 평창 웰니스</h2>
            <p style="color: #558B2F;">미각 MPTI</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        admin_mode = st.checkbox("🔧 관리자 모드", value=st.session_state.get('admin_mode', False), key='admin_mode')
        
        # 진행률 표시
        if not admin_mode and st.session_state.page > 0 and st.session_state.page < 4:
            st.markdown("### 📊 진행 상황")
            progress = st.session_state.page / 4
            st.progress(progress)
            st.markdown(f"**{int(progress * 100)}%** 완료")
            st.markdown(f"**{st.session_state.page}** / 4 단계")
            
            # 단계 표시
            steps = ["기본정보", "단맛", "짠맛", "완료"]
            for i, step in enumerate(steps, 1):
                if i < st.session_state.page:
                    st.markdown(f"✅ {step}")
                elif i == st.session_state.page:
                    st.markdown(f"🔵 **{step}**")
                else:
                    st.markdown(f"⚪ {step}")
        
        st.markdown("---")
        
        st.markdown("""
        <div style="font-size: 0.85rem; color: #757575; padding: 1rem 0;">
            <p><strong>연구기관</strong></p>
            <p>서울대학교<br>정밀푸드솔루션연구실</p>
            <br>
            <p><strong>문의</strong></p>
            <p>fwm825@snu.ac.kr<br>98you21@snu.ac.kr</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 메인 컨텐츠
    if admin_mode:
        # 관리자 인증 확인
        if not st.session_state.admin_authenticated:
            admin_login()
            return
        else:
            admin_page()
            return
    
    # 일반 사용자 페이지
    if st.session_state.page == 0:
        page_intro()
    elif st.session_state.page == 1:
        page_basic_info()
    elif st.session_state.page == 2:
        page_sweet_preference()
    elif st.session_state.page == 3:
        page_salty_preference()
    elif st.session_state.page == 4:
        page_complete()

if __name__ == "__main__":
    main()
