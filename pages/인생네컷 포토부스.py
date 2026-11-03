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
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

st.set_page_config(page_title="인생네컷 포토부스", page_icon="📸", layout="centered")

# ---------------------------------------------------------------------------
# 설정값
# ---------------------------------------------------------------------------
DPI = 300                      # 사진 인화 해상도
SHEET_W, SHEET_H = 1200, 1800  # 4x6 inch (300dpi) 인화지 한 장
SHOTS = 4                      # 네 컷

# 색상 팔레트: bg(배경), bg2(보조 배경), ink(글자), accent(포인트)
PALETTES = {
    "블랙 🖤": {"bg": "#141414", "bg2": "#2B2B2B", "ink": "#FFFFFF", "accent": "#FFB648"},
    "화이트 🤍": {"bg": "#FAFAF7", "bg2": "#ECE9E2", "ink": "#1E1E1E", "accent": "#FF6F91"},
    "베이비 핑크 🩷": {"bg": "#FFD3E2", "bg2": "#FFF1F6", "ink": "#8A2C52", "accent": "#FF5C8A"},
    "스카이 블루 🩵": {"bg": "#C9E3FF", "bg2": "#F0F7FF", "ink": "#1F3A68", "accent": "#4D8DFF"},
    "버터 옐로 💛": {"bg": "#FFEFA8", "bg2": "#FFFAE3", "ink": "#6B4A00", "accent": "#FF9F1C"},
    "라벤더 💜": {"bg": "#DDD0FF", "bg2": "#F5F0FF", "ink": "#4B2E83", "accent": "#9B6BFF"},
    "민트 🍃": {"bg": "#C6F2E2", "bg2": "#EEFFF8", "ink": "#1F5A46", "accent": "#21B088"},
    "직접 고르기 🎨": None,
}

# 프레임 스타일
STYLES = {
    "베이직 ✨": "basic",
    "필름 🎞️": "film",
    "스티커 🎀": "sticker",
    "체크 패턴 🧺": "check",
    "미니멀 🤍": "minimal",
}

