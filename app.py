import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import matplotlib.font_manager as fm
import platform
from collections import Counter
import re

# 1. 페이지 기본 설정
st.set_page_config(page_title="캠퍼스 생활 설문조사 분석", layout="wide")

# 2. 운영체제별 한글 폰트 설정 (나눔고딕 적용)
if platform.system() == 'Windows':
    font_path = 'c:/Windows/Fonts/malgun.ttf'
elif platform.system() == 'Darwin':
    font_path = '/Library/Fonts/AppleGothic.ttf'
else:
    # 리눅스 환경 및 Colab/Streamlit Cloud 등에서 NanumGothic.ttf 사용
    font_path = 'NanumGothic.ttf'

try:
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
except:
    pass

plt.rcParams['axes.unicode_minus'] = False  # 마이너스 부호 깨짐 방지

# 3. 화면 상단 타이틀
st.title("🎓 캠퍼스 생활 설문조사 분석 프로그램")
st.write("파이썬 입문 수업 조교와 함께하는 캠퍼스 라이프 데이터 분석 웹앱입니다.")
st.markdown("---")

# 4. CSV 파일 업로드
st.subheader("📁 1. 설문조사 CSV 파일 업로드")
uploaded_file = st.file_uploader("캠퍼스 생활 설문조사 CSV 파일을 업로드해주세요.", type=["csv"])

