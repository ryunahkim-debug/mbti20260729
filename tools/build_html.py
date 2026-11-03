"""온라인 산사를 서버 없이 열리는 HTML 파일 한 개로 만든다.

    python tools/build_html.py          # → sansa.html

경전 본문, 명상 음악, 수행 기록 화면 같은 내용은 웹앱(pages/온라인 산사.py)에서
그대로 가져온다. 그래서 웹앱을 고친 뒤 이 스크립트를 다시 돌리면 HTML도 똑같이 바뀐다.
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "pages" / "온라인 산사.py"
OUT = ROOT / "sansa.html"

NEEDED = {
    "STORE_JS", "MEDITATION_TEMPLATE", "OFFERINGS", "YEBULMUN", "CHEONSUGYEONG",
    "HEART_SUTRA", "SUTRAS", "TEACHINGS", "LOG_VIEW_HTML",
}


def load_constants() -> dict:
    """웹앱 파일에서 필요한 상수만 골라 계산한다 (Streamlit을 실행하지 않음)."""
    tree = ast.parse(PAGE.read_text(encoding="utf-8"))
    body = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id in NEEDED for t in node.targets)
    ]
    namespace: dict = {}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(PAGE), "exec"), namespace)
    missing = NEEDED - namespace.keys()
    if missing:
        raise SystemExit(f"웹앱에서 찾지 못한 값: {sorted(missing)}")
    return namespace


def build() -> str:
    c = load_constants()
    data = {
        "medTemplate": c["MEDITATION_TEMPLATE"].replace("__STORE_JS__", c["STORE_JS"]),
        "logView": c["LOG_VIEW_HTML"],
        "offerings": [{"name": k, "meaning": v} for k, v in c["OFFERINGS"].items()],
        "sutras": [{"name": k, "html": v[0], "intro": v[1]} for k, v in c["SUTRAS"].items()],
        "teachings": c["TEACHINGS"],
    }
    data_js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return (
        TEMPLATE.replace("__DATA__", data_js)
        .replace("__STORE_JS__", c["STORE_JS"])
    )


TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>새벽 산사</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🪷</text></svg>">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700&display=swap">
<style>
  :root {
    --ink: #e8e2d6; --quiet: #b8ae9c; --gold: #f3d9a4; --amber: #c58b4e; --night: #1c2536;
    --line: rgba(232, 226, 214, .15); --line-strong: rgba(232, 226, 214, .35); --glass: rgba(255, 255, 255, .05);
  }
  * { box-sizing: border-box; }
  html { background: #0f1724; }
  body {
    margin: 0; min-height: 100vh; color: var(--ink);
    font-family: 'Nanum Myeongjo', 'AppleMyungjo', 'Batang', serif;
    background: linear-gradient(180deg, #0f1724 0%, #1c2536 45%, #3a3346 80%, #5b4a4a 100%) fixed;
  }
  main { max-width: 700px; margin: 0 auto; padding: 40px 16px 72px; }
  h1 { font-size: 2.3rem; margin: 0 0 6px; }
  h2 { font-size: 1.45rem; margin: 22px 0 8px; }
  p { line-height: 1.8; }
  .quiet { color: var(--quiet); font-size: .93rem; }
  .card { background: var(--glass); border: 1px solid var(--line); border-radius: 14px;
          padding: 1.05rem 1.25rem; margin: .7rem 0 1rem; line-height: 1.9; }
  .tabs { display: flex; gap: 2px; overflow-x: auto; border-bottom: 1px solid var(--line); margin-top: 18px; }
  .tabs button { background: none; border: none; border-bottom: 2px solid transparent; color: var(--quiet);
                 padding: 10px 12px; font: inherit; font-size: .98rem; cursor: pointer; white-space: nowrap; }
  @media (max-width: 480px) { .tabs button { padding: 10px 7px; font-size: .9rem; flex: 1 0 auto; } }
  .tabs button[aria-selected="true"] { color: var(--ink); border-bottom-color: var(--amber); }
  .panel[hidden] { display: none; }
  .controls { display: flex; flex-wrap: wrap; gap: 14px 22px; align-items: center; margin: 10px 0 6px; }
  label { cursor: pointer; }
  select, input[type=time], textarea {
    font: inherit; font-size: .95rem; color: var(--ink); background: var(--night);
    border: 1px solid var(--line-strong); border-radius: 8px; padding: 6px 9px;
  }
  textarea { width: 100%; min-height: 110px; resize: vertical; line-height: 1.7; }
  input[type=checkbox], input[type=radio] { accent-color: var(--amber); }
  .btn { font: inherit; font-size: .98rem; border-radius: 22px; padding: 9px 22px; cursor: pointer;
         background: var(--amber); color: var(--night); border: none; }
  .btn:disabled { opacity: .45; cursor: not-allowed; }
  .btn.ghost { background: rgba(255, 255, 255, .06); color: var(--ink); border: 1px solid var(--line-strong); }
  .offer-list { list-style: none; padding: 0; margin: 8px 0 14px; }
  .offer-list li { padding: 5px 0; }
  .offer-list span { color: var(--quiet); font-size: .9rem; }
  .result { text-align: center; }
  .result .icons { font-size: 2.4rem; letter-spacing: .3em; }
  .sutra { text-align: center; font-size: 1.05rem; line-height: 2.2; letter-spacing: .04em; }
  .sutra h4 { color: var(--gold); margin: 1.4rem 0 .4rem; font-size: 1.05rem; }
  .note { color: var(--quiet); font-size: .85rem; }
  .ok { color: var(--gold); margin-left: 10px; }
  iframe { width: 100%; border: 0; display: block; background: transparent; }
  details { margin-top: 14px; }
  summary { cursor: pointer; color: var(--quiet); }
  details ul { line-height: 1.9; }
</style>
</head>
<body>
<main>
  <h1>🪷 새벽 산사</h1>
  <div class="quiet" id="clock"></div>
  <div class="card" id="moment"></div>

  <nav class="tabs" role="tablist">
    <button role="tab" data-tab="med" aria-selected="true">🧘 명상</button>
    <button role="tab" data-tab="offer" aria-selected="false">🕯️ 불공</button>
    <button role="tab" data-tab="chant" aria-selected="false">📿 독경</button>
    <button role="tab" data-tab="log" aria-selected="false">📖 기록</button>
    <button role="tab" data-tab="alarm" aria-selected="false">🔔 알림</button>
  </nav>

  <!-- 🧘 명상 -->
  <section class="panel" id="p-med">
    <h2>🧘 고요히 앉기</h2>
    <p class="quiet">허리를 곧게 펴고 편히 앉으세요. 시작하면 종이 세 번 울리고, 시간이 다 되면 다시 종이 울립니다.
      원이 커질 때 들이쉬고, 작아질 때 내쉬어요. 명상 음악을 고르면 종소리 뒤에 음악이 서서히 피어나고,
      끝날 때 함께 잦아들어요. 앉은 시간은 수행 기록에 저절로 남아요.</p>
    <div class="controls">
      <label>명상 시간
        <select id="minutes">
          <option>3</option><option>5</option><option selected>10</option><option>15</option>
          <option>20</option><option>30</option><option>45</option><option>60</option>
        </select> 분</label>
      <label><input type="checkbox" id="moktak" checked> 시작 전 목탁 소리</label>
    </div>
    <iframe id="medFrame" title="명상 타이머" style="height:420px"></iframe>
  </section>

  <!-- 🕯️ 불공 -->
  <section class="panel" id="p-offer" hidden>
    <h2>🕯️ 부처님 전에 공양 올리기</h2>
    <p class="quiet">예로부터 부처님께 올리는 여섯 가지 공양(육법공양)이 있어요.
      마음 가는 공양을 고르고, 조용히 발원을 적어 보세요.</p>
    <ul class="offer-list" id="offerList"></ul>
    <label for="wish">발원문 (마음속 바람을 적어 주세요)</label>
    <textarea id="wish" placeholder="예) 가족 모두 건강하고, 제가 오늘 하루 화내지 않고 따뜻한 말을 하게 하소서."></textarea>
    <p><button class="btn" id="offerBtn">🙇 삼배 올리고 공양하기</button></p>
    <div id="offerResult"></div>
  </section>

  <!-- 📿 독경 -->
  <section class="panel" id="p-chant" hidden>
    <h2>📿 독경</h2>
    <p class="quiet">새벽에는 예불문 → 천수경 → 반야심경 순서로 읽으면 좋아요. 소리 내어 천천히, 한 구절씩.
      뜻을 몰라도 괜찮아요. 읽는 동안 마음이 한곳에 머무는 것, 그것이 독경입니다.</p>
    <div class="controls" id="sutraPicker" role="radiogroup" aria-label="오늘 읽을 경전"></div>
    <p class="quiet" id="sutraIntro"></p>
    <div class="card sutra" id="sutraText"></div>
    <p class="note">※ 사찰과 경본에 따라 표기가 조금씩 다를 수 있어요. 다니시는 절의 경본을 따라 주세요.</p>
    <p><button class="btn ghost" id="chantBtn"></button><span class="ok" id="chantMsg"></span></p>
  </section>

  <!-- 📖 기록 -->
  <section class="panel" id="p-log" hidden>
    <h2>📖 나의 수행 기록</h2>
    <div class="card">🍃 <b>오늘의 법문</b><br><span id="teaching"></span></div>
    <iframe id="logFrame" title="수행 기록" style="height:560px"></iframe>
    <p class="note">※ 기록은 이 브라우저에만 저장되어 다른 사람은 볼 수 없어요. 브라우저 기록을 지우면 함께 사라지니,
      가끔 수행일지를 내려받아 두세요.</p>
  </section>

  <!-- 🔔 알림 -->
  <section class="panel" id="p-alarm" hidden>
    <h2>🔔 매일 새벽예불 알림 받기</h2>
    <p class="quiet">원하는 시각을 고르고 알림 파일을 내려받아 열면, 휴대폰이나 컴퓨터 달력에
      ‘매일 반복되는 새벽예불 일정’이 추가돼요. 이 파일을 열어 두지 않아도 달력 앱이 알려 줍니다.</p>
    <div class="controls">
      <label>예불 시각 (한국 시간) <input type="time" id="alarmTime" value="04:30" step="300"></label>
      <label>수행 시간
        <select id="alarmLen">
          <option>10</option><option>15</option><option>20</option><option selected>30</option>
          <option>45</option><option>60</option>
        </select> 분</label>
      <label>알림
        <select id="alarmRemind">
          <option value="0" selected>정시에</option><option value="5">5분 전</option><option value="10">10분 전</option>
        </select></label>
    </div>
    <div class="card" id="alarmSummary"></div>
    <button class="btn" id="icsBtn">📅 달력에 새벽예불 추가하기 (.ics)</button>
    <details>
      <summary>알림 파일은 어떻게 여나요?</summary>
      <ul>
        <li><b>아이폰</b>: 내려받은 파일을 누르면 ‘모두 추가’가 떠요. 누르면 캘린더에 들어가요.</li>
        <li><b>안드로이드</b>: 파일을 누르고 ‘Google 캘린더’ 또는 ‘삼성 캘린더’로 열어 저장하세요.</li>
        <li><b>컴퓨터</b>: Google 캘린더 → 설정 → 가져오기에서 파일을 올리거나, Outlook·macOS 캘린더에서 파일을 바로 여세요.</li>
        <li>시각을 바꾸고 싶다면 달력에서 기존 일정을 지우고 새 파일을 다시 추가하면 돼요.</li>
      </ul>
    </details>
  </section>
</main>

<script>
const DATA = __DATA__;
__STORE_JS__
const $ = id => document.getElementById(id);

// ---- 탭 ----
document.querySelectorAll('.tabs button').forEach(tab => {
  tab.onclick = () => {
    document.querySelectorAll('.tabs button').forEach(t => t.setAttribute('aria-selected', t === tab));
    document.querySelectorAll('.panel').forEach(p => p.hidden = p.id !== 'p-' + tab.dataset.tab);
  };
});

// ---- 지금 산사의 시간 ----
function kstHour() {
  return Number(new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Seoul', hour: 'numeric', hour12: false })
    .format(new Date())) % 24;
}
function updateClock() {
  const t = kstNow(), [y, m, d] = t.date.split('-'), h = kstHour();
  $('clock').textContent = `${y}년 ${m}월 ${d}일 ${t.time} · 한국 시간`;
  $('moment').textContent =
    h >= 3 && h < 4 ? '🌌 도량석(道場釋) 시간이에요. 목탁 소리로 도량을 깨우며 하루를 엽니다.' :
    h >= 4 && h < 6 ? '🔔 새벽예불 시간이에요. 범종이 울리고, 고요히 마음을 모아 봅니다.' :
    h >= 6 && h < 9 ? '🌅 동이 트는 아침이에요. 맑은 공기 속에서 하루의 발원을 세워 보세요.' :
    h >= 9 && h < 18 ? '☀️ 낮의 산사예요. 바쁜 와중에도 숨 한 번, 잠시 멈춰 봅니다.' :
    h >= 18 && h < 21 ? '🌆 저녁예불 시간이에요. 오늘 하루를 돌아보며 감사함을 올립니다.' :
    '🌙 산사는 잠든 밤이에요. 내일 새벽을 위해 편히 쉬어 가세요.';
}
updateClock(); setInterval(updateClock, 30000);

// ---- 🧘 명상 (웹앱과 같은 타이머·음악을 iframe에 담음) ----
function loadMeditation() {
  const min = $('minutes').value;
  $('medFrame').srcdoc = DATA.medTemplate
    .replaceAll('__MINUTES_PAD__', String(min).padStart(2, '0'))
    .replaceAll('__MINUTES__', min)
    .replaceAll('__MOKTAK__', String($('moktak').checked));
}
try {
  const saved = JSON.parse(localStorage.getItem('online_sansa_timer') || '{}');
  if (saved.minutes) $('minutes').value = saved.minutes;
  if (typeof saved.moktak === 'boolean') $('moktak').checked = saved.moktak;
} catch (e) {}
['minutes', 'moktak'].forEach(id => $(id).onchange = () => {
  try { localStorage.setItem('online_sansa_timer', JSON.stringify({ minutes: $('minutes').value, moktak: $('moktak').checked })); } catch (e) {}
  loadMeditation();
});
loadMeditation();

// ---- 🕯️ 불공 ----
DATA.offerings.forEach((o, i) => {
  const li = document.createElement('li');
  li.innerHTML = `<label><input type="checkbox" value="${i}" ${i < 2 ? 'checked' : ''}> <b></b> — <span></span></label>`;
  li.querySelector('b').textContent = o.name;
  li.querySelector('span').textContent = o.meaning;
  $('offerList').appendChild(li);
});
function chosenOfferings() {
  return [...document.querySelectorAll('#offerList input:checked')].map(c => DATA.offerings[c.value].name);
}
$('offerList').onchange = () => { $('offerBtn').disabled = chosenOfferings().length === 0; };
$('offerBtn').onclick = () => {
  const icons = chosenOfferings().map(n => n.split(' ')[0]).join(' ');
  const wish = $('wish').value.trim();
  const box = $('offerResult');
  box.innerHTML = `<div class="card result"><div class="icons"></div><p>🙇 🙇 🙇</p>
    <p>정성스러운 공양이 부처님 전에 올려졌습니다.</p>
    <p class="quiet">나무 석가모니불 · 나무 석가모니불 · 나무 시아본사 석가모니불</p></div>`;
  box.querySelector('.icons').textContent = icons;
  if (wish) {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = '<b>📜 발원</b><br><span style="white-space:pre-wrap"></span>';
    card.querySelector('span').textContent = wish;
    box.appendChild(card);
  }
  saveEntry({ id: 'off-' + Date.now(), kind: 'offering', minutes: 0,
              text: `공양 (${icons})` + (wish ? ' — ' + wish : '') });
};

// ---- 📿 독경 ----
let sutraIndex = 0;
DATA.sutras.forEach((s, i) => {
  const label = document.createElement('label');
  label.innerHTML = `<input type="radio" name="sutra" value="${i}" ${i === 0 ? 'checked' : ''}> <span></span>`;
  label.querySelector('span').textContent = s.name;
  $('sutraPicker').appendChild(label);
});
function showSutra() {
  const s = DATA.sutras[sutraIndex], plain = s.name.split(' ').slice(1).join(' ');
  $('sutraIntro').textContent = s.intro;
  $('sutraText').innerHTML = s.html;   // 이 파일 안에 담긴 경전 본문(신뢰할 수 있는 내용)
  $('chantBtn').textContent = `📿 ${plain} 독송을 마쳤어요`;
  $('chantMsg').textContent = '';
}
$('sutraPicker').onchange = e => { sutraIndex = Number(e.target.value); showSutra(); };
$('chantBtn').onclick = () => {
  const plain = DATA.sutras[sutraIndex].name.split(' ').slice(1).join(' ');
  saveEntry({ id: 'chant-' + Date.now(), kind: 'chant', minutes: 0, text: plain + ' 독송' });
  $('chantMsg').textContent = '수희찬탄합니다. 🙏 수행 기록에 남겼어요.';
};
showSutra();

// ---- 📖 기록 ----
(() => {
  const today = kstNow().date;
  let h = 0;
  for (const ch of today) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  $('teaching').textContent = DATA.teachings[h % DATA.teachings.length];
})();
$('logFrame').srcdoc = DATA.logView;

// ---- 🔔 알림 (.ics 달력 파일) ----
function addDays(dateStr, n) {
  const d = new Date(dateStr + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
function firstAlarmDate() {
  const now = kstNow(), at = $('alarmTime').value || '04:30';
  return at > now.time ? now.date : addDays(now.date, 1);
}
function updateAlarm() {
  const [, m, d] = firstAlarmDate().split('-');
  const remind = $('alarmRemind').selectedOptions[0].textContent;
  $('alarmSummary').innerHTML = `📅 <b>${m}월 ${d}일</b>부터 매일 <b>${$('alarmTime').value}</b>, `
    + `${$('alarmLen').value}분 동안 · 알림 ${remind}`;
}
['alarmTime', 'alarmLen', 'alarmRemind'].forEach(id => $(id).oninput = updateAlarm);
updateAlarm();
$('icsBtn').onclick = () => {
  const at = $('alarmTime').value || '04:30', before = Number($('alarmRemind').value);
  const start = firstAlarmDate().replaceAll('-', '') + 'T' + at.replace(':', '') + '00';
  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, '');
  const uid = 'online-sansa-dawn-' + Date.now().toString(16) + Math.random().toString(16).slice(2);
  const ics = [
    'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Online Sansa//Dawn Practice//KO', 'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH', 'BEGIN:VTIMEZONE', 'TZID:Asia/Seoul', 'BEGIN:STANDARD', 'DTSTART:19700101T000000',
    'TZOFFSETFROM:+0900', 'TZOFFSETTO:+0900', 'TZNAME:KST', 'END:STANDARD', 'END:VTIMEZONE',
    'BEGIN:VEVENT', 'UID:' + uid, 'DTSTAMP:' + stamp, 'DTSTART;TZID=Asia/Seoul:' + start,
    'DURATION:PT' + $('alarmLen').value + 'M', 'RRULE:FREQ=DAILY', 'SUMMARY:🔔 새벽예불 · 온라인 산사',
    'DESCRIPTION:온라인 산사에 들어가 예불문과 명상으로 하루를 여는 시간입니다. 🪷',
    'BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:🔔 새벽예불 시간이에요',
    before ? 'TRIGGER:-PT' + before + 'M' : 'TRIGGER:PT0M', 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR',
  ].join('\r\n') + '\r\n';
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([ics], { type: 'text/calendar;charset=utf-8' }));
  a.download = 'sansa-dawn_' + at.replace(':', '') + '.ics';
  document.body.appendChild(a); a.click(); a.remove();
};
</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"만들었어요: {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")
