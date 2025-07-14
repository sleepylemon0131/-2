import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. 데이터 로드 함수 ---
# GitHub에 adult.csv 파일이 app.py와 같은 경로에 있다고 가정합니다.
# 만약 다른 경로에 있다면 'adult.csv' 대신 정확한 상대 경로를 입력해주세요.
@st.cache_data
def load_data():
    try:
        # 노트북에서 사용된 데이터 파일 경로를 기준으로 가정
        # 실제 Streamlit Cloud 배포 시에는 app.py와 같은 디렉토리에 adult.csv를 두는 것이 가장 간단합니다.
        df = pd.read_csv("adult.csv") # 또는 "../input/adult-census-income/adult.csv"
        
        # '?' 값을 NaN으로 처리 (노트북에서 null_name='?' 처리하는 부분 참조)
        df.replace('?', pd.NA, inplace=True)
        
        # 소득(income) 변수를 수치형으로 변환 (3D 그래프를 위해)
        # <=50K는 0, >50K는 1로 매핑
        df['income_numeric'] = df['income'].apply(lambda x: 1 if x.strip() == '>50K' else 0)
        
        return df
    except FileNotFoundError:
        st.error("`adult.csv` 파일을 찾을 수 없습니다. Streamlit 앱 파일과 같은 디렉토리에 있는지 확인하거나, 파일 경로를 정확히 지정해주세요.")
        st.stop() # 파일이 없으면 앱 실행 중지
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        st.stop()

df = load_data()

# --- Streamlit 앱 구성 ---
st.set_page_config(layout="wide")
st.title("성인 인구조사 데이터를 활용한 소득과 교육 수준 연관성 분석 (3D 시각화)")
st.markdown("""
이 대시보드는 **성인 인구조사 데이터**를 기반으로 **교육 수준(education.num)**과 **소득(income)** 간의 관계를 **3D 그래프**를 통해 탐색합니다.
세 번째 축에는 선택된 **추가 범주형 변수**를 배치하여 더 깊은 인사이트를 얻을 수 있습니다.
""")

st.sidebar.header("3D 그래프 설정")

# X축: 교육 수준 (education.num)
x_axis_col = 'education.num'
st.sidebar.markdown(f"**X축:** 교육 수준 (education.num)")

# Y축: 소득 (income_numeric)
y_axis_col = 'income_numeric'
st.sidebar.markdown(f"**Y축:** 소득 (<=50K: 0, >50K: 1)")

# Z축으로 사용할 변수 선택
# 노트북의 범주형 피처 목록을 참고했습니다.
z_axis_options = [
    'race', 'sex', 'marital.status', 'workclass', 
    'occupation', 'relationship', 'native.country'
]
z_axis_col = st.sidebar.selectbox("Z축으로 사용할 변수 선택", z_axis_options)

# --- 데이터 필터링 (옵션) ---
st.sidebar.markdown("---")
st.sidebar.subheader("데이터 필터링")

df_filtered = df.copy()

# 교육 수준 수치 범위 필터
min_edu, max_edu = st.sidebar.slider(
    "교육 수준 수치 (education.num)",
    int(df_filtered[x_axis_col].min()), int(df_filtered[x_axis_col].max()),
    (int(df_filtered[x_axis_col].min()), int(df_filtered[x_axis_col].max()))
)
df_filtered = df_filtered[(df_filtered[x_axis_col] >= min_edu) & (df_filtered[x_axis_col] <= max_edu)]

# 원본 교육 수준(education) 필터 (optional)
st.sidebar.markdown("---")
all_education_levels = df['education'].unique().tolist()
selected_education = st.sidebar.multiselect(
    "교육 수준 (education) 선택",
    options=all_education_levels,
    default=all_education_levels
)
df_filtered = df_filtered[df_filtered['education'].isin(selected_education)]

# 소득 필터
selected_income_types = st.sidebar.multiselect(
    "소득 유형 선택",
    options=df['income'].unique().tolist(),
    default=df['income'].unique().tolist()
)
df_filtered = df_filtered[df_filtered['income'].isin(selected_income_types)]

st.markdown("---")

### **3D 산점도 그리기**
st.header("소득과 교육 수준의 3D 관계")

if not df_filtered.empty:
    fig = px.scatter_3d(
        df_filtered,
        x=x_axis_col,
        y=y_axis_col,
        z=z_axis_col,
        color=z_axis_col, # Z축 변수에 따라 색상 부여
        hover_data=['age', 'workclass', 'education', 'marital.status', 'occupation', 'hours.per.week', 'native.country'], # 마우스 오버 시 추가 정보 표시
        labels={
            x_axis_col: '교육 수준 수치 (education.num)',
            y_axis_col: '소득 (>50K: 1, <=50K: 0)',
            z_axis_col: z_axis_col
        },
        title=f'교육 수준, 소득 및 {z_axis_col}의 3D 관계',
        height=700 # 그래프 높이 조정
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("선택된 필터에 해당하는 데이터가 없습니다. 필터를 조정해주세요.")

st.markdown("---")

st.header("데이터 개요")
st.dataframe(df_filtered.head())
st.dataframe(df_filtered.describe(include='all'))

st.markdown("---")
st.markdown("""
### **분석 결과 및 시사점**
* **소득-교육 관계:** 3D 그래프를 통해 교육 수준(education.num)이 높을수록 소득이 높아지는 경향(income_numeric 값이 1에 가까워짐)을 시각적으로 확인할 수 있습니다.
* **제3 변수의 영향:** Z축으로 선택된 변수(예: 인종, 성별, 결혼 상태 등)에 따라 교육 수준과 소득 간의 관계가 어떻게 달라지는지 파악할 수 있습니다. 예를 들어, 특정 그룹에서 교육 수준에 따른 소득 증가 폭이 더 크거나 작게 나타날 수 있습니다.
* **데이터의 이해:** `adult.csv` 데이터는 성인의 인구 통계 및 소득 정보를 포함하며, 이는 교육, 직업, 사회경제적 지위 등 다양한 사회적 요인들이 개인의 소득에 미치는 영향을 분석하는 데 활용될 수 있습니다.

**참고:**
* `education.num`은 교육 수준을 1부터 16까지의 숫자로 나타낸 것입니다. 숫자가 높을수록 고등 교육을 의미합니다.
* `income_numeric`은 `<=50K`를 0, `>50K`를 1로 변환한 값입니다.
""")

st.info("이 대시보드는 `adult.csv` 파일의 데이터를 직접 사용합니다. GitHub에 앱과 함께 `adult.csv` 파일을 올리거나, Streamlit Cloud의 경우 `data` 폴더 안에 넣어 경로를 지정해야 합니다.")
