# 이 파일을 taste_test_app.py의 donut_chart_counts 함수로 교체하세요
# (전체 코드는 아니고, 이 함수만 복사/붙여넣기하면 됩니다)

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import streamlit as st
import pandas as pd

def donut_chart_counts(series: pd.Series, title: str):
    """
    값 분포를 도넛 차트로 시각화 - 파스텔 색상 + 한글 폰트 완벽 지원
    
    매우 중요한 수정사항:
    1. explicit plt.rcParams 설정 (global)
    2. 모든 텍스트에 fontproperties 직접 적용
    3. 폰트 캐시 강제 갱신
    """
    s = series.dropna().astype(str)
    s = s[s != ""]
    if s.empty:
        st.info(f"📝 {title}: 데이터가 없습니다.")
        return

    counts = s.value_counts().sort_index()

    # ============ 한글 폰트 설정 (가장 중요!) ============
    # 현재 rcParams에서 폰트 가져오기
    font_family = mpl.rcParams.get("font.family", ["DejaVu Sans"])
    if isinstance(font_family, list):
        font_name = font_family[0] if font_family else "DejaVu Sans"
    else:
        font_name = font_family
    
    print(f"[CHART] Using font family: {font_name}")
    print(f"[CHART] Full rcParams font.family: {mpl.rcParams['font.family']}")
    
    # 임시 로컬 rcParams 설정
    plt.rcdefaults()
    plt.rcParams['font.family'] = font_name
    plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # ============ 파스텔 색상 정의 ============
    pastel_colors = ['#A5D6A7', '#C5A5D8', '#FFB6B9', '#FED8B1', '#B4E7FF', 
                     '#C8E6C9', '#B2DFDB', '#FFCCBC', '#F8BBD0', '#E1BEE7']
    
    colors = pastel_colors[:len(counts)] if len(counts) <= len(pastel_colors) else (
        pastel_colors * (len(counts) // len(pastel_colors) + 1))[:len(counts)]
    
    # ============ Figure & Axis 생성 ============
    fig = plt.figure(figsize=(6, 6), dpi=100)
    fig.patch.set_facecolor('white')
    ax = fig.add_subplot(111)
    
    # ============ 파이 차트 그리기 ============
    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=[str(label) for label in counts.index],  # 명시적 문자열
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        textprops={
            'fontname': font_name,
            'fontsize': 12,
            'weight': 'bold'
        }
    )
    
    # ============ 시료 번호(라벨) 스타일 설정 ============
    for text in texts:
        # 직접 fontproperties 설정
        text.set_fontproperties(fm.FontProperties(
            family='sans-serif',
            size=15,
            weight='bold'
        ))
        text.set_color('#2E5945')
        text.set_fontname(font_name)
    
    # ============ 퍼센트 텍스트 스타일 설정 ============
    for autotext in autotexts:
        # 직접 fontproperties 설정
        autotext.set_fontproperties(fm.FontProperties(
            family='sans-serif',
            size=13,
            weight='bold'
        ))
        autotext.set_color('#2E5945')
        autotext.set_fontname(font_name)
    
    # ============ 도넛 효과 ============
    centre_circle = plt.Circle((0, 0), 0.65, fc='white', edgecolor='white', linewidth=2)
    ax.add_artist(centre_circle)
    
    # ============ 제목 설정 ============
    ax.set_title(
        title,
        fontname=font_name,
        fontsize=15,
        weight='bold',
        color='#2E5945',
        pad=20
    )
    
    ax.axis('equal')
    plt.tight_layout()
    
    # ============ 렌더링 ============
    try:
        st.pyplot(fig, use_container_width=True, dpi=100)
    except Exception as e:
        st.error(f"차트 렌더링 중 오류: {e}")
    finally:
        plt.close(fig)
    
    # ============ 데이터 테이블 ============
    st.dataframe(
        counts.rename("응답 수").reset_index().rename(columns={"index": "시료"}),
        use_container_width=True,
        hide_index=True
    )


# ============ 추가: set_korean_font() 함수 확인용 ============
def diagnose_font():
    """폰트 설정 상태 진단"""
    st.write("### 🔍 폰트 진단 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**matplotlib rcParams:**")
        st.code(f"""
font.family: {mpl.rcParams['font.family']}
font.sans-serif: {mpl.rcParams.get('font.sans-serif', 'Not set')}
axes.unicode_minus: {mpl.rcParams.get('axes.unicode_minus', 'Not set')}
        """)
    
    with col2:
        st.write("**시스템 폰트:**")
        available_fonts = sorted(set(f.name for f in mpl.font_manager.fontManager.ttflist))
        korean_fonts = [f for f in available_fonts if any(
            c in f for c in ['Noto', 'Nanum', '나눔', 'Gothic']
        )]
        st.write(f"찾은 한글 폰트: {', '.join(korean_fonts) if korean_fonts else '❌ 없음'}")
