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

# CSS 스타일링 - 웰니스 & 자연 테마 + 실린더 디자인
st.markdown("""
    <style>
    /* 전체 배경 - 자연스러운 연한 민트/초록 */
    .stApp {
        background: linear-gradient(180deg, 
            #F0F8F5 0%,
            #E8F5F0 50%,
            #F0F8F5 100%
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
        color: #2E5945;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    h2, h3 {
        color: #3D6B54;
        font-weight: 600;
    }
    
    /* ========== 기본 라디오 버튼 스타일 리셋 ========== */
    div[data-testid="stRadio"] > div {
        background: transparent;
        padding: 0.5rem;
        display: flex;
        gap: 1rem;
    }
    
    div[data-testid="stRadio"] > div > label {
        background: white;
        border: 2px solid #D4CFC4;
        border-radius: 10px;
        padding: 0.8rem 2.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        min-width: 100px;
        min-height: auto;
        display: flex;
        align-items: center;
        justify-content: center;
        position: static;
        transform: none;
    }
    
    div[data-testid="stRadio"] > div > label:hover {
        border-color: #5D8A6F;
        box-shadow: 0 3px 12px rgba(93, 138, 111, 0.15);
        transform: translateY(-2px);
    }
    
    div[data-testid="stRadio"] > div > label:has(input:checked) {
        background: #F0F7F4;
        border: 2px solid #5D8A6F;
        box-shadow: 0 3px 15px rgba(93, 138, 111, 0.25);
        transform: none;
    }
    
    div[data-testid="stRadio"] > div > label::before,
    div[data-testid="stRadio"] > div > label::after {
        display: none;
    }
    
    div[data-testid="stRadio"] input[type="radio"] {
        display: none;
    }
    
    div[data-testid="stRadio"] > div > label > div {
        font-size: 1.05rem;
        font-weight: 600;
        color: #4A4A4A;
        margin: 0;
        text-shadow: none;
    }
    
    div[data-testid="stRadio"] > div > label:has(input:checked) > div {
        color: #2E5945;
        font-size: 1.05rem;
        animation: none;
    }
    
    /* ========== 시료 선택 전용 스타일 (sweet_input, salty_input) ========== */
    /* 시료 라벨 */
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > label,
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > label {
        font-size: 1.15rem;
        font-weight: 600;
        color: #2E5945;
        margin-bottom: 1.5rem;
    }
    
    /* 시료 컨테이너 - 연한 연두색 배경 */
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div,
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div {
        background: #E8F5E3 !important;
        padding: 2.5rem 1.5rem !important;
        border-radius: 20px !important;
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        grid-template-rows: auto auto !important;
        justify-items: center !important;
        gap: 2rem !important;
        max-width: 100% !important;
        box-shadow: 0 4px 12px rgba(93, 138, 111, 0.1) !important;
    }
    
    /* 5번째 항목을 중앙에 배치 */
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label:nth-child(5),
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label:nth-child(5) {
        grid-column: 2 / 3 !important;
    }
    
    /* 시료 선택 카드 - 실린더 디자인 */
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label,
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label {
        background: transparent !important;
        border: none !important;
        padding: 1rem !important;
        min-width: 120px !important;
        min-height: 200px !important;
        position: relative !important;
        box-shadow: none !important;
    }
    
    /* 실린더 구조 */
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label::before,
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label::before {
        content: '' !important;
        display: block !important;
        position: absolute !important;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 90px;
        height: 120px;
        background: 
            radial-gradient(ellipse at top, #E0E0E0 0%, #BDBDBD 100%) top / 100% 25px no-repeat,
            linear-gradient(90deg, #F5F5F5 0%, #EEEEEE 50%, #F5F5F5 100%) 0 12px / 100% calc(100% - 37px) no-repeat,
            radial-gradient(ellipse at bottom, #BDBDBD 0%, #9E9E9E 100%) bottom / 100% 25px no-repeat;
        border-radius: 0;
        box-shadow: 
            0 2px 5px rgba(0, 0, 0, 0.15) inset,
            0 6px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.35s ease;
    }
    
    /* 시료 호버 */
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label:hover,
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label:hover {
        transform: translateY(-8px) !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label:hover::before,
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label:hover::before {
        box-shadow: 
            0 2px 5px rgba(0, 0, 0, 0.15) inset,
            0 8px 20px rgba(0, 0, 0, 0.25);
    }
    
    /* 시료 선택됨 */
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label:has(input:checked),
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label:has(input:checked) {
        transform: translateY(-12px) scale(1.05) !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* 선택된 실린더 - 초록색 */
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label:has(input:checked)::before,
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label:has(input:checked)::before {
        background: 
            radial-gradient(ellipse at top, #A5D6A7 0%, #81C784 100%) top / 100% 25px no-repeat,
            linear-gradient(90deg, #C8E6C9 0%, #A5D6A7 50%, #C8E6C9 100%) 0 12px / 100% calc(100% - 37px) no-repeat,
            radial-gradient(ellipse at bottom, #81C784 0%, #66BB6A 100%) bottom / 100% 25px no-repeat !important;
        box-shadow: 
            0 2px 5px rgba(76, 175, 80, 0.3) inset,
            0 10px 25px rgba(76, 175, 80, 0.4) !important;
    }
    
    /* 시료 번호 */
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label > div,
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label > div {
        font-size: 3.2rem !important;
        font-weight: 800 !important;
        color: #757575 !important;
        margin-top: 130px !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1) !important;
        font-family: 'Arial Rounded MT Bold', 'Helvetica Rounded', Arial, sans-serif !important;
    }
    
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label:hover > div,
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label:hover > div {
        color: #616161 !important;
        transform: scale(1.08) !important;
    }
    
    div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label:has(input:checked) > div,
    div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label:has(input:checked) > div {
        color: #2E5945 !important;
        font-size: 3.6rem !important;
        text-shadow: 3px 3px 6px rgba(46, 89, 69, 0.2) !important;
        animation: gentlePulse 0.5s ease-in-out !important;
    }
    
    @keyframes gentlePulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #D4CFC4;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: white;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #5D8A6F;
        box-shadow: 0 0 0 3px rgba(93, 138, 111, 0.1);
    }
    
    /* 라벨 스타일 */
    .stTextInput > label,
    .stNumberInput > label {
        font-weight: 600;
        color: #2E5945;
        font-size: 1.05rem;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1.05rem;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.12);
    }
    
    /* Primary 버튼 */
    .stButton > button[kind="primary"] {
        background: #7BA088;
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #6A8F77;
    }
    
    /* Secondary 버튼 */
    .stButton > button[kind="secondary"] {
        background: #E8F5F0;
        color: #5D8A6F;
        border: 2px solid #D4CFC4;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #D5EDE5;
        border-color: #7BA088;
    }
    
    /* 섹션 헤더 */
    .section-header {
        background: #F0F7F4;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 2rem 0 1.5rem 0;
        border-left: 5px solid #5D8A6F;
        box-shadow: 0 3px 10px rgba(46, 89, 69, 0.08);
    }
    
    /* 파란색 박스 - 단맛 (차분한 블루) */
    .blue-box {
        background: #EEF5F9;
        padding: 2rem;
        border-radius: 16px;
        border-left: 6px solid #6B9AB8;
        margin: 2rem 0;
        box-shadow: 0 4px 12px rgba(107, 154, 184, 0.15);
        animation: fadeIn 0.5s ease-in;
    }
    
    /* 빨간색 박스 - 짠맛 (차분한 산호빛) */
    .red-box {
        background: #FDF6F4;
        padding: 2rem;
        border-radius: 16px;
        border-left: 6px solid #C89B8C;
        margin: 2rem 0;
        box-shadow: 0 4px 12px rgba(200, 155, 140, 0.15);
        animation: fadeIn 0.5s ease-in;
    }
    
    /* 초록색 박스 - 완료 */
    .green-box {
        background: #F0F7F4;
        padding: 2rem;
        border-radius: 12px;
        border-left: 5px solid #5D8A6F;
        margin: 1.5rem 0;
        box-shadow: 0 3px 10px rgba(93, 138, 111, 0.12);
    }
    
    /* 통계 카드 */
    .stat-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(46, 89, 69, 0.1);
        transition: transform 0.3s ease;
        border: 1px solid #E8E5DF;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 18px rgba(46, 89, 69, 0.15);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #5D8A6F;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: #6B7B6A;
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
        background: #5D8A6F;
        border-radius: 10px;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #E8F5F0 0%, #D5EDE5 100%);
    }
    
    /* 데이터프레임 스타일 */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* 선택 박스 */
    .stSelectbox > div > div {
        border-radius: 12px;
        border: 2px solid #D4CFC4;
    }
    
    /* 다운로드 버튼 */
    .stDownloadButton > button {
        background: #6B9AB8;
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
        height: 1px;
        background: #D4CFC4;
    }
    
    /* 성공 메시지 */
    .stSuccess {
        background: #F0F7F4;
        border-left: 5px solid #5D8A6F;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* 경고 메시지 */
    .stWarning {
        background: #FFF9F0;
        border-left: 5px solid #D4A574;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* 에러 메시지 */
    .stError {
        background: #FDF6F4;
        border-left: 5px solid #C89B8C;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* 정보 메시지 */
    .stInfo {
        background: #EEF5F9;
        border-left: 5px solid #6B9AB8;
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
        /* 메인 컨테이너 모바일 최적화 */
        .main {
            padding: 1rem;
        }
        
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        /* 헤더 크기 조정 */
        h1 {
            font-size: 2rem !important;
        }
        
        h2 {
            font-size: 1.5rem !important;
        }
        
        h3 {
            font-size: 1.3rem !important;
        }
        
        h4 {
            font-size: 1.1rem !important;
        }
        
        /* 텍스트 색상 명시 */
        p, span, div, label {
            color: #2E5945 !important;
        }
        
        /* 입력 필드 모바일 최적화 */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            font-size: 16px !important;
            padding: 0.75rem !important;
        }
        
        /* 버튼 크기 조정 */
        .stButton > button {
            padding: 1rem 1.5rem !important;
            font-size: 1rem !important;
            width: 100% !important;
        }
        
        /* 컬럼 모바일에서 세로 정렬 */
        .row-widget.stHorizontal {
            flex-direction: column !important;
        }
        
        /* 시료 선택 모바일 최적화 - 3열 2행 그리드 */
        div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div,
        div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div {
            display: grid !important;
            grid-template-columns: repeat(3, 1fr) !important;
            grid-template-rows: auto auto !important;
            justify-items: center !important;
            gap: 1rem !important;
            padding: 1.5rem 0.5rem !important;
        }
        
        /* 5번째 항목 모바일에서도 중앙 배치 */
        div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label:nth-child(5),
        div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label:nth-child(5) {
            grid-column: 2 / 3 !important;
            justify-self: center !important;
        }
        
        div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label,
        div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label {
            min-width: 85px !important;
            min-height: 160px !important;
        }
        
        div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label::before,
        div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label::before {
            width: 70px;
            height: 95px;
        }
        
        div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label > div,
        div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label > div {
            font-size: 2.5rem !important;
            margin-top: 105px !important;
        }
        
        div[data-testid="stRadio"]:has(input[id*="sweet_input"]) > div > label:has(input:checked) > div,
        div[data-testid="stRadio"]:has(input[id*="salty_input"]) > div > label:has(input:checked) > div {
            font-size: 2.8rem !important;
        }
        
        /* 성별 선택 모바일 최적화 */
        div[data-testid="stRadio"] > div > label {
            min-width: 120px !important;
            padding: 1rem 2rem !important;
        }
        
        /* 박스 패딩 조정 */
        .blue-box, .red-box, .green-box {
            padding: 1.5rem !important;
            margin: 1.5rem 0 !important;
        }
        
        /* 통계 카드 모바일 */
        .stat-card {
            margin-bottom: 1rem;
        }
        
        /* 사이드바 모바일 */
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
        
        /* 데이터프레임 스크롤 */
        .dataframe {
            font-size: 0.85rem !important;
        }
    }
    
    /* 추가 텍스트 색상 명시 */
    .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span {
        color: #2E5945;
    }
    
    /* 라벨 텍스트 색상 */
    label[data-testid="stWidgetLabel"] {
        color: #2E5945 !important;
    }
    
    /* 입력 필드 텍스트 */
    input, textarea, select {
        color: #2E5945 !important;
    }
    
    /* 라디오 버튼 텍스트 */
    div[data-testid="stRadio"] label {
        color: #2E5945 !important;
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
        <h1 style="font-size: 3rem; color: #2E5945; margin-bottom: 0.5rem;">
            🍽️ 평창 웰니스 클래스
        </h1>
        <p style="font-size: 1.3rem; color: #5D8A6F; font-weight: 500;">
            나의 미각탐험 ! MPTI
        </p>
        <p style="font-size: 1rem; color: #7BA088; font-style: italic;">
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
    <div style="background: #FFF9F0; 
                padding: 1.5rem; border-radius: 12px; border-left: 5px solid #D4A574; 
                margin: 1.5rem 0; box-shadow: 0 3px 10px rgba(212, 165, 116, 0.12);">
        <h4 style="color: #A67C52; margin-bottom: 1rem;">📋 테스트 안내</h4>
        <p style="font-size: 1.05rem; line-height: 1.8; color: #4A4A4A;">
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
        <p style="color: #5D8A6F; font-size: 1.1rem;">다음 질문에 응답해 주시기 바랍니다</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 성명
    name = st.text_input("👤 성명 *", value=st.session_state.responses.get('name', ''), placeholder="홍길동", key="name_input")
    
    # 성별
    st.markdown("#### ⚥ 성별 *")
    gender = st.radio("성별 선택", ["남", "여"], 
                     index=0 if st.session_state.responses.get('gender', '남') == '남' else 1,
                     horizontal=True,
                     key="gender_input")
    
    st.markdown("---")
    
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
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #EEF5F9; 
                padding: 2rem; border-radius: 16px; border-left: 6px solid #6B9AB8; 
                margin: 2rem 0; box-shadow: 0 4px 12px rgba(107, 154, 184, 0.15);">
        <h4 style="color: #4A7899; margin-bottom: 1rem;">🔵 파란 글씨 표시된 시료</h4>
        <p style="font-size: 1.05rem; line-height: 1.8; color: #4A4A4A;">
            <strong>복숭아 음료를 마신다고 생각하면서</strong>,
            시료 순서대로 <strong>(1 → 2 → 3 → 4 → 5)</strong> 맛을 보고<br>
            <strong style="color: #4A7899;">가장 높은 선호도의 시료 하나만 체크</strong>해주세요
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🧪 시료 선택")
    st.markdown("음료수를 마신다고 생각했을 때, 가장 선호하는 시료를 선택해주세요")
    
    # 현재 선택된 값
    current_value = st.session_state.responses.get('sweet_preference', None)
    
    # 1행: 시료 1, 2, 3
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧪 1", key="sweet_1", use_container_width=True, 
                    type="primary" if current_value == "1" else "secondary"):
            st.session_state.responses['sweet_preference'] = "1"
            st.rerun()
    
    with col2:
        if st.button("🧪 2", key="sweet_2", use_container_width=True,
                    type="primary" if current_value == "2" else "secondary"):
            st.session_state.responses['sweet_preference'] = "2"
            st.rerun()
    
    with col3:
        if st.button("🧪 3", key="sweet_3", use_container_width=True,
                    type="primary" if current_value == "3" else "secondary"):
            st.session_state.responses['sweet_preference'] = "3"
            st.rerun()
    
    # 2행: 시료 4, 5 (5번 중앙)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧪 4", key="sweet_4", use_container_width=True,
                    type="primary" if current_value == "4" else "secondary"):
            st.session_state.responses['sweet_preference'] = "4"
            st.rerun()
    
    with col2:
        if st.button("🧪 5", key="sweet_5", use_container_width=True,
                    type="primary" if current_value == "5" else "secondary"):
            st.session_state.responses['sweet_preference'] = "5"
            st.rerun()
    
    with col3:
        st.write("")  # 빈 공간
    
    # 선택된 시료 표시
    if current_value:
        st.success(f"✅ 시료 {current_value}번이 선택되었습니다.")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 이전", key="prev_sweet"):
            st.session_state.page = 1
            st.rerun()
    
    with col2:
        if st.button("다음 단계로 →", type="primary", key="next_sweet", use_container_width=True):
            if current_value:
                st.session_state.page = 3
                st.rerun()
            else:
                st.error("❌ 시료를 선택해주세요.")

def page_salty_preference():
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1>🥣 짠맛 선호도 조사</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #FDF6F4; 
                padding: 2rem; border-radius: 16px; border-left: 6px solid #C89B8C; 
                margin: 2rem 0; box-shadow: 0 4px 12px rgba(200, 155, 140, 0.15);">
        <h4 style="color: #A67C6D; margin-bottom: 1rem;">🔴 빨간 글씨 표시된 시료</h4>
        <p style="font-size: 1.05rem; line-height: 1.8; color: #4A4A4A;">
            <strong>콩나물국을 먹는다고 생각하면서</strong>,<br>
            시료 순서대로 <strong>(1 → 2 → 3 → 4 → 5)</strong> 맛을 보고<br>
            <strong style="color: #A67C6D;">가장 높은 선호도의 시료를 하나만 체크</strong>해주세요
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🧪 시료 선택")
    st.markdown("콩나물국을 먹는다고 생각했을 때, 가장 선호하는 시료를 선택해주세요")
    
    # 현재 선택된 값
    current_value = st.session_state.responses.get('salty_preference', None)
    
    # 1행: 시료 1, 2, 3
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧪 1", key="salty_1", use_container_width=True, 
                    type="primary" if current_value == "1" else "secondary"):
            st.session_state.responses['salty_preference'] = "1"
            st.rerun()
    
    with col2:
        if st.button("🧪 2", key="salty_2", use_container_width=True,
                    type="primary" if current_value == "2" else "secondary"):
            st.session_state.responses['salty_preference'] = "2"
            st.rerun()
    
    with col3:
        if st.button("🧪 3", key="salty_3", use_container_width=True,
                    type="primary" if current_value == "3" else "secondary"):
            st.session_state.responses['salty_preference'] = "3"
            st.rerun()
    
    # 2행: 시료 4, 5 (5번 중앙)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧪 4", key="salty_4", use_container_width=True,
                    type="primary" if current_value == "4" else "secondary"):
            st.session_state.responses['salty_preference'] = "4"
            st.rerun()
    
    with col2:
        if st.button("🧪 5", key="salty_5", use_container_width=True,
                    type="primary" if current_value == "5" else "secondary"):
            st.session_state.responses['salty_preference'] = "5"
            st.rerun()
    
    with col3:
        st.write("")  # 빈 공간
    
    # 선택된 시료 표시
    if current_value:
        st.success(f"✅ 시료 {current_value}번이 선택되었습니다.")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 이전", key="prev_salty"):
            st.session_state.page = 2
            st.rerun()
    
    with col2:
        if st.button("✅ 제출하기", type="primary", key="submit", use_container_width=True):
            if current_value:
                st.session_state.page = 4
                st.rerun()
            else:
                st.error("❌ 시료를 선택해주세요.")

def page_complete():
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 3rem;">✅ 테스트 완료!</h1>
        <p style="color: #5D8A6F; font-size: 1.3rem; margin-top: 1rem;">소중한 시간 내어 참여해주셔서 감사합니다 🙏</p>
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
    <div style="background: #F0F7F4; 
                padding: 2rem; border-radius: 12px; border-left: 5px solid #5D8A6F; 
                margin: 1.5rem 0; box-shadow: 0 3px 10px rgba(93, 138, 111, 0.12);">
        <h3 style="color: #2E5945;">🎉 감사합니다!</h3>
        <p style="font-size: 1.05rem; line-height: 1.8; color: #4A4A4A;">
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
            <div style="text-align: center; padding: 1.5rem; background: #EEF5F9; border-radius: 12px; flex: 1; margin: 0 1rem; border: 1px solid #D1E3EC;">
                <div style="font-size: 2.5rem;">🍑</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #4A7899; margin: 0.5rem 0;">시료 {st.session_state.responses.get('sweet_preference', '-')}</div>
                <div style="color: #6B9AB8;">단맛 선호</div>
            </div>
            <div style="text-align: center; padding: 1.5rem; background: #FDF6F4; border-radius: 12px; flex: 1; margin: 0 1rem; border: 1px solid #E8D5CF;">
                <div style="font-size: 2.5rem;">🥣</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #A67C6D; margin: 0.5rem 0;">시료 {st.session_state.responses.get('salty_preference', '-')}</div>
                <div style="color: #C89B8C;">짠맛 선호</div>
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
    <div style="background: #5D8A6F; color: white; padding: 2rem; border-radius: 16px; text-align: center; margin-bottom: 2rem; box-shadow: 0 6px 20px rgba(46, 89, 69, 0.2);">
        <h1 style="color: white;">🔧 관리자 대시보드</h1>
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
                <div style="background: #F0F7F4; 
                            padding: 2rem; border-radius: 12px; border-left: 5px solid #5D8A6F; 
                            margin: 1.5rem 0; box-shadow: 0 3px 10px rgba(93, 138, 111, 0.12);">
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
            <h2 style="color: #2E5945;">🌿 평창 웰니스</h2>
            <p style="color: #5D8A6F;">미각 MPTI</p>
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
        <div style="font-size: 0.85rem; color: #6B7B6A; padding: 1rem 0;">
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
