"""온라인 산사만 단독으로 여는 진입점.

Streamlit Community Cloud에서 Main file path를 이 파일로 지정하면
MBTI 페이지 없이 곧바로 「새벽 산사」가 열린다.
(app.py로 배포하면 MBTI 앱과 함께 왼쪽 메뉴에 산사가 나온다.)
"""
from pathlib import Path

import streamlit as st

TEMPLE_PAGE = Path(__file__).parent / "pages" / "온라인 산사.py"

st.navigation(
    [st.Page(TEMPLE_PAGE, title="새벽 산사", icon="🪷", default=True)],
    position="hidden",
).run()