FONT_CANDIDATES = {
    "title": [
        # Linux / Streamlit Cloud (packages.txt 의 fonts-nanum)
        "/usr/share/fonts/truetype/nanum/NanumSquareRoundEB.ttf",
        "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf",
        "/usr/share/fonts/truetype/nanum/NanumSquareEB.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        # Windows / macOS
        "C:/Windows/Fonts/malgunbd.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ],
    "body": [
        "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf",
        "/usr/share/fonts/truetype/nanum/NanumSquareRoundR.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ],
    "mono": [  # 날짜 스탬프용 (숫자만 쓰므로 영문 글꼴)
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "C:/Windows/Fonts/consolab.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ],
}

K = 2  # 2배 크기로 그린 뒤 줄여서 테두리를 매끄럽게


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    """두 색을 t 비율(0~1)로 섞기"""
    a, b = hex_to_rgb(c1) if isinstance(c1, str) else c1, hex_to_rgb(c2) if isinstance(c2, str) else c2
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


@st.cache_resource
def find_font_path(role: str):
    for p in FONT_CANDIDATES[role]:
        if os.path.exists(p):
            return p
    if role == "mono":
        return find_font_path("body")
    if role == "title":
        return find_font_path("body")
    return None


def get_font(size: int, role: str = "body"):
    path = find_font_path(role)
    if path:
        return ImageFont.truetype(path, int(size))
    return ImageFont.load_default(size=int(size))


def text_size(font, text, tracking=0):
    b = font.getbbox(text)
    if tracking:
        return sum(font.getlength(ch) for ch in text) + tracking * max(len(text) - 1, 0), b
    return b[2] - b[0], b


def draw_text_center(draw, text, cx, top, font, fill, tracking=0):
    """top 위치에 가운데 정렬로 글자 쓰기 (tracking = 자간)"""
    if not text:
        return 0
    w, b = text_size(font, text, tracking)
    h = font.getbbox("가Ag")[3] - font.getbbox("가Ag")[1]
    x = cx - w / 2
    if tracking:
        for ch in text:
            draw.text((x, top - font.getbbox("가Ag")[1]), ch, font=font, fill=fill)
            x += font.getlength(ch) + tracking
    else:
        draw.text((x - b[0], top - font.getbbox("가Ag")[1]), text, font=font, fill=fill)
    return h


def fit_font(text, max_w, start, role="title", tracking=0, min_size=14):
    size = start
    while size > min_size:
        f = get_font(size, role)
        if text_size(f, text, tracking)[0] <= max_w:
            return f
        size -= 2
    return get_font(min_size, role)


# ---- 장식 도형 ---------------------------------------------------------------
def heart_points(cx, cy, size):
    import math
    pts = []
    for i in range(60):
        t = 2 * math.pi * i / 60
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * size / 34, cy + y * size / 34))
    return pts


def star_points(cx, cy, r, n=5, inner=0.45, rot=-90):
    import math
    pts = []
    for i in range(n * 2):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(rot + 180 * i / n)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def sticker(draw, kind, cx, cy, size, color, outline=(255, 255, 255)):
    """흰 테두리가 있는 스티커 느낌의 하트/별/반짝이"""
    if kind == "heart":
        draw.polygon(heart_points(cx, cy, size * 1.25), fill=outline)
        draw.polygon(heart_points(cx, cy, size), fill=color)
    elif kind == "star":
        draw.polygon(star_points(cx, cy, size * 0.75, inner=0.5), fill=outline)
        draw.polygon(star_points(cx, cy, size * 0.55, inner=0.45), fill=color)
    elif kind == "sparkle":
        draw.polygon(star_points(cx, cy, size * 0.6, n=4, inner=0.22), fill=color)
    elif kind == "dot":
        r = size * 0.18
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return m


def paste_shadow(canvas, box, radius, blur, offset, alpha=70):
    x0, y0, x1, y1 = box
    pad = blur * 3
    sh = Image.new("RGBA", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0),
                                         radius=radius, fill=(0, 0, 0, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(sh, (x0 - pad + offset, y0 - pad + offset))


# ---- 프레임 합성 -------------------------------------------------------------
def layout_cells(layout, style):
    """기본 해상도(300dpi) 기준 사진 칸 위치와 하단 글자 영역 계산"""
    if layout == "strip":
        W, H = SHEET_W // 2, SHEET_H
        side = 62 if style == "film" else 34
        top, gap, footer = (40 if style == "film" else 34), 18, 250
        cw = W - side * 2
        ch = (H - top - footer - gap * (SHOTS - 1)) // SHOTS
        cells = [(side, top + i * (ch + gap), side + cw, top + i * (ch + gap) + ch) for i in range(SHOTS)]
        foot = (cells[-1][3], H)
    else:
        W, H = SHEET_W, SHEET_H
        side = 84 if style == "film" else 56
        top, gap, footer = 56, 26, 330
        cw = (W - side * 2 - gap) // 2
        ch = (H - top - footer - gap) // 2
        cells = []
        for i in range(SHOTS):
            r, c = divmod(i, 2)
            x0, y0 = side + c * (cw + gap), top + r * (ch + gap)
            cells.append((x0, y0, x0 + cw, y0 + ch))
        foot = (cells[-1][3], H)
    return W, H, cells, foot


def draw_background(canvas, style, pal, W, H):
    d = ImageDraw.Draw(canvas)
    if style == "sticker":
        # 위→아래 부드러운 그라데이션
        top, bot = hex_to_rgb(pal["bg2"]), hex_to_rgb(pal["bg"])
        for y in range(H):
            d.line([(0, y), (W, y)], fill=mix(top, bot, y / H))
    elif style == "check":
        canvas.paste(hex_to_rgb(pal["bg2"]), (0, 0, W, H))
        band = 26 * K
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        col = hex_to_rgb(pal["bg"]) + (150,)
        for x in range(0, W, band * 2):
            ld.rectangle((x, 0, x + band - 1, H), fill=col)
        canvas.alpha_composite(layer)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for y in range(0, H, band * 2):
            ld.rectangle((0, y, W, y + band - 1), fill=col)
        canvas.alpha_composite(layer)
    else:
        canvas.paste(hex_to_rgb(pal["bg"]), (0, 0, W, H))


def draw_film_holes(draw, pal, W, H, side):
    hole = mix(pal["bg"], pal["ink"], 0.85) if sum(hex_to_rgb(pal["bg"])) < 384 else mix(pal["bg"], "#000000", 0.75)
    hw, hh, step = int(side * 0.38), int(side * 0.26), int(side * 0.62)
    for x in (side * 0.5, W - side * 0.5):
        y = step * 0.6
        while y < H - hh:
            draw.rounded_rectangle((x - hw / 2, y, x + hw / 2, y + hh), radius=hh * 0.3, fill=hole)
            y += step


def compose_frame(photos, layout, style, pal, title, subtitle, show_date, mirror):
    W0, H0, cells0, foot0 = layout_cells(layout, style)
    W, H = W0 * K, H0 * K
    cells = [tuple(v * K for v in c) for c in cells0]
    foot_top, foot_bot = foot0[0] * K, foot0[1] * K
    s = (W0 / 600) * K  # 사진 테두리 배율 (스트립 = 1, 격자 = 2)
    ts = (1.0 if layout == "strip" else 1.45) * K  # 글자·스티커 배율

    canvas = Image.new("RGBA", (W, H))
    draw_background(canvas, style, pal, W, H)
    draw = ImageDraw.Draw(canvas)

    if style == "film":
        draw_film_holes(draw, pal, W, H, cells[0][0])

    # 스타일별 사진 처리
    radius = {"basic": 14, "film": 0, "sticker": 26, "check": 6, "minimal": 0}[style] * s
    border = {"basic": 0, "film": 0, "sticker": 9, "check": 10, "minimal": 0}[style] * s
    shadow = style in ("sticker", "check", "basic")

    for i, (x0, y0, x1, y1) in enumerate(cells):
        x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
        if shadow:
            paste_shadow(canvas, (x0, y0, x1, y1), int(radius + border), int(7 * s), int(4 * s),
                         alpha=55 if style != "basic" else 35)
        if border:
            draw.rounded_rectangle((x0, y0, x1, y1), radius=radius + border, fill=(255, 255, 255))
        ix0, iy0, ix1, iy1 = int(x0 + border), int(y0 + border), int(x1 - border), int(y1 - border)
        ph = ImageOps.fit(photos[i], (ix1 - ix0, iy1 - iy0), method=Image.LANCZOS, centering=(0.5, 0.42))
        if mirror:
            ph = ImageOps.mirror(ph)
        if radius:
            canvas.paste(ph, (ix0, iy0), rounded_mask(ph.size, int(radius)))
        else:
            canvas.paste(ph, (ix0, iy0))
        if style == "minimal":
            draw.rectangle((ix0, iy0, ix1 - 1, iy1 - 1), outline=hex_to_rgb(pal["ink"]), width=max(1, int(1.5 * s)))

    # 스티커 장식 (사진 모서리에 살짝 걸치게)
    if style == "sticker":
        acc, ink = hex_to_rgb(pal["accent"]), hex_to_rgb(pal["ink"])
        white = mix(pal["accent"], "#FFFFFF", 0.35)  # 반짝이 색
        c = cells
        deco = [
            ("heart", c[0][2] - 6 * ts, c[0][1] + 8 * ts, 46 * ts, acc),
            ("sparkle", c[0][0] + 4 * ts, c[0][1] + 2 * ts, 40 * ts, white),
            ("star", c[1][0] + 6 * ts, c[1][3] - 6 * ts, 52 * ts, hex_to_rgb("#FFD84D")),
            ("heart", c[2][2] - 10 * ts, c[2][3] - 4 * ts, 38 * ts, acc),
            ("sparkle", c[3][2] - 2 * ts, c[3][1] + 10 * ts, 34 * ts, white),
            ("star", c[3][0] + 8 * ts, c[3][3] - 2 * ts, 40 * ts, acc),
        ]
        if layout == "grid":
            deco = [
                ("heart", c[0][2] - 10 * ts, c[0][1] + 10 * ts, 40 * ts, acc),
                ("sparkle", c[0][0] + 6 * ts, c[0][3] - 6 * ts, 34 * ts, white),
                ("star", c[1][2] - 8 * ts, c[1][3] - 8 * ts, 44 * ts, hex_to_rgb("#FFD84D")),
                ("heart", c[2][0] + 10 * ts, c[2][1] + 10 * ts, 32 * ts, acc),
                ("sparkle", c[3][2] - 6 * ts, c[3][1] + 8 * ts, 32 * ts, white),
                ("star", c[3][0] + 8 * ts, c[3][3] - 6 * ts, 36 * ts, acc),
            ]
        for kind, x, y, size, col in deco:
            sticker(draw, kind, x, y, size, col)
        # 하단 양옆 작은 장식
        fy = (foot_top + foot_bot) / 2
        for kind, dx, dy, size, col in [("heart", 44, -30, 26, acc), ("sparkle", 70, 26, 22, ink),
                                         ("dot", 30, 40, 30, acc)]:
            sticker(draw, kind, dx * ts, fy + dy * ts, size * ts, col)
            sticker(draw, kind, W - dx * ts, fy - dy * ts, size * ts, col)

    # ---- 하단 글자 영역 ----
    ink, acc = hex_to_rgb(pal["ink"]), hex_to_rgb(pal["accent"])
    cx = W / 2
    max_w = W - 90 * ts
    date_txt = datetime.now().strftime("%Y.%m.%d")

    if style == "check":
        # 흰색 라벨 카드 위에 글자
        lx0, ly0 = cells[0][0], foot_top + 26 * ts
        lx1, ly1 = cells[0][0] + (cells[-1][2] - cells[0][0]), foot_bot - 34 * ts
        paste_shadow(canvas, (int(lx0), int(ly0), int(lx1), int(ly1)), int(18 * ts), int(6 * ts), int(3 * ts), 45)
        draw.rounded_rectangle((lx0, ly0, lx1, ly1), radius=18 * ts, fill=(255, 255, 255))
        draw.rounded_rectangle((lx0 + 8 * ts, ly0 + 8 * ts, lx1 - 8 * ts, ly1 - 8 * ts), radius=12 * ts,
                               outline=acc, width=int(2.5 * ts))
        foot_top, foot_bot = ly0, ly1
        max_w = (lx1 - lx0) - 50 * ts
        ink = hex_to_rgb(pal["ink"]) if sum(hex_to_rgb(pal["ink"])) < 600 else (40, 40, 40)

    lines = []  # (text, font, color, tracking, gap_before)
    if style == "minimal":
        t = title.upper()
        tf = fit_font(t, max_w, 40 * ts, "title", tracking=10 * ts)
        lines.append((t, tf, ink, 10 * ts, 0))
        lines.append(("__rule__", None, ink, 0, 18 * ts))
        if subtitle:
            lines.append((subtitle, fit_font(subtitle, max_w, 24 * ts, "body"), ink, 0, 18 * ts))
        if show_date:
            lines.append((date_txt, get_font(19 * ts, "mono"), mix(pal["ink"], pal["bg"], 0.35), 4 * ts, 12 * ts))
    elif style == "film":
        tf = fit_font(title, max_w, 54 * ts, "title")
        lines.append((title, tf, ink, 0, 0))
        if subtitle:
            lines.append((subtitle, fit_font(subtitle, max_w, 26 * ts, "body"), mix(pal["ink"], pal["bg"], 0.2), 0, 16 * ts))
        if show_date:
            stamp = datetime.now().strftime("'%y %m %d")
            lines.append((stamp, get_font(28 * ts, "mono"), acc, 2 * ts, 16 * ts))
    else:
        tf = fit_font(title, max_w, 58 * ts, "title")
        lines.append((title, tf, ink, 0, 0))
        if subtitle:
            lines.append((subtitle, fit_font(subtitle, max_w, 28 * ts, "body"), ink, 0, 14 * ts))
        if show_date:
            lines.append((date_txt, get_font(20 * ts, "mono"), acc if style != "check" else hex_to_rgb(pal["accent"]),
                          3 * ts, 14 * ts))

    def line_h(item):
        text, font, *_ = item
        if text == "__rule__":
            return 2 * ts
        b = font.getbbox("가Ag")
        return b[3] - b[1]

    total = sum(line_h(l) + l[4] for l in lines)
    y = foot_top + (foot_bot - foot_top - total) / 2
    for item in lines:
        text, font, color, tracking, gap = item
        y += gap
        if text == "__rule__":
            draw.line([(cx - 40 * ts, y), (cx + 40 * ts, y)], fill=color, width=max(1, int(2 * ts)))
        else:
            draw_text_center(draw, text, cx, y, font, color, tracking)
        y += line_h(item)

    return canvas.convert("RGB").resize((W0, H0), Image.LANCZOS)


def placeholder_photos(n):
    """미리보기용 빈 칸 (번호가 적힌 회색 사진)"""
    out = []
    for i in range(n):
        im = Image.new("RGB", (800, 600), (214, 214, 218))
        d = ImageDraw.Draw(im)
        f = get_font(150, "title")
        draw_text_center(d, str(i + 1), 400, 220, f, (170, 170, 178))
        out.append(im)
    return out


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
        style_name = st.selectbox("프레임 스타일", list(STYLES.keys()))
        palette_name = st.selectbox("프레임 색상", list(PALETTES.keys()))
    with c2:
        title = st.text_input("프레임 제목", value="LIFE 4 CUTS")
        subtitle = st.text_input("한 줄 문구", value="우리 MBTI 찰떡 케미", help="이모지는 인쇄 글꼴에서 깨질 수 있어요.")
        show_date = st.checkbox("날짜 넣기", value=True)
        mirror = st.checkbox("좌우 반전 (거울 모드)", value=False)
    if PALETTES[palette_name] is None:
        cc1, cc2, cc3 = st.columns(3)
        bg = cc1.color_picker("배경색", "#FFE5EC")
        palette = {
            "bg": bg,
            "bg2": "#{:02X}{:02X}{:02X}".format(*mix(bg, "#FFFFFF", 0.6)),
            "ink": cc2.color_picker("글자색", "#333333"),
            "accent": cc3.color_picker("포인트색", "#FF4B6E"),
        }
    else:
        palette = PALETTES[palette_name]

layout = "strip" if "1x4" in layout_label else "grid"

if len(photos) < SHOTS:
    with st.expander("👀 프레임 미리보기", expanded=not photos):
        filled = photos + placeholder_photos(SHOTS)[len(photos):]
        preview = compose_frame(filled, layout, STYLES[style_name], palette, title, subtitle, show_date, mirror)
        st.image(preview, width=220 if layout == "strip" else 360)

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

    frame = compose_frame(photos, layout, STYLES[style_name], palette, title, subtitle, show_date, mirror)
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
