import streamlit as st

st.set_page_config(page_title="나라별 MBTI 분포", page_icon="🌍", layout="centered")

st.title("🌍 글로벌 눈으로 보는 나라별 MBTI 분포 특성")
st.markdown("세계 각국마다 문화와 환경에 따라 성격 유형 분포가 조금씩 다르다는 사실, 알고 있니? 주요 국가들의 성향을 살펴볼까? ✈️")
st.markdown("---")

country_selection = st.selectbox(
    "궁금한 국가를 선택해 봐! 👇",
    ["대한민국 (Korea)", "미국 (USA)", "일본 (Japan)", "독일 (Germany)"]
)

if "대한민국" in country_selection:
    st.subheader("🇰🇷 대한민국: 꼼꼼함과 책임감 중심 (ISTJ / ISFJ / ESTJ 우세)")
    st.write("- **특징**: 전통적으로 사회적 규범, 성실함, 체계적인 시스템을 중요하게 여기는 성향의 비율이 전 세계 평균 대비 높은 편이에요.")
    st.success("💡 **상담가쌤의 한마디**: 대한민국 학생들은 책임감이 강해서 때로는 어깨가 무거울 수 있어. 조금은 여유를 가져도 괜찮단다!")

elif "미국" in country_selection:
    st.subheader("🇺🇸 미국: 자유로움과 외향성 (ENFP / ESFJ / ESTP 우세)")
    st.write("- **특징**: 개인의 표현을 중요시하고 새로운 도전과 사교 활동을 즐기는 외향형(E) 및 직관형(N)의 비율이 상대적으로 높게 나타납니다.")
    st.success("💡 **상담가쌤의 한마디**: 자신의 생각을 거침없이 표현하고 도전하는 분위기가 문화 속에 잘 녹아있지!")

elif "일본" in country_selection:
    st.subheader("🇯🇵 일본: 배려와 내향적 조화 (ISFJ / INFP / ISTJ 우세)")
    st.write("- **특징**: 타인과의 조화를 매우 중요하게 생각하고, 세심하게 주변을 배려하는 내향형(I) 및 감각형(S) 유형의 비중이 높아요.")
    st.success("💡 **상담가쌤의 한마디**: 남을 배려하는 마음은 아름답지만, 때로는 너 자신의 목소리도 당당하게 내보렴!")

elif "독일" in country_selection:
    st.subheader("🇩🇪 독일: 철저한 분석과 논리 (INTJ / ISTJ 우세)")
    st.write("- **특징**: 효율성, 정밀함, 철학적이고 논리적인 분석력을 중시하는 사고형(T)과 계획형(J)의 기질이 뚜렷하게 관찰되는 나라입니다.")
    st.success("💡 **상담가쌤의 한마디**: 원칙과 계획을 중시하는 멋진 논리력을 가지고 있구나!")