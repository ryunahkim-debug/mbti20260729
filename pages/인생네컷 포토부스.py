import base64
import io
import os
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont, ImageOps

st.set_page_config(page_title="인생네컷 포토부스", page_icon="📸", layout="centered")

# ---------------------------------------------------------------------------
# 설정값
# ---------------------------------------------------------------------------
DPI = 300                      # 사진 인화 해상도
SHEET_W, SHEET_H = 1200, 1800  # 4x6 inch (300dpi) 인화지 한 장
SHOTS = 4                      # 네 컷

THEMES = {
    "클래식 블랙 🖤": {"bg": "#111111", "text": "#FFFFFF", "accent": "#FFD84D"},
    "깔끔 화이트 🤍": {"bg": "#FFFFFF", "text": "#222222", "accent": "#FF7AA2"},
    "러블리 핑크 🩷": {"bg": "#FFC8DD", "text": "#7A1F45", "accent": "#FFFFFF"},
    "하늘 블루 🩵": {"bg": "#BDE0FE", "text": "#1D3557", "accent": "#FFFFFF"},
    "민트 초코 🍃": {"bg": "#B9F3E4", "text": "#3E2723", "accent": "#6D4C41"},
    "직접 고르기 🎨": None,
}

FONT_CANDIDATES = [
    # Linux / Streamlit Cloud (packages.txt 의 fonts-nanum)
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    # Windows
    "C:/Windows/Fonts/malgunbd.ttf",
    "C:/Windows/Fonts/malgun.ttf",
    # macOS
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/AppleGothic.ttf",
]


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


@st.cache_resource
def find_font_path():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def get_font(size: int):
    path = find_font_path()
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def draw_center_text(draw, text, cx, y, font, fill):
    if not text:
        return
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def fit_font(draw, text, max_w, start_size, min_size=18):
    size = start_size
    while size > min_size:
        f = get_font(size)
        b = draw.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= max_w:
            return f
        size -= 2
    return get_font(min_size)


