import html
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

st.set_page_config(page_title="온라인 산사", page_icon="🪷", layout="centered")

# ---------------------------------------------------------------
# 0. 고요한 새벽 분위기 (색감 / 글꼴)
# ---------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700&display=swap');
    .stApp {
        background: linear-gradient(180deg, #0f1724 0%, #1c2536 45%, #3a3346 80%, #5b4a4a 100%);
        color: #e8e2d6;
    }
    [data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3,
    [data-testid="stMain"] p, [data-testid="stMain"] label, [data-testid="stMain"] li {
        font-family: 'Nanum Myeongjo', serif;
        color: #e8e2d6;
    }
    [data-testid="stMain"] header, [data-testid="stHeader"] { background: transparent; }
    [data-testid="stMain"] .stButton button:not([kind="primary"]),
    [data-testid="stMain"] .stDownloadButton button {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(232, 226, 214, 0.35);
    }
    .temple-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(232, 226, 214, 0.15);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin: 0.6rem 0 1rem;
        line-height: 1.9;
    }
    .sutra {
        text-align: center;
        font-size: 1.05rem;
        line-height: 2.2;
        letter-spacing: 0.04em;
    }
    .quiet { color: #b8ae9c !important; font-size: 0.92rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# 1. 지금 산사의 시간 (한국 시간 기준)
# ---------------------------------------------------------------
now = datetime.now(ZoneInfo("Asia/Seoul"))
hour = now.hour

if 3 <= hour < 4:
    moment = "🌌 도량석(道場釋) 시간이에요. 목탁 소리로 도량을 깨우며 하루를 엽니다."
elif 4 <= hour < 6:
    moment = "🔔 새벽예불 시간이에요. 범종이 울리고, 고요히 마음을 모아 봅니다."
elif 6 <= hour < 9:
    moment = "🌅 동이 트는 아침이에요. 맑은 공기 속에서 하루의 발원을 세워 보세요."
elif 9 <= hour < 18:
    moment = "☀️ 낮의 산사예요. 바쁜 와중에도 숨 한 번, 잠시 멈춰 봅니다."
elif 18 <= hour < 21:
    moment = "🌆 저녁예불 시간이에요. 오늘 하루를 돌아보며 감사함을 올립니다."
else:
    moment = "🌙 산사는 잠든 밤이에요. 내일 새벽을 위해 편히 쉬어 가세요."

st.title("🪷 새벽 산사")
st.markdown(
    f"<p class='quiet'>{now.strftime('%Y년 %m월 %d일 %H:%M')} · 한국 시간</p>",
    unsafe_allow_html=True,
)
st.markdown(f"<div class='temple-card'>{moment}</div>", unsafe_allow_html=True)

# 세션 동안의 수행 기록
if "practice_log" not in st.session_state:
    st.session_state.practice_log = []

tab_meditate, tab_offer, tab_chant, tab_log = st.tabs(
    ["🧘 명상", "🕯️ 불공 드리기", "📿 독경", "📖 오늘의 기록"]
)

# ---------------------------------------------------------------
# 2. 명상 — 타종으로 시작하고 끝나는 타이머 (소리는 브라우저에서 합성)
# ---------------------------------------------------------------
with tab_meditate:
    st.subheader("🧘 고요히 앉기")
    st.markdown(
        "<p class='quiet'>허리를 곧게 펴고 편히 앉으세요. 시작하면 종이 세 번 울리고, "
        "시간이 다 되면 다시 종이 울립니다. 원이 커질 때 들이쉬고, 작아질 때 내쉬어요.</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        minutes = st.select_slider("명상 시간 (분)", options=[3, 5, 10, 15, 20, 30, 45, 60], value=10)
    with col2:
        moktak = st.toggle("시작 전 목탁 소리", value=True)

    meditation_html = f"""
    <div id="wrap" style="font-family:'Nanum Myeongjo',serif;color:#e8e2d6;text-align:center;padding:10px 0;">
      <div id="circle" style="width:120px;height:120px;margin:20px auto;border-radius:50%;
           background:radial-gradient(circle,#f3d9a4 0%,#c58b4e 55%,rgba(197,139,78,0) 72%);
           transform:scale(0.6);transition:transform 4s ease-in-out;opacity:.85;"></div>
      <div id="guide" style="font-size:16px;min-height:24px;color:#b8ae9c;">준비가 되면 시작하세요</div>
      <div id="time" style="font-size:42px;margin:8px 0 14px;letter-spacing:.08em;">{minutes:02d}:00</div>
      <button id="btn" style="background:#c58b4e;color:#1c2536;border:none;border-radius:24px;
              padding:10px 28px;font-size:16px;cursor:pointer;font-family:inherit;">🔔 입정 (시작)</button>
    </div>
    <script>
    const TOTAL = {minutes} * 60;
    const USE_MOKTAK = {str(moktak).lower()};
    let ctx = null, timer = null, breath = null, endAt = 0, running = false;
    const $ = id => document.getElementById(id);

    // 싱잉볼/범종 느낌의 종소리: 여러 배음을 겹쳐 길게 사라지게 함
    function bell(t, base) {{
      [[1,0.5],[2.76,0.25],[5.4,0.12],[8.93,0.06]].forEach(([mul, amp]) => {{
        const o = ctx.createOscillator(), g = ctx.createGain();
        o.frequency.value = base * mul;
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime(amp, t + 0.01);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 9 / Math.sqrt(mul));
        o.connect(g).connect(ctx.destination);
        o.start(t); o.stop(t + 10);
      }});
    }}
    // 목탁: 짧고 둥근 나무 소리
    function knock(t) {{
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.frequency.setValueAtTime(720, t);
      o.frequency.exponentialRampToValueAtTime(480, t + 0.12);
      g.gain.setValueAtTime(0.7, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.18);
      o.connect(g).connect(ctx.destination);
      o.start(t); o.stop(t + 0.2);
    }}
    function fmt(s) {{
      return String(Math.floor(s/60)).padStart(2,'0') + ':' + String(s%60).padStart(2,'0');
    }}
    function startBreath() {{
      let inhale = true;
      const step = () => {{
        $('circle').style.transform = inhale ? 'scale(1.25)' : 'scale(0.6)';
        $('guide').textContent = inhale ? '들이쉬고…' : '내쉬고…';
        inhale = !inhale;
      }};
      step(); breath = setInterval(step, 4000);
    }}
    function stop(done) {{
      running = false;
      clearInterval(timer); clearInterval(breath);
      $('circle').style.transform = 'scale(0.6)';
      $('btn').textContent = '🔔 입정 (시작)';
      if (done) {{
        const t = ctx.currentTime + 0.1;
        bell(t, 196); bell(t + 5, 196); bell(t + 10, 196);
        $('guide').textContent = '🙏 출정(出定) — 수고하셨습니다. 고요함을 하루로 가져가세요.';
        $('time').textContent = '00:00';
      }} else {{
        $('guide').textContent = '잠시 멈추었습니다';
        $('time').textContent = fmt(TOTAL);
      }}
    }}
    $('btn').onclick = () => {{
      if (running) {{ stop(false); return; }}
      ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
      ctx.resume();
      running = true;
      $('btn').textContent = '⏹ 멈추기';
      let t = ctx.currentTime + 0.1, lead = 0;
      if (USE_MOKTAK) {{
        // 점점 빨라졌다가 잦아드는 목탁 한 줄
        const gaps = [0.9,0.8,0.7,0.6,0.5,0.4,0.32,0.26,0.22,0.2,0.2,0.2];
        gaps.forEach(g => {{ knock(t + lead); lead += g; }});
        lead += 1.0;
      }}
      bell(t + lead, 196); bell(t + lead + 6, 196); bell(t + lead + 12, 196);
      $('guide').textContent = '종소리와 함께 마음을 내려놓습니다…';
      setTimeout(() => {{
        if (!running) return;
        endAt = Date.now() + TOTAL * 1000;
        startBreath();
        timer = setInterval(() => {{
          const left = Math.max(0, Math.round((endAt - Date.now()) / 1000));
          $('time').textContent = fmt(left);
          if (left <= 0) stop(true);
        }}, 500);
      }}, (lead + 1) * 1000);
    }};
    </script>
    """
    if hasattr(st, "iframe"):  # Streamlit 최신 버전
        st.iframe(meditation_html, height=330)
    else:
        import streamlit.components.v1 as components
        components.html(meditation_html, height=330)

    if st.button("🙏 오늘의 명상을 기록하기"):
        st.session_state.practice_log.append(
            f"{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%H:%M')} · 🧘 {minutes}분 명상"
        )
        st.success("기록했어요. 꾸준함이 곧 수행입니다.")

# ---------------------------------------------------------------
# 3. 불공 드리기 — 육법공양과 발원
# ---------------------------------------------------------------
OFFERINGS = {
    "🪔 등(燈)": "어둠을 밝히는 지혜의 빛",
    "🌿 향(香)": "스스로를 태워 주변을 맑히는 해탈의 향",
    "🌸 꽃(花)": "수행의 열매를 맺는 만행의 꽃",
    "🍵 차(茶)": "번뇌의 갈증을 씻는 감로의 차",
    "🍎 과일(果)": "깨달음의 결실을 뜻하는 보리의 과일",
    "🍚 쌀(米)": "모든 생명을 살리는 기쁨의 공양미",
}

with tab_offer:
    st.subheader("🕯️ 부처님 전에 공양 올리기")
    st.markdown(
        "<p class='quiet'>예로부터 부처님께 올리는 여섯 가지 공양(육법공양)이 있어요. "
        "마음 가는 공양을 고르고, 조용히 발원을 적어 보세요.</p>",
        unsafe_allow_html=True,
    )

    chosen = st.multiselect(
        "올릴 공양", list(OFFERINGS.keys()), default=["🪔 등(燈)", "🌿 향(香)"]
    )
    for item in chosen:
        st.markdown(f"- **{item}** — {OFFERINGS[item]}")

    wish = st.text_area(
        "발원문 (마음속 바람을 적어 주세요)",
        placeholder="예) 가족 모두 건강하고, 제가 오늘 하루 화내지 않고 따뜻한 말을 하게 하소서.",
        height=110,
    )

    if st.button("🙇 삼배 올리고 공양하기", type="primary", disabled=not chosen):
        icons = " ".join(item.split()[0] for item in chosen)
        st.markdown(
            f"""
            <div class='temple-card' style='text-align:center;'>
              <div style='font-size:2.6rem;letter-spacing:.3em;'>{icons}</div>
              <p>🙇 🙇 🙇</p>
              <p>정성스러운 공양이 부처님 전에 올려졌습니다.</p>
              <p class='quiet'>나무 석가모니불 · 나무 석가모니불 · 나무 시아본사 석가모니불</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if wish.strip():
            st.markdown(
                f"<div class='temple-card'><b>📜 발원</b><br>"
                f"{html.escape(wish.strip()).replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )
        st.session_state.practice_log.append(
            f"{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%H:%M')} · 🕯️ 공양 ({icons})"
            + (f" — {wish.strip()[:40]}" if wish.strip() else "")
        )

# ---------------------------------------------------------------
# 4. 독경 — 반야심경 함께 읽기
# ---------------------------------------------------------------
HEART_SUTRA = """
**마하반야바라밀다심경**

관자재보살 행심반야바라밀다시<br>조견오온개공 도일체고액<br><br>
사리자 색불이공 공불이색<br>색즉시공 공즉시색<br>수상행식 역부여시<br><br>
사리자 시제법공상<br>불생불멸 불구부정 부증불감<br><br>
시고 공중무색 무수상행식<br>무안이비설신의 무색성향미촉법<br>무안계 내지 무의식계<br><br>
무무명 역무무명진<br>내지 무노사 역무노사진<br>무고집멸도 무지 역무득<br>이무소득고<br><br>
보리살타 의반야바라밀다고<br>심무가애 무가애고 무유공포<br>원리전도몽상 구경열반<br><br>
삼세제불 의반야바라밀다고<br>득아뇩다라삼먁삼보리<br><br>
고지반야바라밀다<br>시대신주 시대명주 시무상주 시무등등주<br>능제일체고 진실불허<br><br>
고설반야바라밀다주 즉설주왈<br><br>
**아제아제 바라아제 바라승아제 모지 사바하**<br>
**아제아제 바라아제 바라승아제 모지 사바하**<br>
**아제아제 바라아제 바라승아제 모지 사바하**
"""

with tab_chant:
    st.subheader("📿 반야심경 독송")
    st.markdown(
        "<p class='quiet'>소리 내어 천천히, 한 구절씩 읽어 보세요. 뜻을 몰라도 괜찮아요. "
        "읽는 동안 마음이 한곳에 머무는 것, 그것이 독경입니다.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<div class='temple-card sutra'>{HEART_SUTRA}</div>", unsafe_allow_html=True)

    if st.button("📿 독송을 마쳤어요"):
        st.session_state.practice_log.append(
            f"{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%H:%M')} · 📿 반야심경 독송"
        )
        st.success("수희찬탄합니다. 🙏")

# ---------------------------------------------------------------
# 5. 오늘의 기록 + 한 줄 법문
# ---------------------------------------------------------------
TEACHINGS = [
    "마음이 모든 것의 근본이다. 마음이 맑으면 세상도 맑아진다.",
    "미움은 미움으로 그치지 않는다. 미움을 버릴 때에만 그친다.",
    "지나간 일을 좇지 말고, 오지 않은 일을 바라지 말라. 지금 이 순간을 살펴라.",
    "물방울이 모여 항아리를 채우듯, 작은 선행이 모여 큰 복이 된다.",
    "남의 허물을 보지 말고, 내가 한 일과 하지 않은 일을 살펴라.",
    "바위가 바람에 흔들리지 않듯, 지혜로운 이는 칭찬과 비난에 흔들리지 않는다.",
    "스스로 등불을 삼고, 스스로를 의지하라.",
]

with tab_log:
    st.subheader("📖 오늘의 수행 기록")
    # 날짜마다 같은 법문이 나오도록 날짜를 씨앗으로 사용
    teaching = random.Random(now.strftime("%Y%m%d")).choice(TEACHINGS)
    st.markdown(f"<div class='temple-card'>🍃 <b>오늘의 법문</b><br>{teaching}</div>", unsafe_allow_html=True)

    if st.session_state.practice_log:
        for entry in st.session_state.practice_log:
            st.markdown(f"- {entry}")
        st.download_button(
            "📥 수행일지 저장하기",
            data=f"{now.strftime('%Y-%m-%d')} 수행일지\n\n" + "\n".join(st.session_state.practice_log),
            file_name=f"수행일지_{now.strftime('%Y%m%d')}.txt",
        )
    else:
        st.markdown("<p class='quiet'>아직 기록이 없어요. 오늘의 첫 수행을 시작해 보세요.</p>", unsafe_allow_html=True)

    st.caption("※ 기록은 이 창을 열어둔 동안에만 남아요. 매일 간직하고 싶다면 수행일지를 저장해 두세요.")
