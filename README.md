# mbti20260729

Streamlit으로 만든 웹앱 모음이에요.

| 실행 파일 | 내용 |
| --- | --- |
| `app.py` | 🧭 MBTI 진로 상담소 (왼쪽 메뉴에 MBTI 페이지들과 🪷 온라인 산사가 함께 나와요) |
| `temple_app.py` | 🪷 **새벽 산사**만 단독으로 열기 — 명상 · 불공 · 독경 · 수행 기록 · 새벽 알림 |

## 🌐 웹앱으로 배포하기 (Streamlit Community Cloud, 무료)

1. <https://share.streamlit.io> 에 들어가 **GitHub 계정으로 로그인**해요.
2. 오른쪽 위 **Create app** → **Deploy a public app from GitHub**를 골라요.
3. 아래처럼 채워요.
   - **Repository**: `ryunahkim-debug/mbti20260729`
   - **Branch**: 산사 기능이 있는 브랜치 (main에 합친 뒤라면 `main`)
   - **Main file path**: `temple_app.py` (산사만) 또는 `app.py` (MBTI 앱 + 산사)
   - **App URL**: 원하는 주소, 예) `dawn-sansa` → `https://dawn-sansa.streamlit.app`
4. **Deploy**를 누르면 1~2분 뒤 주소가 열려요. 이후 GitHub에 올린 변경은 자동으로 반영돼요.

> 한동안 아무도 들어오지 않으면 앱이 잠들어요. 그럴 땐 화면의 깨우기 버튼(“Yes, get this app back up!”)을 누르고 30초쯤 기다리면 다시 열려요.

## 📱 휴대폰 홈 화면에 앱처럼 두기

- **아이폰 (Safari)**: 주소를 연 뒤 공유 버튼 → **홈 화면에 추가**
- **안드로이드 (Chrome)**: 주소를 연 뒤 오른쪽 위 ⋮ → **홈 화면에 추가** (또는 **앱 설치**)

홈 화면의 아이콘을 누르면 앱처럼 바로 새벽 산사가 열려요.

## 💻 내 컴퓨터에서 실행하기

```bash
pip install -r requirements.txt
streamlit run temple_app.py   # 또는 streamlit run app.py
```
