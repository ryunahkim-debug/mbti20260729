import hashlib
import hmac
import html
import json
import random
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

st.set_page_config(page_title="온라인 산사", page_icon="🪷", layout="centered")

KST = ZoneInfo("Asia/Seoul")


def render_html(src: str, height: int) -> None:
    """HTML+JS를 iframe으로 그린다 (Streamlit 신·구버전 모두 지원)."""
    if hasattr(st, "iframe"):
        st.iframe(src, height=height)
    else:
        import streamlit.components.v1 as components

        components.html(src, height=height)


def js_value(value) -> str:
    """파이썬 값을 <script> 안에 안전하게 넣을 수 있는 JS 리터럴로 바꾼다."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


# ---------------------------------------------------------------
# 수행 기록 저장소
# 기록은 각자의 브라우저(localStorage)에만 저장되어, 창을 닫아도 날마다 쌓이고
# 다른 사람에게는 보이지 않는다. 모든 iframe이 같은 키를 함께 쓴다.
# ---------------------------------------------------------------
STORE_JS = """
const SANSA_KEY = 'online_sansa_log_v1';
function kstNow() {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false
  }).formatToParts(new Date());
  const p = Object.fromEntries(parts.map(x => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, time: `${p.hour === '24' ? '00' : p.hour}:${p.minute}` };
}
function loadLog() {
  try { return JSON.parse(localStorage.getItem(SANSA_KEY) || '[]'); } catch (e) { return []; }
}
function saveEntry(entry) {
  try {
    const log = loadLog();
    if (log.some(x => x.id === entry.id)) return;   // 같은 기록을 두 번 넣지 않음
    const t = kstNow();
    log.push(Object.assign({ date: t.date, time: t.time }, entry));
    localStorage.setItem(SANSA_KEY, JSON.stringify(log));
  } catch (e) { /* 저장이 막힌 브라우저(시크릿 창 등)에서는 조용히 넘어감 */ }
}
"""


def record(kind: str, text: str, minutes: int = 0) -> None:
    """버튼을 누른 그 순간의 수행을 브라우저 저장소에 한 줄 추가한다."""
    entry = {"id": uuid.uuid4().hex, "kind": kind, "text": text, "minutes": minutes}
    render_html(f"<script>{STORE_JS}\nsaveEntry({js_value(entry)});</script>", height=1)


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
    [data-testid="stMain"] .stDownloadButton button:not([kind="primary"]) {
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
    .sutra h4 { color: #f3d9a4; margin: 1.4rem 0 0.4rem; font-size: 1.05rem; }
    .quiet { color: #b8ae9c !important; font-size: 0.92rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------
# 0-1. 산문(山門) 잠금 — 주인만 들어올 수 있게
# 비밀번호는 코드가 아니라 배포 설정의 Secrets에 `sansa_password = "..."`로 넣는다.
# 설정하지 않으면(예: 내 컴퓨터에서 실행) 잠금 없이 열린다.
# 홈 화면 바로가기용 주소에는 비밀번호 대신 비밀번호에서 만든 열쇠(key)가 붙는다.
# ---------------------------------------------------------------
def _owner_password():
    try:
        return st.secrets.get("sansa_password")
    except Exception:  # secrets.toml이 아예 없을 때
        return None


def _door_key(password: str) -> str:
    return hashlib.sha256(f"online-sansa:{password}".encode()).hexdigest()[:32]


def open_temple_gate() -> None:
    password = _owner_password()
    if not password or st.session_state.get("sansa_owner"):
        return

    key = _door_key(str(password))
    if hmac.compare_digest(st.query_params.get("key", "").encode(), key.encode()):
        st.session_state.sansa_owner = True
        return

    st.title("🪷 새벽 산사")
    st.markdown(
        "<div class='temple-card' style='text-align:center;'>🔒 산문이 닫혀 있어요.<br>"
        "<span class='quiet'>이 산사의 주인만 들어올 수 있어요.</span></div>",
        unsafe_allow_html=True,
    )
    with st.form("gate"):
        typed = st.text_input("비밀번호", type="password")
        remember = st.checkbox("이 기기에서 기억하기 (홈 화면 바로가기용 주소 만들기)", value=True)
        entered = st.form_submit_button("🙏 들어가기", type="primary")
    if entered:
        if hmac.compare_digest(typed.encode(), str(password).encode()):
            st.session_state.sansa_owner = True
            if remember:
                st.query_params["key"] = key
            st.rerun()
        else:
            st.error("비밀번호가 맞지 않아요.")
    st.stop()


open_temple_gate()

# ---------------------------------------------------------------
# 1. 지금 산사의 시간 (한국 시간 기준)
# ---------------------------------------------------------------
now = datetime.now(KST)
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

tab_meditate, tab_offer, tab_chant, tab_log, tab_alarm = st.tabs(
    ["🧘 명상", "🕯️ 불공", "📿 독경", "📖 기록", "🔔 알림"]
)

# ---------------------------------------------------------------
# 명상 타이머 + 명상 음악
# 모든 소리(종·목탁·음악·자연의 소리)는 브라우저(Web Audio)에서 그때그때 만들어 낸다.
# 그래서 음원 파일이 필요 없고, 저작권 걱정 없이 끝없이 이어진다.
# ---------------------------------------------------------------
MEDITATION_TEMPLATE = """
<style>
  body { margin:0; font-family:'Nanum Myeongjo',serif; color:#e8e2d6; }
  .wrap { text-align:center; padding:6px 0; }
  .music { display:flex; gap:10px; align-items:center; justify-content:center; flex-wrap:wrap;
           background:rgba(255,255,255,.05); border:1px solid rgba(232,226,214,.15);
           border-radius:12px; padding:10px 12px; margin:0 4px 6px; font-size:14px; }
  select { font-family:inherit; font-size:14px; background:#1c2536; color:#e8e2d6;
           border:1px solid rgba(232,226,214,.35); border-radius:8px; padding:5px 8px; }
  input[type=range] { width:110px; accent-color:#c58b4e; }
  .ghost { font-family:inherit; font-size:13px; border-radius:18px; padding:5px 12px; cursor:pointer;
           background:rgba(255,255,255,.06); color:#e8e2d6; border:1px solid rgba(232,226,214,.35); }
  #circle { width:120px; height:120px; margin:18px auto; border-radius:50%;
            background:radial-gradient(circle,#f3d9a4 0%,#c58b4e 55%,rgba(197,139,78,0) 72%);
            transform:scale(0.6); transition:transform 4s ease-in-out; opacity:.85; }
  #guide { font-size:16px; min-height:24px; color:#b8ae9c; }
  #time { font-size:42px; margin:8px 0 14px; letter-spacing:.08em; }
  #btn { background:#c58b4e; color:#1c2536; border:none; border-radius:24px; padding:10px 28px;
         font-size:16px; cursor:pointer; font-family:inherit; }
</style>
<div class="wrap">
  <div class="music">
    <label for="kind">🎵 명상 음악</label>
    <select id="kind">
      <option value="none">소리 없이 고요히</option>
      <option value="drone">🎶 잔잔한 명상 음악</option>
      <option value="chime">🎐 산사의 바람과 풍경 소리</option>
      <option value="stream">💧 계곡 물소리</option>
      <option value="rain">🌧️ 처마 끝 빗소리</option>
    </select>
    <span>🔉</span><input id="vol" type="range" min="0" max="100" value="60" aria-label="음악 크기">
    <button id="preview" class="ghost">🎧 미리 듣기</button>
  </div>
  <div id="circle"></div>
  <div id="guide">준비가 되면 시작하세요</div>
  <div id="time">__MINUTES_PAD__:00</div>
  <button id="btn">🔔 입정 (시작)</button>
</div>
<script>
__STORE_JS__
const TOTAL = __MINUTES__ * 60;
const USE_MOKTAK = __MOKTAK__;
let ctx = null, timer = null, breath = null, startedAt = 0, endAt = 0, running = false;
let musicOut = null, music = null, previewing = false;
const $ = id => document.getElementById(id);

// ---- 음악 설정은 브라우저에 기억해 둔다 ----
try {
  $('kind').value = localStorage.getItem('online_sansa_music') || 'drone';
  $('vol').value = localStorage.getItem('online_sansa_volume') || '60';
} catch (e) {}

function ensureCtx() {
  if (!ctx) {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    musicOut = ctx.createGain();
    musicOut.connect(ctx.destination);
    setVolume();
  }
  ctx.resume();
}
function setVolume() {
  if (!musicOut) return;
  const v = $('vol').value / 100;
  musicOut.gain.setTargetAtTime(v * v * 0.9, ctx.currentTime, 0.1);   // 귀에 자연스러운 곡선
}

// ---- 소리 재료들 ----
function noiseBuffer(color) {
  const len = ctx.sampleRate * 4, buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
  let last = 0, b0 = 0, b1 = 0, b2 = 0;
  for (let i = 0; i < len; i++) {
    const w = Math.random() * 2 - 1;
    if (color === 'brown') { last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; }
    else if (color === 'pink') {
      b0 = 0.99765 * b0 + w * 0.099; b1 = 0.963 * b1 + w * 0.2965; b2 = 0.57 * b2 + w * 1.0527;
      d[i] = (b0 + b1 + b2 + w * 0.1848) * 0.12;
    } else d[i] = w * 0.5;
  }
  return buf;
}
function loopNoise(color) {
  const s = ctx.createBufferSource();
  s.buffer = noiseBuffer(color); s.loop = true; s.start();
  return s;
}
function reverb(seconds) {   // 넓은 법당 같은 울림
  const len = ctx.sampleRate * seconds, ir = ctx.createBuffer(2, len, ctx.sampleRate);
  for (let c = 0; c < 2; c++) {
    const d = ir.getChannelData(c);
    for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 3);
  }
  const conv = ctx.createConvolver(); conv.buffer = ir;
  return conv;
}
function lfo(freq, depth, target) {   // 천천히 출렁이게
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.frequency.value = freq; g.gain.value = depth;
  o.connect(g).connect(target); o.start();
  return o;
}
function tone(dest, freq, t, amp, attack, release, type) {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = type || 'sine'; o.frequency.value = freq;
  g.gain.setValueAtTime(0, t);
  g.gain.linearRampToValueAtTime(amp, t + attack);
  g.gain.exponentialRampToValueAtTime(0.0001, t + attack + release);
  o.connect(g).connect(dest);
  o.start(t); o.stop(t + attack + release + 0.1);
}
function every(minMs, maxMs, fn, timers) {   // 불규칙한 간격으로 되풀이
  const loop = () => { fn(); timers.push(setTimeout(loop, minMs + Math.random() * (maxMs - minMs))); };
  timers.push(setTimeout(loop, minMs * 0.3));
}

// ---- 네 가지 명상 음악 ----
const MUSIC = {
  // 낮은 지속음 위로 오음계의 맑은 음이 드문드문 떠오름
  drone(out, nodes, timers) {
    const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 900;
    const wet = ctx.createGain(); wet.gain.value = 0.7;
    const rv = reverb(5); rv.connect(wet).connect(out);
    lp.connect(out); lp.connect(rv);
    [[98, 0.10, 'sine'], [146.83, 0.07, 'sine'], [196, 0.025, 'triangle']].forEach(([f, a, type], i) => {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = type; o.frequency.value = f; g.gain.value = a;
      o.connect(g).connect(lp); o.start();
      nodes.push(o, lfo(0.05 + i * 0.03, a * 0.4, g.gain));
    });
    const scale = [392, 440, 493.88, 587.33, 659.25, 783.99];
    every(3500, 8000, () => {
      const f = scale[Math.floor(Math.random() * scale.length)], t = ctx.currentTime + 0.05;
      tone(rv, f, t, 0.05, 1.2, 7);
      tone(lp, f, t, 0.025, 1.2, 5);
      if (Math.random() < 0.35) tone(rv, f * 1.5, t + 1.6, 0.025, 1.2, 6);
    }, timers);
  },
  // 산바람이 불었다 잦아들고, 처마의 풍경이 가끔 울림
  chime(out, nodes, timers) {
    const n = loopNoise('brown'), lp = ctx.createBiquadFilter(), g = ctx.createGain();
    lp.type = 'lowpass'; lp.frequency.value = 500; g.gain.value = 0.35;
    n.connect(lp).connect(g).connect(out);
    nodes.push(n, lfo(0.07, 250, lp.frequency), lfo(0.04, 0.18, g.gain));
    const rv = reverb(3); rv.connect(out);
    const notes = [1046.5, 1174.7, 1318.5, 1568, 1760];
    every(3000, 11000, () => {
      let t = ctx.currentTime + 0.05;
      const strikes = 1 + Math.floor(Math.random() * 3);
      for (let i = 0; i < strikes; i++) {
        const f = notes[Math.floor(Math.random() * notes.length)];
        [[1, 0.035], [2.76, 0.012], [5.4, 0.006]].forEach(([m, a]) => tone(rv, f * m, t, a, 0.005, 4 / m));
        t += 0.25 + Math.random() * 0.6;
      }
    }, timers);
  },
  // 바위 사이를 흐르는 물소리
  stream(out, nodes) {
    const low = loopNoise('brown'), bp1 = ctx.createBiquadFilter(), g1 = ctx.createGain();
    bp1.type = 'bandpass'; bp1.frequency.value = 500; bp1.Q.value = 0.4; g1.gain.value = 0.5;
    low.connect(bp1).connect(g1).connect(out);
    const hi = loopNoise('white'), bp2 = ctx.createBiquadFilter(), g2 = ctx.createGain();
    bp2.type = 'bandpass'; bp2.frequency.value = 2200; bp2.Q.value = 1.2; g2.gain.value = 0.05;
    hi.connect(bp2).connect(g2).connect(out);
    nodes.push(low, hi, lfo(0.3, 700, bp2.frequency), lfo(0.13, 0.025, g2.gain), lfo(0.05, 150, bp1.frequency));
  },
  // 처마 끝에 떨어지는 빗소리
  rain(out, nodes, timers) {
    const n = loopNoise('pink'), hp = ctx.createBiquadFilter(), lp = ctx.createBiquadFilter(), g = ctx.createGain();
    hp.type = 'highpass'; hp.frequency.value = 400; lp.type = 'lowpass'; lp.frequency.value = 5000;
    g.gain.value = 0.55;
    n.connect(hp).connect(lp).connect(g).connect(out);
    nodes.push(n, lfo(0.03, 0.1, g.gain));
    const dropBuf = noiseBuffer('white');
    every(40, 260, () => {
      const s = ctx.createBufferSource(), bp = ctx.createBiquadFilter(), dg = ctx.createGain(), t = ctx.currentTime;
      s.buffer = dropBuf; bp.type = 'bandpass'; bp.frequency.value = 1500 + Math.random() * 3500; bp.Q.value = 4;
      dg.gain.setValueAtTime(0.06 + Math.random() * 0.08, t);
      dg.gain.exponentialRampToValueAtTime(0.0001, t + 0.04);
      s.connect(bp).connect(dg).connect(out);
      s.start(t, Math.random() * 3, 0.05);
    }, timers);
  },
};

function startMusic() {
  stopMusic(0.5);
  const kind = $('kind').value;
  if (kind === 'none') return;
  ensureCtx();
  const fade = ctx.createGain(), nodes = [], timers = [];
  fade.gain.setValueAtTime(0, ctx.currentTime);
  fade.gain.linearRampToValueAtTime(1, ctx.currentTime + 5);   // 5초에 걸쳐 스며들 듯 시작
  fade.connect(musicOut);
  MUSIC[kind](fade, nodes, timers);
  music = { fade, nodes, timers };
}
function stopMusic(fadeSec) {
  if (!music) return;
  const m = music; music = null;
  m.timers.forEach(clearTimeout);
  const t = ctx.currentTime;
  m.fade.gain.cancelScheduledValues(t);
  m.fade.gain.setValueAtTime(m.fade.gain.value, t);
  m.fade.gain.linearRampToValueAtTime(0, t + fadeSec);
  setTimeout(() => {
    m.nodes.forEach(n => { try { n.stop(); } catch (e) {} });
    m.fade.disconnect();
  }, fadeSec * 1000 + 200);
}

$('kind').onchange = () => {
  try { localStorage.setItem('online_sansa_music', $('kind').value); } catch (e) {}
  if (running || previewing) {
    startMusic();
    if (previewing && $('kind').value === 'none') { previewing = false; $('preview').textContent = '🎧 미리 듣기'; }
  }
};
$('vol').oninput = () => {
  try { localStorage.setItem('online_sansa_volume', $('vol').value); } catch (e) {}
  setVolume();
};
$('preview').onclick = () => {
  if (running) return;
  if (previewing) {
    previewing = false; stopMusic(1.5); $('preview').textContent = '🎧 미리 듣기';
  } else if ($('kind').value !== 'none') {
    previewing = true; startMusic(); $('preview').textContent = '⏸ 그만 듣기';
  }
};

// ---- 종과 목탁 ----
// 싱잉볼/범종 느낌의 종소리: 여러 배음을 겹쳐 길게 사라지게 함
function bell(t, base) {
  [[1,0.5],[2.76,0.25],[5.4,0.12],[8.93,0.06]].forEach(([mul, amp]) => {
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.frequency.value = base * mul;
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(amp, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 9 / Math.sqrt(mul));
    o.connect(g).connect(ctx.destination);
    o.start(t); o.stop(t + 10);
  });
}
// 목탁: 짧고 둥근 나무 소리
function knock(t) {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.frequency.setValueAtTime(720, t);
  o.frequency.exponentialRampToValueAtTime(480, t + 0.12);
  g.gain.setValueAtTime(0.7, t);
  g.gain.exponentialRampToValueAtTime(0.0001, t + 0.18);
  o.connect(g).connect(ctx.destination);
  o.start(t); o.stop(t + 0.2);
}

// ---- 명상 타이머 ----
function fmt(s) {
  return String(Math.floor(s/60)).padStart(2,'0') + ':' + String(s%60).padStart(2,'0');
}
function startBreath() {
  let inhale = true;
  const step = () => {
    $('circle').style.transform = inhale ? 'scale(1.25)' : 'scale(0.6)';
    $('guide').textContent = inhale ? '들이쉬고…' : '내쉬고…';
    inhale = !inhale;
  };
  step(); breath = setInterval(step, 4000);
}
function stop(done) {
  const sat = startedAt ? Math.floor((Date.now() - startedAt) / 60000) : 0;
  running = false;
  clearInterval(timer); clearInterval(breath);
  $('circle').style.transform = 'scale(0.6)';
  $('btn').textContent = '🔔 입정 (시작)';
  $('preview').disabled = false;
  if (done) {
    stopMusic(8);   // 종소리와 함께 음악이 천천히 잦아듦
    const t = ctx.currentTime + 0.1;
    bell(t, 196); bell(t + 5, 196); bell(t + 10, 196);
    $('guide').textContent = '🙏 출정(出定) — 수고하셨습니다. 수행 기록에 남겼어요.';
    $('time').textContent = '00:00';
    saveEntry({ id: 'med-' + startedAt, kind: 'meditation', minutes: TOTAL / 60, text: (TOTAL / 60) + '분 명상' });
  } else {
    stopMusic(2);
    if (sat >= 1) {
      saveEntry({ id: 'med-' + startedAt, kind: 'meditation', minutes: sat, text: sat + '분 명상 (도중에 마침)' });
      $('guide').textContent = sat + '분 앉았어요. 수행 기록에 남겼어요.';
    } else {
      $('guide').textContent = '잠시 멈추었습니다';
    }
    $('time').textContent = fmt(TOTAL);
  }
  startedAt = 0;
}
$('btn').onclick = () => {
  if (running) { stop(false); return; }
  ensureCtx();
  running = true;
  if (previewing) { previewing = false; $('preview').textContent = '🎧 미리 듣기'; }
  $('preview').disabled = true;
  $('btn').textContent = '⏹ 멈추기';
  let t = ctx.currentTime + 0.1, lead = 0;
  if (USE_MOKTAK) {
    // 점점 빨라졌다가 잦아드는 목탁 한 줄
    const gaps = [0.9,0.8,0.7,0.6,0.5,0.4,0.32,0.26,0.22,0.2,0.2,0.2];
    gaps.forEach(g => { knock(t + lead); lead += g; });
    lead += 1.0;
  }
  bell(t + lead, 196); bell(t + lead + 6, 196); bell(t + lead + 12, 196);
  $('guide').textContent = '종소리와 함께 마음을 내려놓습니다…';
  setTimeout(() => {
    if (!running) return;
    startMusic();   // 종이 울린 뒤 음악이 서서히 피어남
    startedAt = Date.now();
    endAt = startedAt + TOTAL * 1000;
    startBreath();
    timer = setInterval(() => {
      const left = Math.max(0, Math.round((endAt - Date.now()) / 1000));
      $('time').textContent = fmt(left);
      if (left <= 0) stop(true);
    }, 500);
  }, (lead + 1) * 1000);
};
</script>
"""

# ---------------------------------------------------------------
# 2. 명상 — 타종으로 시작하고 끝나는 타이머 (소리는 브라우저에서 합성)
#    끝까지 앉으면(또는 1분 이상 앉았다 멈추면) 수행 기록에 자동으로 남는다.
# ---------------------------------------------------------------
with tab_meditate:
    st.subheader("🧘 고요히 앉기")
    st.markdown(
        "<p class='quiet'>허리를 곧게 펴고 편히 앉으세요. 시작하면 종이 세 번 울리고, "
        "시간이 다 되면 다시 종이 울립니다. 원이 커질 때 들이쉬고, 작아질 때 내쉬어요. "
        "명상 음악을 고르면 종소리 뒤에 음악이 서서히 피어나고, 끝날 때 함께 잦아들어요. "
        "앉은 시간은 수행 기록에 저절로 남아요.</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        minutes = st.select_slider("명상 시간 (분)", options=[3, 5, 10, 15, 20, 30, 45, 60], value=10)
    with col2:
        moktak = st.toggle("시작 전 목탁 소리", value=True)

    meditation_html = (
        MEDITATION_TEMPLATE.replace("__STORE_JS__", STORE_JS)
        .replace("__MINUTES__", str(minutes))
        .replace("__MINUTES_PAD__", f"{minutes:02d}")
        .replace("__MOKTAK__", str(moktak).lower())
    )
    render_html(meditation_html, height=420)

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
        record("offering", f"공양 ({icons})" + (f" — {wish.strip()}" if wish.strip() else ""))

# ---------------------------------------------------------------
# 4. 독경 — 예불문 · 천수경 · 반야심경
# ---------------------------------------------------------------
YEBULMUN = """
<h4>다게 (茶偈)</h4>
아금청정수 변위감로다<br>봉헌삼보전 원수애납수<br>
원수애납수 원수자비애납수

<h4>오분향례 (五分香禮)</h4>
계향 정향 혜향 해탈향 해탈지견향<br>
광명운대 주변법계<br>공양시방 무량불법승

<h4>헌향진언</h4>
옴 바아라 도비야 훔 (세 번)

<h4>칠정례 (七頂禮)</h4>
지심귀명례 삼계도사 사생자부<br>시아본사 석가모니불<br><br>
지심귀명례 시방삼세 제망찰해<br>상주일체 불타야중<br><br>
지심귀명례 시방삼세 제망찰해<br>상주일체 달마야중<br><br>
지심귀명례 대지문수사리보살 대행보현보살<br>대비관세음보살 대원본존지장보살마하살<br><br>
지심귀명례 영산당시 수불부촉 십대제자<br>십육성 오백성 독수성 내지 천이백제대아라한<br>무량자비성중<br><br>
지심귀명례 서건동진 급아해동<br>역대전등 제대조사 천하종사<br>일체미진수 제대선지식<br><br>
지심귀명례 시방삼세 제망찰해<br>상주일체 승가야중

<h4>축원</h4>
유원 무진삼보 대자대비<br>수아정례 명훈가피력<br>
원공법계제중생 자타일시성불도
"""

CHEONSUGYEONG = """
<h4>정구업진언 (淨口業眞言)</h4>
수리수리 마하수리 수수리 사바하 (세 번)

<h4>오방내외안위제신진언</h4>
나무 사만다 못다남 옴 도로도로 지미 사바하 (세 번)

<h4>개경게 (開經偈)</h4>
무상심심미묘법 백천만겁난조우<br>아금문견득수지 원해여래진실의

<h4>개법장진언</h4>
옴 아라남 아라다 (세 번)

<h4>천수천안 관자재보살 광대원만 무애대비심 대다라니 계청</h4>
계수관음대비주 원력홍심상호신<br>천비장엄보호지 천안광명변관조<br>
진실어중선밀어 무위심내기비심<br>속령만족제희구 영사멸제제죄업<br>
천룡중성동자호 백천삼매돈훈수<br>수지신시광명당 수지심시신통장<br>
세척진로원제해 초증보리방편문<br>아금칭송서귀의 소원종심실원만<br><br>
나무대비관세음 원아속지일체법<br>나무대비관세음 원아조득지혜안<br>
나무대비관세음 원아속도일체중<br>나무대비관세음 원아조득선방편<br>
나무대비관세음 원아속승반야선<br>나무대비관세음 원아조득월고해<br>
나무대비관세음 원아속득계정도<br>나무대비관세음 원아조등원적산<br>
나무대비관세음 원아속회무위사<br>나무대비관세음 원아조동법성신<br><br>
아약향도산 도산자최절<br>아약향화탕 화탕자소멸<br>아약향지옥 지옥자고갈<br>
아약향아귀 아귀자포만<br>아약향수라 악심자조복<br>아약향축생 자득대지혜<br><br>
나무관세음보살마하살 나무대세지보살마하살<br>나무천수보살마하살 나무여의륜보살마하살<br>
나무대륜보살마하살 나무관자재보살마하살<br>나무정취보살마하살 나무만월보살마하살<br>
나무수월보살마하살 나무군다리보살마하살<br>나무십일면보살마하살 나무제대보살마하살<br>
나무본사아미타불 (세 번)

<h4>신묘장구대다라니 (神妙章句大陀羅尼)</h4>
나모라 다나다라 야야 나막알약 바로기제 새바라야<br>모지 사다바야 마하 사다바야 마하 가로니가야<br>
옴 살바 바예수 다라나 가라야 다사명<br>나막 까리다바 이맘 알야 바로기제 새바라 다바<br>
니라간타 나막 하리나야 마발다 이사미<br>살발타 사다남 수반 아예염 살바 보다남<br>바바말아 미수다감<br>
다냐타 옴 아로계 아로가 마지로가 지가란제<br>혜혜하례 마하모지 사다바 사마라 사마라 하리나야<br>
구로구로 갈마 사다야 사다야 도로도로 미연제<br>마하 미연제 다라다라 다린나례 새바라<br>
자라자라 마라 미마라 아마라 몰제 예혜혜<br>로계 새바라 라아 미사미 나사야<br>
나베 사미사미 나사야 모하자라 미사미 나사야<br>
호로호로 마라호로 하례 바나마 나바<br>사라사라 시리시리 소로소로 못쟈못쟈<br>
모다야 모다야 매다리야 니라간타<br>가마사 날사남 바라하라 나야 마낙 사바하<br>
싯다야 사바하 마하 싯다야 사바하<br>싯다유예 새바라야 사바하 니라간타야 사바하<br>
바라하 목카 싱하 목카야 사바하<br>바나마 하따야 사바하 자가라 욕다야 사바하<br>
상카 섭나 녜모 다나야 사바하<br>마하라 구타 다라야 사바하<br>
바마 사간타 이사 시체다 가릿나 이나야 사바하<br>먀가라 잘마 이바 사나야 사바하<br>
나모라 다나다라 야야 나막알약 바로기제 새바라야 사바하 (세 번)

<h4>사방찬 (四方讚)</h4>
일쇄동방결도량 이쇄남방득청량<br>삼쇄서방구정토 사쇄북방영안강

<h4>도량찬 (道場讚)</h4>
도량청정무하예 삼보천룡강차지<br>아금지송묘진언 원사자비밀가호

<h4>참회게 (懺悔偈)</h4>
아석소조제악업 개유무시탐진치<br>종신구의지소생 일체아금개참회

<h4>참회진언</h4>
옴 살바 못자모지 사다야 사바하 (세 번)
"""

HEART_SUTRA = """
<h4>마하반야바라밀다심경</h4>
관자재보살 행심반야바라밀다시<br>조견오온개공 도일체고액<br><br>
사리자 색불이공 공불이색<br>색즉시공 공즉시색<br>수상행식 역부여시<br><br>
사리자 시제법공상<br>불생불멸 불구부정 부증불감<br><br>
시고 공중무색 무수상행식<br>무안이비설신의 무색성향미촉법<br>무안계 내지 무의식계<br><br>
무무명 역무무명진<br>내지 무노사 역무노사진<br>무고집멸도 무지 역무득<br>이무소득고<br><br>
보리살타 의반야바라밀다고<br>심무가애 무가애고 무유공포<br>원리전도몽상 구경열반<br><br>
삼세제불 의반야바라밀다고<br>득아뇩다라삼먁삼보리<br><br>
고지반야바라밀다<br>시대신주 시대명주 시무상주 시무등등주<br>능제일체고 진실불허<br><br>
고설반야바라밀다주 즉설주왈<br><br>
<b>아제아제 바라아제 바라승아제 모지 사바하</b><br>
<b>아제아제 바라아제 바라승아제 모지 사바하</b><br>
<b>아제아제 바라아제 바라승아제 모지 사바하</b>
"""

SUTRAS = {
    "🔔 예불문": (
        YEBULMUN,
        "새벽예불의 처음이에요. 맑은 물을 감로차 삼아 올리고, 불·법·승 삼보께 일곱 번 절하며 귀의합니다.",
    ),
    "🙏 천수경": (
        CHEONSUGYEONG,
        "입을 맑히는 진언으로 시작해, 관세음보살의 크신 자비에 기대어 참회하는 경이에요. "
        "여기에는 참회진언까지 앞부분을 실었어요.",
    ),
    "🪷 반야심경": (
        HEART_SUTRA,
        "모든 것이 비어 있음(空)을 깨달아 괴로움에서 벗어나는 지혜를 담은, 가장 짧고 널리 읽히는 경이에요.",
    ),
}

with tab_chant:
    st.subheader("📿 독경")
    st.markdown(
        "<p class='quiet'>새벽에는 예불문 → 천수경 → 반야심경 순서로 읽으면 좋아요. "
        "소리 내어 천천히, 한 구절씩. 뜻을 몰라도 괜찮아요. "
        "읽는 동안 마음이 한곳에 머무는 것, 그것이 독경입니다.</p>",
        unsafe_allow_html=True,
    )
    sutra_name = st.radio("오늘 읽을 경전", list(SUTRAS.keys()), horizontal=True)
    sutra_text, sutra_intro = SUTRAS[sutra_name]
    st.markdown(f"<p class='quiet'>{sutra_intro}</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='temple-card sutra'>{sutra_text}</div>", unsafe_allow_html=True)
    st.caption("※ 사찰과 경본에 따라 표기가 조금씩 다를 수 있어요. 다니시는 절의 경본을 따라 주세요.")

    plain_name = sutra_name.split(" ", 1)[1]
    if st.button(f"📿 {plain_name} 독송을 마쳤어요"):
        record("chant", f"{plain_name} 독송")
        st.success("수희찬탄합니다. 🙏 수행 기록에 남겼어요.")

# ---------------------------------------------------------------
# 5. 수행 기록 — 날짜별로 계속 쌓이는 기록 (브라우저에 저장)
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

LOG_VIEW_HTML = """
<style>
  body { margin:0; font-family:'Nanum Myeongjo',serif; color:#e8e2d6; }
  .stats { display:flex; gap:10px; margin-bottom:14px; }
  .stat { flex:1; background:rgba(255,255,255,.05); border:1px solid rgba(232,226,214,.15);
          border-radius:12px; padding:10px 6px; text-align:center; }
  .stat b { display:block; font-size:24px; color:#f3d9a4; }
  .stat span { font-size:13px; color:#b8ae9c; }
  .label { font-size:13px; color:#b8ae9c; margin:6px 0; }
  .grid { display:grid; grid-template-columns:repeat(15, 1fr); gap:4px; margin-bottom:16px; }
  .cell { aspect-ratio:1; border-radius:4px; background:rgba(255,255,255,.07); }
  .cell.on { background:#c58b4e; }
  .cell.today { outline:1px solid #f3d9a4; }
  .day { margin:12px 0 4px; font-weight:bold; color:#f3d9a4; font-size:15px; }
  .entry { font-size:14px; line-height:1.7; padding-left:6px; overflow-wrap:anywhere; }
  .entry .t { color:#b8ae9c; margin-right:6px; }
  .empty { color:#b8ae9c; font-size:14px; padding:18px 0; text-align:center; }
  .list { max-height:250px; overflow-y:auto; padding-right:4px; }
  .actions { display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }
  button { font-family:inherit; font-size:13px; border-radius:18px; padding:7px 14px; cursor:pointer;
           background:rgba(255,255,255,.06); color:#e8e2d6; border:1px solid rgba(232,226,214,.35); }
  button.danger { color:#e6a9a0; border-color:rgba(230,169,160,.4); }
</style>
<div class="stats">
  <div class="stat"><b id="streak">0</b><span>연속 수행일</span></div>
  <div class="stat"><b id="days">0</b><span>모든 수행일</span></div>
  <div class="stat"><b id="mins">0</b><span>명상한 시간(분)</span></div>
</div>
<div class="label">최근 30일 · 수행한 날은 금빛으로 밝혀져요</div>
<div class="grid" id="grid"></div>
<div class="list" id="list"></div>
<div class="actions">
  <button id="dl">📥 수행일지 내려받기</button>
  <button id="clear" class="danger">🗑 기록 모두 지우기</button>
</div>
<script>
__STORE_JS__
const ICON = { meditation: '🧘', offering: '🕯️', chant: '📿' };
const $ = id => document.getElementById(id);
let lastRaw = null;
function shift(dateStr, days) {
  const d = new Date(dateStr + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}
function render(force) {
  let raw = null;
  try { raw = localStorage.getItem(SANSA_KEY); } catch (e) {}
  const today = kstNow().date;
  if (!force && raw === lastRaw + today) return;   // 바뀐 게 없으면 다시 그리지 않음
  lastRaw = raw + today;
  const log = loadLog();
  const dates = new Set(log.map(e => e.date));

  // 연속 수행일: 오늘(아직이면 어제)부터 거꾸로 하루씩 세기
  let d = dates.has(today) ? today : shift(today, -1), streak = 0;
  while (dates.has(d)) { streak++; d = shift(d, -1); }
  $('streak').textContent = streak;
  $('days').textContent = dates.size;
  $('mins').textContent = log.reduce((s, e) => s + (e.kind === 'meditation' ? (e.minutes || 0) : 0), 0);

  const grid = $('grid'); grid.innerHTML = '';
  for (let i = 29; i >= 0; i--) {
    const day = shift(today, -i), c = document.createElement('div');
    c.className = 'cell' + (dates.has(day) ? ' on' : '') + (i === 0 ? ' today' : '');
    c.title = day; grid.appendChild(c);
  }

  const list = $('list'); list.innerHTML = '';
  if (!log.length) {
    list.innerHTML = '<div class="empty">아직 기록이 없어요. 오늘의 첫 수행을 시작해 보세요. 🌱</div>';
    return;
  }
  const byDate = {};
  log.forEach(e => (byDate[e.date] = byDate[e.date] || []).push(e));
  Object.keys(byDate).sort().reverse().forEach(day => {
    const h = document.createElement('div');
    h.className = 'day'; h.textContent = day === today ? day + ' (오늘)' : day;
    list.appendChild(h);
    byDate[day].sort((a, b) => a.time.localeCompare(b.time)).forEach(e => {
      const row = document.createElement('div'), t = document.createElement('span');
      row.className = 'entry'; t.className = 't'; t.textContent = e.time;
      row.appendChild(t);
      row.appendChild(document.createTextNode((ICON[e.kind] || '·') + ' ' + e.text));
      list.appendChild(row);
    });
  });
}
$('dl').onclick = () => {
  const log = loadLog().slice().sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time));
  let out = '🪷 온라인 산사 수행일지\\n', last = '';
  log.forEach(e => {
    if (e.date !== last) { out += '\\n[' + e.date + ']\\n'; last = e.date; }
    out += e.time + '  ' + (ICON[e.kind] || '·') + ' ' + e.text + '\\n';
  });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([out], { type: 'text/plain;charset=utf-8' }));
  a.download = '수행일지_' + kstNow().date + '.txt';
  document.body.appendChild(a); a.click(); a.remove();
};
$('clear').onclick = () => {
  if (confirm('지금까지의 수행 기록을 모두 지울까요? 되돌릴 수 없어요.')) {
    try { localStorage.removeItem(SANSA_KEY); } catch (e) {}
    render(true);
  }
};
render(true);
// 명상을 마치거나 공양을 올리면 곧바로 반영
window.addEventListener('storage', e => { if (e.key === SANSA_KEY) render(true); });
setInterval(() => render(false), 2000);
</script>
""".replace("__STORE_JS__", STORE_JS)

with tab_log:
    st.subheader("📖 나의 수행 기록")
    # 날짜마다 같은 법문이 나오도록 날짜를 씨앗으로 사용
    teaching = random.Random(now.strftime("%Y%m%d")).choice(TEACHINGS)
    st.markdown(f"<div class='temple-card'>🍃 <b>오늘의 법문</b><br>{teaching}</div>", unsafe_allow_html=True)
    render_html(LOG_VIEW_HTML, height=560)
    st.caption(
        "※ 기록은 지금 쓰는 이 브라우저에만 저장되어 다른 사람은 볼 수 없어요. "
        "브라우저 기록을 지우거나 다른 기기로 들어오면 보이지 않으니, 가끔 수행일지를 내려받아 두세요."
    )


# ---------------------------------------------------------------
# 6. 새벽 알림 — 휴대폰/PC 달력에 매일 반복되는 새벽예불 일정 추가
# ---------------------------------------------------------------
def build_ics(start: datetime, duration_min: int, remind_before: int) -> str:
    stamp = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Online Sansa//Dawn Practice//KO",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VTIMEZONE",
        "TZID:Asia/Seoul",
        "BEGIN:STANDARD",
        "DTSTART:19700101T000000",
        "TZOFFSETFROM:+0900",
        "TZOFFSETTO:+0900",
        "TZNAME:KST",
        "END:STANDARD",
        "END:VTIMEZONE",
        "BEGIN:VEVENT",
        f"UID:online-sansa-dawn-{uuid.uuid4().hex}",
        f"DTSTAMP:{stamp}",
        f"DTSTART;TZID=Asia/Seoul:{start.strftime('%Y%m%dT%H%M00')}",
        f"DURATION:PT{duration_min}M",
        "RRULE:FREQ=DAILY",
        "SUMMARY:🔔 새벽예불 · 온라인 산사",
        "DESCRIPTION:온라인 산사에 들어가 예불문과 명상으로 하루를 여는 시간입니다. 🪷",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:🔔 새벽예불 시간이에요",
        f"TRIGGER:-PT{remind_before}M" if remind_before else "TRIGGER:PT0M",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"


with tab_alarm:
    st.subheader("🔔 매일 새벽예불 알림 받기")
    st.markdown(
        "<p class='quiet'>원하는 시각을 고르고 알림 파일을 내려받아 열면, 휴대폰이나 컴퓨터 달력에 "
        "‘매일 반복되는 새벽예불 일정’이 추가돼요. 이 페이지를 열어 두지 않아도 달력 앱이 알려 줍니다.</p>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        alarm_time = st.time_input("예불 시각 (한국 시간)", value=datetime(2000, 1, 1, 4, 30).time(), step=300)
        practice_len = st.select_slider("수행 시간 (분)", options=[10, 15, 20, 30, 45, 60], value=30)
    with c2:
        remind = st.radio("알림", ["정시에", "5분 전", "10분 전"], index=0)

    remind_before = {"정시에": 0, "5분 전": 5, "10분 전": 10}[remind]

    first = now.replace(hour=alarm_time.hour, minute=alarm_time.minute, second=0, microsecond=0)
    if first <= now:
        first += timedelta(days=1)

    st.markdown(
        f"<div class='temple-card'>📅 <b>{first.strftime('%m월 %d일')}</b>부터 매일 "
        f"<b>{alarm_time.strftime('%H:%M')}</b>, {practice_len}분 동안 · 알림 {remind}</div>",
        unsafe_allow_html=True,
    )

    st.download_button(
        "📅 달력에 새벽예불 추가하기 (.ics)",
        data=build_ics(first, practice_len, remind_before).encode("utf-8"),
        file_name=f"새벽예불_{alarm_time.strftime('%H%M')}.ics",
        mime="text/calendar",
        type="primary",
    )

    with st.expander("알림 파일은 어떻게 여나요?"):
        st.markdown(
            "- **아이폰**: 내려받은 파일을 누르면 ‘모두 추가’가 떠요. 누르면 캘린더에 들어가요.\n"
            "- **안드로이드**: 파일을 누르고 ‘Google 캘린더’ 또는 ‘삼성 캘린더’로 열어 저장하세요.\n"
            "- **컴퓨터**: Google 캘린더 → 설정 → 가져오기에서 파일을 올리거나, "
            "Outlook·macOS 캘린더에서 파일을 바로 여세요.\n"
            "- 시각을 바꾸고 싶다면 달력에서 기존 일정을 지우고 새 파일을 다시 추가하면 돼요."
        )