def draw_sparkles(draw, w, h, color, area_top, area_bottom):
    """프레임 하단에 작은 별/점 장식"""
    import random

    rnd = random.Random(42)
    side = max(40, w // 12)  # 글자와 겹치지 않도록 좌우 가장자리에만
    for i in range(14):
        x = rnd.randint(12, side) if i % 2 == 0 else rnd.randint(w - side, w - 12)
        y = rnd.randint(area_top, area_bottom)
        r = rnd.choice([3, 4, 6])
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def make_strip(photos, theme, title, subtitle, show_date, mirror):
    """세로형 1x4 스트립 (2x6 inch = 600x1800 px)"""
    W, H = SHEET_W // 2, SHEET_H
    margin, gap, footer = 30, 18, 230
    cell_w = W - margin * 2
    cell_h = (H - margin - footer - gap * (SHOTS - 1)) // SHOTS

    img = Image.new("RGB", (W, H), hex_to_rgb(theme["bg"]))
    draw = ImageDraw.Draw(img)

    for i, p in enumerate(photos):
        ph = ImageOps.fit(p, (cell_w, cell_h), method=Image.LANCZOS, centering=(0.5, 0.45))
        if mirror:
            ph = ImageOps.mirror(ph)
        y = margin + i * (cell_h + gap)
        img.paste(ph, (margin, y))

    foot_top = margin + SHOTS * cell_h + (SHOTS - 1) * gap
    draw_sparkles(draw, W, H, hex_to_rgb(theme["accent"]), foot_top + 15, H - 15)
    tf = fit_font(draw, title, W - 60, 64)
    draw_center_text(draw, title, W / 2, foot_top + 45, tf, hex_to_rgb(theme["text"]))
    sf = fit_font(draw, subtitle, W - 60, 34)
    draw_center_text(draw, subtitle, W / 2, foot_top + 125, sf, hex_to_rgb(theme["text"]))
    if show_date:
        df = get_font(26)
        draw_center_text(draw, datetime.now().strftime("%Y.%m.%d"), W / 2, foot_top + 172,
                         df, hex_to_rgb(theme["text"]))
    return img


def make_grid(photos, theme, title, subtitle, show_date, mirror):
    """2x2 격자형 (4x6 inch = 1200x1800 px)"""
    W, H = SHEET_W, SHEET_H
    margin, gap, footer = 50, 26, 330
    cell_w = (W - margin * 2 - gap) // 2
    cell_h = (H - margin - footer - gap) // 2

    img = Image.new("RGB", (W, H), hex_to_rgb(theme["bg"]))
    draw = ImageDraw.Draw(img)
    for i, p in enumerate(photos):
        ph = ImageOps.fit(p, (cell_w, cell_h), method=Image.LANCZOS, centering=(0.5, 0.45))
        if mirror:
            ph = ImageOps.mirror(ph)
        r, c = divmod(i, 2)
        img.paste(ph, (margin + c * (cell_w + gap), margin + r * (cell_h + gap)))

    foot_top = margin + 2 * cell_h + gap
    draw_sparkles(draw, W, H, hex_to_rgb(theme["accent"]), foot_top + 20, H - 20)
    tf = fit_font(draw, title, W - 100, 96)
    draw_center_text(draw, title, W / 2, foot_top + 55, tf, hex_to_rgb(theme["text"]))
    sf = fit_font(draw, subtitle, W - 100, 48)
    draw_center_text(draw, subtitle, W / 2, foot_top + 175, sf, hex_to_rgb(theme["text"]))
    if show_date:
        draw_center_text(draw, datetime.now().strftime("%Y.%m.%d"), W / 2, foot_top + 245,
                         get_font(36), hex_to_rgb(theme["text"]))
    return img


def make_print_sheet(frame_img, layout):
    """인화용 4x6 시트. 스트립은 두 장을 나란히 붙여 가운데를 자르면 2장이 나온다."""
    if layout == "strip":
        sheet = Image.new("RGB", (SHEET_W, SHEET_H), "white")
        sheet.paste(frame_img, (0, 0))
        sheet.paste(frame_img, (SHEET_W // 2, 0))
        return sheet
    return frame_img


def to_bytes(img, fmt):
    buf = io.BytesIO()
    if fmt == "PDF":
        img.save(buf, format="PDF", resolution=DPI)
    elif fmt == "JPEG":
        img.save(buf, format="JPEG", quality=95, dpi=(DPI, DPI))
    else:
        img.save(buf, format="PNG", dpi=(DPI, DPI))
    return buf.getvalue()


def load_photo(file):
    img = Image.open(file)
    img = ImageOps.exif_transpose(img)  # 휴대폰 사진 회전 정보 반영
    return img.convert("RGB")


# ---------------------------------------------------------------------------
# 프린터 연동 (앱이 실행 중인 컴퓨터에 연결된 프린터로 바로 출력)
# ---------------------------------------------------------------------------
def list_server_printers():
    system = platform.system()
    if system == "Windows":
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-Printer | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, timeout=10,
            )
            return [l.strip() for l in out.stdout.splitlines() if l.strip()]
        except Exception:
            return []
    if shutil.which("lpstat"):
        try:
            out = subprocess.run(["lpstat", "-e"], capture_output=True, text=True, timeout=10)
            return [l.strip() for l in out.stdout.splitlines() if l.strip()]
        except Exception:
            return []
    return []


def print_on_server(sheet, printer, copies):
    safe_printer = printer.replace("'", "''")  # PowerShell 문자열 이스케이프
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    sheet.save(tmp, format="JPEG", quality=95, dpi=(DPI, DPI))
    tmp.close()
    system = platform.system()
    if system == "Windows":
        # Windows 기본 '사진 인쇄' 동작 사용 (선택한 프린터를 기본 프린터로 잠시 지정)
        ps = (
            f"$p = Get-CimInstance Win32_Printer | Where-Object {{$_.Name -eq '{safe_printer}'}}; "
            f"Invoke-CimMethod -InputObject $p -MethodName SetDefaultPrinter | Out-Null; "
            f"1..{copies} | ForEach-Object {{ Start-Process -FilePath '{tmp.name}' -Verb Print }}"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=60)
        return f"'{printer}' 프린터로 {copies}장 출력 요청을 보냈어요."
    cmd = ["lp", "-d", printer, "-n", str(copies),
           "-o", "media=4x6", "-o", "fit-to-page", tmp.name]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(out.stderr or out.stdout)
    return out.stdout.strip() or "출력 요청 완료!"


def browser_print_button(sheet):
    """휴대폰/PC 브라우저의 인쇄 기능(AirPrint, Mopria 등)으로 4x6 인화"""
    b64 = base64.b64encode(to_bytes(sheet, "JPEG")).decode()
    html = (
        f"""
        <style>
          @page {{ size: 4in 6in; margin: 0; }}
          body {{ margin: 0; font-family: sans-serif; }}
          #sheet {{ display: none; }}
          button {{ width: 100%; padding: 14px; font-size: 17px; border: 0; border-radius: 10px;
                   background: #ff4b6e; color: white; font-weight: bold; cursor: pointer; }}
          @media print {{
            button {{ display: none; }}
            #sheet {{ display: block; width: 4in; height: 6in; }}
          }}
        </style>
        <button onclick="window.print()">🖨️ 이 기기에서 바로 인쇄하기 (4x6 인화지)</button>
        <img id="sheet" src="data:image/jpeg;base64,{b64}">
        """
    )
    if hasattr(st, "iframe"):          # 최신 Streamlit
        st.iframe(html, height=60)
    else:                              # 구버전 호환
        components.html(html, height=60)


# ---------------------------------------------------------------------------
# 화면
# ---------------------------------------------------------------------------
st.title("📸 인생네컷 포토부스")
st.markdown(
    "휴대폰으로 사진 **4장**을 찍으면 예쁜 프레임에 쏙 들어가! "
    "완성되면 바로 **사진 출력기**로 인쇄할 수 있어. ✨"
)

if "photos" not in st.session_state:
    st.session_state.photos = []
if "shot_id" not in st.session_state:
    st.session_state.shot_id = 0

photos = st.session_state.photos

# --- 1. 프레임 꾸미기 -------------------------------------------------------
with st.expander("🎨 1단계: 프레임 꾸미기", expanded=not photos):
    c1, c2 = st.columns(2)
    with c1:
        layout_label = st.radio("레이아웃", ["세로 네컷 (1x4)", "격자 네컷 (2x2)"], horizontal=False)
        theme_name = st.selectbox("프레임 색상", list(THEMES.keys()))
    with c2:
        title = st.text_input("프레임 제목", value="LIFE 4 CUTS")
        subtitle = st.text_input("한 줄 문구", value="우리 MBTI 찰떡 케미", help="이모지는 인쇄 글꼴에서 깨질 수 있어요.")
        show_date = st.checkbox("날짜 넣기", value=True)
        mirror = st.checkbox("좌우 반전 (거울 모드)", value=False)
    if THEMES[theme_name] is None:
        cc1, cc2, cc3 = st.columns(3)
        theme = {
            "bg": cc1.color_picker("배경색", "#FFE5EC"),
            "text": cc2.color_picker("글자색", "#333333"),
            "accent": cc3.color_picker("포인트색", "#FF4B6E"),
        }
    else:
        theme = THEMES[theme_name]

layout = "strip" if "1x4" in layout_label else "grid"

# --- 2. 촬영 ---------------------------------------------------------------
st.subheader(f"📷 2단계: 사진 찍기 ({len(photos)}/{SHOTS})")
st.progress(len(photos) / SHOTS)

if len(photos) < SHOTS:
    mode = st.radio(
        "촬영 방법",
        ["휴대폰 카메라로 찍기 (추천)", "웹 카메라 화면으로 찍기"],
        horizontal=True,
        help="휴대폰 카메라 방식은 '사진 찍기'를 누르면 휴대폰 기본 카메라 앱이 열려서 화질이 가장 좋아요.",
    )
    key = f"shot_{st.session_state.shot_id}"
    new_file = None
    if mode.startswith("휴대폰"):
        new_file = st.file_uploader(
            f"{len(photos) + 1}번째 사진 — 눌러서 '사진 찍기' 선택 (여러 장 한 번에 선택도 가능)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key=key,
        )
    else:
        cam = st.camera_input(f"{len(photos) + 1}번째 컷! 포즈 잡고 찰칵 📸", key=key)
        new_file = [cam] if cam else None

    if new_file:
        for f in new_file:
            if len(st.session_state.photos) >= SHOTS:
                break
            try:
                st.session_state.photos.append(load_photo(f))
            except Exception:
                st.error(f"'{getattr(f, 'name', '사진')}' 파일을 열 수 없어요. JPG/PNG로 다시 시도해 줘!")
        st.session_state.shot_id += 1  # 위젯을 비워서 다음 컷을 찍을 수 있게
        st.rerun()

if photos:
    cols = st.columns(SHOTS)
    for i in range(SHOTS):
        with cols[i]:
            if i < len(photos):
                st.image(photos[i], caption=f"{i + 1}컷", width="stretch")
                if st.button("🗑️ 지우기", key=f"del_{i}", width="stretch"):
                    st.session_state.photos.pop(i)
                    st.session_state.shot_id += 1
                    st.rerun()
            else:
                st.markdown(f"<div style='text-align:center;padding:30px 0;border:2px dashed #ccc;"
                            f"border-radius:8px;color:#aaa'>{i + 1}컷</div>", unsafe_allow_html=True)
    if st.button("🔄 처음부터 다시 찍기"):
        st.session_state.photos = []
        st.session_state.shot_id += 1
        st.rerun()

# --- 3. 완성 & 출력 ---------------------------------------------------------
if len(photos) == SHOTS:
    st.markdown("---")
    st.subheader("🎉 3단계: 완성! 출력하기")

    maker = make_strip if layout == "strip" else make_grid
    frame = maker(photos, theme, title, subtitle, show_date, mirror)
    sheet = make_print_sheet(frame, layout)

    st.image(frame, caption="완성된 인생네컷", width=320 if layout == "strip" else 480)
    if layout == "strip":
        st.caption("✂️ 인화지(4x6)에는 같은 네컷이 2줄 나란히 인쇄돼요. 가운데를 자르면 친구랑 한 장씩!")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    d1, d2 = st.columns(2)
    d1.download_button("💾 사진 저장 (PNG)", to_bytes(frame, "PNG"),
                       file_name=f"인생네컷_{stamp}.png", mime="image/png", width="stretch")
    d2.download_button("📄 인화용 파일 (PDF 4x6)", to_bytes(sheet, "PDF"),
                       file_name=f"인생네컷_인화용_{stamp}.pdf", mime="application/pdf",
                       width="stretch")

    st.markdown("#### 🖨️ 사진 출력기로 인쇄")
    tab1, tab2 = st.tabs(["📱 휴대폰/브라우저에서 인쇄", "🖥️ 포토부스 PC 프린터로 출력"])

    with tab1:
        browser_print_button(sheet)
        st.info(
            "**휴대폰과 프린터가 같은 Wi-Fi**에 있으면 바로 인쇄돼요.\n\n"
            "- 아이폰: 인쇄 → **AirPrint** 프린터 선택\n"
            "- 안드로이드: 인쇄 → **Mopria / 기본 인쇄 서비스** 에서 프린터 선택\n"
            "- 용지 크기는 **4x6 (10x15cm)**, 여백 없음으로 설정해 줘!\n\n"
            "버튼이 안 되면 위의 **인화용 파일(PDF)** 을 받아서 프린터 전용 앱"
            "(예: Canon SELPHY, Epson Smart Panel, HP Smart)으로 열어 인쇄하면 돼요."
        )

    with tab2:
        printers = list_server_printers()
        if printers:
            pc1, pc2 = st.columns([3, 1])
            printer = pc1.selectbox("프린터 선택", printers)
            copies = pc2.number_input("매수", min_value=1, max_value=10, value=1)
            if st.button("🖨️ 지금 출력하기", type="primary", width="stretch"):
                try:
                    with st.spinner("프린터로 보내는 중..."):
                        msg = print_on_server(sheet, printer, int(copies))
                    st.success(f"✅ {msg}")
                    st.balloons()
                except Exception as e:
                    st.error(f"출력에 실패했어요: {e}")
        else:
            st.warning("이 앱이 실행 중인 컴퓨터에서 연결된 프린터를 찾지 못했어요.")
        st.caption(
            "포토부스처럼 쓰려면: 사진 프린터를 연결한 노트북에서 "
            "`streamlit run app.py --server.address 0.0.0.0` 로 앱을 실행하고, "
            "휴대폰에서 같은 Wi-Fi로 `http://노트북IP:8501` 에 접속하세요. "
            "이 탭의 버튼을 누르면 노트북에 연결된 프린터로 바로 출력됩니다."
        )
