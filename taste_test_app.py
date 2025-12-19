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

# CSS 스타일링
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stRadio > label {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f1f1f;
    }
    .section-header {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1.5rem 0;
    }
    .instruction-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .blue-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    .red-box {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
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
    st.title("🍽️ 맛 선호도 평가를 통한 나의 미각 MPTI 확인하기")
    
    st.markdown("""
    ### 안녕하세요.
    
    '평창 웰니스 클래스'에서 '미각 MPTI(맛 선호도 평가를 통한 나의 미각 MPTI 확인하기)' 프로그램을 기획한 서울대학교 정밀식의학연구실입니다.
    
    먼저 귀중한 시간을 내어 테스트에 참여해주셔서 진심으로 감사드립니다.
    
    본 테스트는 **단맛, 짠맛의 선호도**를 측정하기 위해 설계되었습니다.
    
    #### 📋 테스트 안내
    - **소요 시간**: 약 15~20분
    - **진행 방법**: 시료를 3초간 입에 담고 뱉은 후 가장 높은 선호도의 시료를 하나만 체크
    
    본 테스트와 관련하여 궁금하신 점이나 문의사항이 있으시면, 아래에 제시된 연구자의 이메일로 문의해 주십시오.
    
    **※ 완성된 설문지를 제출하시는 것으로 귀하의 연구 참여에 대한 동의 의사가 확인된 것으로 간주됨을 알려드립니다.**
    
    감사합니다.
    
    ---
    
    **연구자**:
    - 류혜리 (fwm825@snu.ac.kr)
    - 유정연 (98you21@snu.ac.kr)
    """)
    
    st.markdown("---")
    
    # 이메일 입력
    email = st.text_input("📧 이메일 주소 *", placeholder="example@email.com")
    
    if st.button("테스트 시작하기", type="primary", use_container_width=True):
        if email and "@" in email:
            st.session_state.responses['email'] = email
            st.session_state.page = 1
            st.rerun()
        else:
            st.error("유효한 이메일 주소를 입력해주세요.")

def page_basic_info():
    st.title("📝 기본 정보")
    st.markdown("### 다음 질문에 응답해 주시기 바랍니다.")
    
    # 성명
    name = st.text_input("성명 *", value=st.session_state.responses.get('name', ''))
    
    # 성별
    gender = st.radio("성별 *", ["남", "여"], 
                     index=0 if st.session_state.responses.get('gender', '남') == '남' else 1,
                     horizontal=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 나이
        age = st.number_input("나이 (숫자만 입력) *", min_value=1, max_value=120, 
                             value=st.session_state.responses.get('age', 30))
    
    with col2:
        # 신장
        height = st.number_input("신장 cm (숫자만 입력) *", min_value=50, max_value=250, 
                                value=st.session_state.responses.get('height', 170))
    
    with col3:
        # 체중
        weight = st.number_input("체중 kg (숫자만 입력) *", min_value=20, max_value=300, 
                                value=st.session_state.responses.get('weight', 70))
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 이전"):
            st.session_state.page = 0
            st.rerun()
    
    with col2:
        if st.button("다음 →", type="primary", use_container_width=True):
            if name:
                st.session_state.responses['name'] = name
                st.session_state.responses['gender'] = gender
                st.session_state.responses['age'] = age
                st.session_state.responses['height'] = height
                st.session_state.responses['weight'] = weight
                st.session_state.page = 2
                st.rerun()
            else:
                st.error("모든 필수 항목을 입력해주세요.")

def page_sweet_preference():
    st.title("🍑 단맛 선호도 조사")
    
    st.markdown("""
    <div class="blue-box">
    <strong>🔵 파란 글씨 표시된 시료</strong><br>
    <strong>• 복숭아음료를 마신다고 생각하면서</strong>, 시료 순서대로(1~5) 맛을 보고 <strong>가장 높은 선호도의 시료를 하나만 체크해주세요</strong>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    sweet_preference = st.radio(
        "**음료수를 마신다고 생각했을 때, 가장 선호하는 시료를 선택해주세요 ***",
        options=["1", "2", "3", "4", "5"],
        index=None if 'sweet_preference' not in st.session_state.responses else ["1", "2", "3", "4", "5"].index(st.session_state.responses['sweet_preference']),
        horizontal=True
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 이전", key="prev_sweet"):
            st.session_state.page = 1
            st.rerun()
    
    with col2:
        if st.button("다음 →", type="primary", key="next_sweet", use_container_width=True):
            if sweet_preference:
                st.session_state.responses['sweet_preference'] = sweet_preference
                st.session_state.page = 3
                st.rerun()
            else:
                st.error("시료를 선택해주세요.")

def page_salty_preference():
    st.title("🥣 짠맛 선호도 조사")
    
    st.markdown("""
    <div class="red-box">
    <strong>🔴 빨간 글씨 표시된 시료</strong><br>
    <strong>• 콩나물국을 먹는다고 생각하면서</strong>, 시료 순서대로(1~5) 맛을 보고 <strong>가장 높은 선호도의 시료를 하나만 체크해주세요</strong>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    salty_preference = st.radio(
        "**콩나물국을 먹는다고 생각했을 때, 가장 선호하는 시료를 선택해주세요 ***",
        options=["1", "2", "3", "4", "5"],
        index=None if 'salty_preference' not in st.session_state.responses else ["1", "2", "3", "4", "5"].index(st.session_state.responses['salty_preference']),
        horizontal=True
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 이전", key="prev_salty"):
            st.session_state.page = 2
            st.rerun()
    
    with col2:
        if st.button("제출하기", type="primary", key="submit", use_container_width=True):
            if salty_preference:
                st.session_state.responses['salty_preference'] = salty_preference
                st.session_state.page = 4
                st.rerun()
            else:
                st.error("시료를 선택해주세요.")

def page_complete():
    st.title("✅ 테스트 완료")
    
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
    
    st.success("**테스트에 응해주셔서 감사합니다!**")
    
    st.markdown("""
    귀하의 소중한 응답이 성공적으로 제출되었습니다.
    
    본 연구에 참여해 주셔서 진심으로 감사드립니다.
    """)
    
    # 제출 정보 표시
    if st.session_state.get('saved_to_db', False):
        # BMI 계산
        height_m = st.session_state.responses.get('height', 170) / 100
        weight_kg = st.session_state.responses.get('weight', 70)
        bmi = weight_kg / (height_m ** 2)
        
        st.markdown(f"""
        <div style="background: #e8f5e8; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
            <h4>📋 제출 완료 요약</h4>
            <p><strong>👤 이름:</strong> {st.session_state.responses.get('name', '-')}</p>
            <p><strong>📧 이메일:</strong> {st.session_state.responses.get('email', '-')}</p>
            <p><strong>🎂 나이:</strong> {st.session_state.responses.get('age', '-')}세</p>
            <p><strong>⚥ 성별:</strong> {st.session_state.responses.get('gender', '-')}</p>
            <p><strong>📏 신장:</strong> {st.session_state.responses.get('height', '-')}cm</p>
            <p><strong>⚖️ 체중:</strong> {st.session_state.responses.get('weight', '-')}kg</p>
            <p><strong>📊 BMI:</strong> {bmi:.1f}</p>
            <p><strong>🍑 단맛 선호:</strong> 시료 {st.session_state.responses.get('sweet_preference', '-')}</p>
            <p><strong>🥣 짠맛 선호:</strong> 시료 {st.session_state.responses.get('salty_preference', '-')}</p>
            <p><strong>📅 제출 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>💾 저장 상태:</strong> ✅ 데이터베이스 저장 완료</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 응답 데이터 다운로드
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 응답 데이터 다운로드 (JSON)", type="primary", use_container_width=True):
            response_data = {
                "제출시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                **st.session_state.responses
            }
            
            json_str = json.dumps(response_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="💾 JSON 파일 다운로드",
                data=json_str,
                file_name=f"미각MPTI_{st.session_state.responses.get('name', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
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
    st.title("🔐 관리자 로그인")
    
    password = st.text_input("비밀번호를 입력하세요", type="password")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("로그인", type="primary", use_container_width=True):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 올바르지 않습니다.")
    
    with col2:
        if st.button("취소", use_container_width=True):
            st.session_state.admin_mode = False
            st.rerun()

def admin_page():
    """관리자 페이지"""
    st.title("🔧 관리자 페이지")
    
    # 로그아웃 버튼
    if st.button("🚪 로그아웃", use_container_width=False):
        st.session_state.admin_authenticated = False
        st.rerun()
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea, #764ba2); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;">
        <h2>미각 MPTI 응답 관리</h2>
        <p>제출된 모든 응답을 확인하고 관리할 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    sb = get_supabase()
    df_db = fetch_taste_responses_df() if sb else pd.DataFrame()
    
    if not df_db.empty:
        # 통계 카드
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: 700; color: #667eea;">{len(df_db)}</div>
                <div style="color: #7f8c8d; font-size: 0.9rem; margin-top: 0.5rem;">총 응답 수</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            unique_users = df_db['이메일'].nunique() if '이메일' in df_db.columns else 0
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: 700; color: #667eea;">{unique_users}</div>
                <div style="color: #7f8c8d; font-size: 0.9rem; margin-top: 0.5rem;">참여자 수</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_age = int(df_db['나이'].mean()) if '나이' in df_db.columns else 0
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: 700; color: #667eea;">{avg_age}세</div>
                <div style="color: #7f8c8d; font-size: 0.9rem; margin-top: 0.5rem;">평균 나이</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            today_str = datetime.now().strftime('%Y-%m-%d')
            today_count = df_db["제출시간"].astype(str).str.contains(today_str).sum() if "제출시간" in df_db.columns else 0
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: 700; color: #667eea;">{today_count}</div>
                <div style="color: #7f8c8d; font-size: 0.9rem; margin-top: 0.5rem;">오늘 응답</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 응답 목록
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 2rem;">
            <h3>📊 응답 기록</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 표시할 컬럼 선택
        display_cols = ["성명", "이메일", "성별", "나이", "신장", "체중", "단맛선호", "짠맛선호", "제출시간"]
        available_cols = [col for col in display_cols if col in df_db.columns]
        
        st.dataframe(df_db[available_cols], use_container_width=True, height=400)
        
        # CSV 다운로드
        st.markdown("<br>", unsafe_allow_html=True)
        csv = df_db.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 전체 데이터 CSV 다운로드",
            data=csv,
            file_name=f"미각MPTI_전체응답_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # 개별 응답 상세보기
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 1rem;">
            <h3>🔍 개별 응답 상세보기</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if '성명' in df_db.columns and '이메일' in df_db.columns:
            selected_option = st.selectbox(
                "참여자 선택",
                options=df_db.apply(lambda x: f"{x['성명']} ({x['이메일']})", axis=1).tolist()
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
                
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                    <p><strong>👤 성명:</strong> {selected_row.get('성명', '-')}</p>
                    <p><strong>📧 이메일:</strong> {selected_row.get('이메일', '-')}</p>
                    <p><strong>⚥ 성별:</strong> {selected_row.get('성별', '-')}</p>
                    <p><strong>🎂 나이:</strong> {selected_row.get('나이', '-')}세</p>
                    <p><strong>📏 신장:</strong> {selected_row.get('신장', '-')}cm</p>
                    <p><strong>⚖️ 체중:</strong> {selected_row.get('체중', '-')}kg</p>
                    <p><strong>📊 BMI:</strong> {bmi:.1f}</p>
                    <p><strong>🍑 단맛 선호:</strong> 시료 {selected_row.get('단맛선호', '-')}</p>
                    <p><strong>🥣 짠맛 선호:</strong> 시료 {selected_row.get('짠맛선호', '-')}</p>
                    <p><strong>📅 제출시간:</strong> {selected_row.get('제출시간', '-')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 상세 응답 데이터 표시
                if '응답데이터' in selected_row and selected_row['응답데이터']:
                    try:
                        response_detail = json.loads(selected_row['응답데이터'])
                        st.markdown("### 📝 상세 응답 데이터")
                        st.json(response_detail)
                    except:
                        st.warning("응답 데이터를 불러올 수 없습니다.")
    
    else:
        st.info("📝 아직 제출된 응답이 없습니다.")

# 메인 로직
def main():
    # 사이드바 - 관리자 모드 토글
    with st.sidebar:
        st.markdown("---")
        admin_mode = st.checkbox("🔧 관리자 모드", value=st.session_state.get('admin_mode', False), key='admin_mode')
    
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
    
    # 진행률 표시
    if st.session_state.page > 0 and st.session_state.page < 4:
        progress = st.session_state.page / 4
        st.sidebar.progress(progress)
        st.sidebar.markdown(f"**진행률**: {int(progress * 100)}%")
        st.sidebar.markdown(f"**현재 페이지**: {st.session_state.page}/4")

if __name__ == "__main__":
    main()