if uploaded_file is not None:
    # 파일 읽기
    raw_df = pd.read_csv(uploaded_file)

    # 5. 데이터 미리보기
    st.subheader("👀 2. 업로드된 데이터 미리보기")
    st.dataframe(raw_df.head())

    # 6. 잘못된 데이터 처리 및 전처리
    initial_rows = len(raw_df)

    df = raw_df.copy()
    df['만족도'] = pd.to_numeric(df['만족도'], errors='coerce')
    df['공부시간'] = pd.to_numeric(df['공부시간'], errors='coerce')

    target_cols = ['학과', '공부시간', '스마트폰', '수면시간', '만족도']
    clean_df = df.dropna(subset=target_cols)

    excluded_count = initial_rows - len(clean_df)

    st.subheader("🧹 3. 데이터 전처리 결과")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="정상 분석 데이터 건수", value=f"{len(clean_df)} 건")
    with col2:
        st.metric(label="이상치 및 결측으로 제외된 건수", value=f"{excluded_count} 건")

    st.markdown("---")

    # 7. 학과 선택 필터
    st.subheader("🔍 4. 학과별 분석 및 시각화")
    departments = ['전체'] + sorted(clean_df['학과'].unique().tolist())
    selected_dept = st.selectbox("분석할 학과를 선택하세요:", departments)

    # 선택한 학과에 따른 데이터 필터링
    if selected_dept == '전체':
        plot_df = clean_df
        st.info("현재 **전체 학과** 데이터가 표시됩니다.")
    else:
        plot_df = clean_df[clean_df['학과'] == selected_dept]
        st.info(f"현재 **{selected_dept}** 데이터가 표시됩니다.")

    # 선택된 학과의 평균 만족도 계산
    if not plot_df.empty:
        avg_satisfaction = plot_df['만족도'].mean()
        st.metric(label=f"[{selected_dept}] 평균 학교생활 만족도", value=f"{avg_satisfaction:.2f} 점 / 10점 만점")

    st.markdown("---")

    # 8. 그래프 및 시각화 (막대그래프, 산점도, 워드클라우드, 의견 단어 빈도 및 긍/부정 분석)
    st.subheader("📊 5. 생활 습관 및 의견 텍스트 분석 시각화")

    # 탭으로 시각화 구분
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "생활습관 비교",
        "공부시간 vs 만족도",
        "워드클라우드",
        "단어 빈도수 TOP 10",
        "긍정/부정 단어 분석"
    ])

    with tab1:
        st.markdown("#### 학과별 주요 생활 습관 시간 비교")
        habit_mean = clean_df.groupby('학과')[['공부시간', '스마트폰', '수면시간']].mean().reset_index()

        fig, ax = plt.subplots(figsize=(10, 5))
        habit_mean.set_index('학과').plot(kind='bar', ax=ax, colormap='Set2')
        ax.set_title(f"학과별 평균 생활 습관 시간 비교 ({selected_dept})", fontsize=14, fontweight='bold')
        ax.set_xlabel("학과 명", fontsize=12)
        ax.set_ylabel("시간 (시간/일)", fontsize=12)
        plt.xticks(rotation=45)
        ax.legend(["공부시간", "스마트폰 사용시간", "수면시간"])
        st.pyplot(fig)

    with tab2:
        st.markdown("#### 일일 공부시간과 학교생활 만족도의 관계")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.scatterplot(data=plot_df, x='공부시간', y='만족도', hue='학과', s=100, palette='deep', ax=ax)
        ax.set_title("공부시간과 만족도의 상관관계", fontsize=14, fontweight='bold')
        ax.set_xlabel("일일 공부 시간 (시간)", fontsize=12)
        ax.set_ylabel("학교생활 만족도 (점)", fontsize=12)
        st.pyplot(fig)

    with tab3:
        st.markdown("#### 학생들이 작성한 한 줄 의견 워드클라우드")
        text_data = " ".join(plot_df['한줄의견'].dropna().astype(str).tolist())

        if text_data.strip():
            wc = WordCloud(
                font_path=font_path,
                background_color='white',
                width=800,
                height=400,
                max_words=50
            ).generate(text_data)

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            ax.set_title(f"주요 키워드 워드클라우드 ({selected_dept})", fontsize=14, fontweight='bold')
            st.pyplot(fig)
        else:
            st.warning("표시할 텍스트 의견이 없습니다.")

    with tab4:
        st.markdown("#### 한 줄 의견에서 자주 등장하는 단어 상위 10개")
        text_data_all = " ".join(plot_df['한줄의견'].dropna().astype(str).tolist())
        words = [w for w in re.findall(r'[가-힣]{2,}', text_data_all)]  # 2글자 이상 한글 단어 추출
        word_counts = Counter(words).most_common(10)

        if word_counts:
            w_df = pd.DataFrame(word_counts, columns=['단어', '빈도수'])

            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(w_df['단어'], w_df['빈도수'], color='skyblue')
            ax.set_title(f"자주 등장하는 단어 TOP 10 ({selected_dept})", fontsize=14, fontweight='bold')
            ax.set_xlabel("단어", fontsize=12)
            ax.set_ylabel("빈도수 (회)", fontsize=12)
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.warning("분석할 텍스트 데이터가 부족합니다.")

    with tab5:
        st.markdown("#### 긍정 단어 vs 부정 단어 등장 횟수 비교")
        text_data_all = " ".join(plot_df['한줄의견'].dropna().astype(str).tolist())

        # 대표적인 긍정/부정 키워드 정의
        pos_keywords = ['좋아요', '맛있어요', '재미있어요', '도움이', '예뻐서', '친절해요']
        neg_keywords = ['부족해요', '피곤해요', '불편해요', '힘들어요', '후회돼요', '아쉬워요', '비싸서', '붐벼서']

        pos_score = sum(text_data_all.count(kw) for kw in pos_keywords)
        neg_score = sum(text_data_all.count(kw) for kw in neg_keywords)

        sentiment_df = pd.DataFrame({
            '감성분류': ['긍정 단어', '부정 단어'],
            '등장횟수': [pos_score, neg_score]
        })

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(sentiment_df['감성분류'], sentiment_df['등장횟수'], color=['#66b3ff', '#ff9999'])
        ax.set_title(f"의견 감성 키워드 등장 횟수 ({selected_dept})", fontsize=14, fontweight='bold')
        ax.set_xlabel("감성 구분", fontsize=12)
        ax.set_ylabel("등장 횟수 (회)", fontsize=12)
        st.pyplot(fig)

else:
    st.warning("👈 상단의 파일 업로더를 통해 'campus_life.csv' 파일을 업로드해주세요.")