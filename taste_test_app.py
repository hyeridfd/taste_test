import streamlit as st
import pandas as pd
from datetime import datetime
import json

# 페이지 설정
st.set_page_config(
    page_title="평창 웰니스 클래스 - SNU 미각테스트",
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
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'page' not in st.session_state:
    st.session_state.page = 0
if 'responses' not in st.session_state:
    st.session_state.responses = {}

# 설문 데이터 구조
taste_types = {
    "단맛": {
        "context": "음료수를 마신다고 생각하면서",
        "samples": ["126", "358", "741", "937", "512"],
        "intensity_options": ["전혀 달지않다", "달지않다", "보통이다", "달다", "매우 달다"]
    },
    "짠맛": {
        "context": "콩나물국을 먹는다고 생각하면서",
        "samples": ["476", "375", "543", "741", "268"],
        "intensity_options": ["전혀 짜지않다", "짜지않다", "보통이다", "짜다", "매우 짜다"]
    },
    "신맛": {
        "context": "레몬주스를 먹는다고 생각하면서",
        "samples": ["596", "197", "387", "421", "265"],
        "intensity_options": ["전혀 시지않다", "시지않다", "보통이다", "시다", "매우 시다"]
    },
    "매운맛": {
        "context": "라면국물을 먹는다고 생각하면서",
        "samples": ["284", "563", "486", "347", "167"],
        "intensity_options": ["전혀 맵지않다", "맵지않다", "보통이다", "맵다", "매우 맵다"]
    }
}

preference_options = ["싫다", "약간 싫다", "보통이다", "약간 좋다", "좋다"]

def page_intro():
    st.title("🍽️ [평창 웰니스 클래스] SNU 미각테스트")
    
    st.markdown("""
    ### 안녕하세요.
    
    '평창 웰니스 클래스'에서 미각테스트를 기획한 서울대학교 정밀식의학연구실입니다.
    
    먼저 귀중한 시간을 내어 테스트에 참여해주셔서 진심으로 감사드립니다.
    
    본 테스트는 **단맛, 짠맛, 신맛, 매운맛**의 민감도와 선호도를 측정하기 위해 설계되었습니다.
    
    #### 📋 테스트 안내
    - **소요 시간**: 약 15~20분
    - **진행 방법**: 시료를 3초간 입에 담고 뱉은 후 맛의 강도와 선호도를 솔직하게 응답
    
    #### ⚠️ 주의사항
    - **가장 높은 선호도의 시료는 하나만** 체크해주세요
    - **'보통이다' 이상의 선호도에 최소한 한 곳 이상** 체크해주세요
    
    본 테스트와 관련하여 궁금하신 점이나 문의사항이 있으시면, 아래에 제시된 연구자의 이메일로 문의해 주십시오.
    
    **※ 완성된 설문지를 제출하시는 것으로 귀하의 연구 참여에 대한 동의 의사가 확인된 것으로 간주됨을 알려드립니다.**
    
    ---
    
    **연구자**:
    - 황희정 (hhj2831@snu.ac.kr)
    - 유정연 (98you21@snu.ac.kr)
    - 류혜리 (fwm825@snu.ac.kr)
    """)
    
    st.markdown("---")
    
    # 이메일 입력
    email = st.text_input("📧 이메일 주소 *", placeholder="example@email.com")
    
    if st.button("테스트 시작하기", type="primary"):
        if email and "@" in email:
            st.session_state.responses['email'] = email
            st.session_state.page = 1
            st.rerun()
        else:
            st.error("유효한 이메일 주소를 입력해주세요.")

def page_basic_info():
    st.title("📝 기본 정보")
    st.markdown("### 성명, 성별, 나이를 입력해주세요")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        name = st.text_input("성명 *", value=st.session_state.responses.get('name', ''))
    
    with col2:
        gender = st.radio("성별 *", ["남", "여"], 
                         index=0 if st.session_state.responses.get('gender', '남') == '남' else 1)
    
    with col3:
        age = st.number_input("나이 *", min_value=1, max_value=120, 
                             value=st.session_state.responses.get('age', 30))
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 이전"):
            st.session_state.page = 0
            st.rerun()
    
    with col2:
        if st.button("다음 →", type="primary"):
            if name:
                st.session_state.responses['name'] = name
                st.session_state.responses['gender'] = gender
                st.session_state.responses['age'] = age
                st.session_state.page = 2
                st.rerun()
            else:
                st.error("모든 필수 항목을 입력해주세요.")

def page_taste_test(taste_name, page_num):
    taste_data = taste_types[taste_name]
    
    st.title(f"{taste_name} 정도 및 선호도 조사")
    
    st.markdown(f"""
    <div class="instruction-box">
    <strong>✅ 테스트 방법</strong><br>
    • <strong>{taste_data['context']}</strong>, 시료 순서대로 맛을 보고 각 시료의 {taste_name} 정도와 선호하는 정도에 따라 각각 체크해주세요<br>
    • <strong>가장 높은 선호도의 시료를 하나만 체크해주세요</strong><br>
    • <strong>'보통이다' 이상의 선호도에 최소한 한 곳 이상 체크해주세요</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # 각 시료에 대한 평가
    all_filled = True
    for i, sample in enumerate(taste_data['samples'], 1):
        st.markdown(f"""
        <div class="section-header">
        <h3>시료 {i}: &lt;{sample}&gt;</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            intensity_key = f"{taste_name}_{sample}_강도"
            intensity = st.radio(
                f"**{i}-1. <{sample}> {taste_name} 강도 ***",
                taste_data['intensity_options'],
                key=intensity_key,
                index=None if intensity_key not in st.session_state.responses else taste_data['intensity_options'].index(st.session_state.responses[intensity_key])
            )
            if intensity:
                st.session_state.responses[intensity_key] = intensity
            else:
                all_filled = False
        
        with col2:
            preference_key = f"{taste_name}_{sample}_선호도"
            preference = st.radio(
                f"**{i}-2. <{sample}> {taste_name} 선호도 ***",
                preference_options,
                key=preference_key,
                index=None if preference_key not in st.session_state.responses else preference_options.index(st.session_state.responses[preference_key])
            )
            if preference:
                st.session_state.responses[preference_key] = preference
            else:
                all_filled = False
        
        st.markdown("---")
    
    # 네비게이션 버튼
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 이전", key=f"prev_{page_num}"):
            st.session_state.page = page_num - 1
            st.rerun()
    
    with col2:
        if st.button("다음 →", type="primary", key=f"next_{page_num}"):
            if all_filled:
                st.session_state.page = page_num + 1
                st.rerun()
            else:
                st.error("모든 필수 항목을 선택해주세요.")

def page_complete():
    st.title("✅ 테스트 완료")
    
    st.success("**테스트에 응해주셔서 감사합니다!**")
    
    st.markdown("""
    귀하의 소중한 응답이 성공적으로 제출되었습니다.
    
    본 연구에 참여해 주셔서 진심으로 감사드립니다.
    """)
    
    # 응답 데이터 저장
    if st.button("응답 데이터 다운로드 (JSON)", type="primary"):
        response_data = {
            "제출시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **st.session_state.responses
        }
        
        json_str = json.dumps(response_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="JSON 파일 다운로드",
            data=json_str,
            file_name=f"미각테스트_{st.session_state.responses.get('name', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    if st.button("처음으로 돌아가기"):
        st.session_state.page = 0
        st.session_state.responses = {}
        st.rerun()

# 메인 로직
def main():
    if st.session_state.page == 0:
        page_intro()
    elif st.session_state.page == 1:
        page_basic_info()
    elif st.session_state.page == 2:
        page_taste_test("단맛", 2)
    elif st.session_state.page == 3:
        page_taste_test("짠맛", 3)
    elif st.session_state.page == 4:
        page_taste_test("신맛", 4)
    elif st.session_state.page == 5:
        page_taste_test("매운맛", 5)
    elif st.session_state.page == 6:
        page_complete()
    
    # 진행률 표시
    if st.session_state.page > 0 and st.session_state.page < 6:
        progress = st.session_state.page / 6
        st.sidebar.progress(progress)
        st.sidebar.markdown(f"**진행률**: {int(progress * 100)}%")
        st.sidebar.markdown(f"**현재 페이지**: {st.session_state.page}/6")

if __name__ == "__main__":
    main()
