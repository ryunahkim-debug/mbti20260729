import streamlit as st

st.set_page_config(page_title="한국 MBTI 비율", page_icon="🇰🇷", layout="centered")

st.title("🇰🇷 우리나라 대중적인 MBTI 비율 분석")
st.markdown("한국갤럽 및 각종 통계 자료를 바탕으로 재구성한 국내 추정 MBTI 비율 분포란다! 📊")
st.markdown("---")

# 통계 데이터
korea_mbti_ratios = {
    'ISTJ': 13.5, 'ISFJ': 9.5, 'INFJ': 3.1, 'INTJ': 4.1,
    'ISTP': 8.9, 'ISFP': 6.2, 'INFP': 5.1, 'INTP': 3.8,
    'ESTP': 5.8, 'ESFP': 5.3, 'ENFP': 4.3, 'ENTP': 3.2,
    'ESTJ': 7.9, 'ESFJ': 8.5, 'ENFJ': 3.7, 'ENTJ': 3.2
}

st.subheader("📌 유형별 인구 비율 순위표 (%)")
sorted_ratios = sorted(korea_mbti_ratios.items(), key=lambda x: x[1], reverse=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**상위 그룹 (자주 볼 수 있는 유형)**")
    for mbti, pct in sorted_ratios[:8]:
        st.markdown(f"- **{mbti}**: {pct}%")
with col2:
    st.markdown("**하위 그룹 (희귀한 유형)**")
    for mbti, pct in sorted_ratios[8:]:
        st.markdown(f"- **{mbti}**: {pct}%")

st.markdown("---")
st.subheader("📈 시각화 그래프")
st.bar_chart(korea_mbti_ratios)
st.caption("※ 참고용 통계 자료이며 표본 집단에 따라 약간의 차이가 있을 수 있습니다.")