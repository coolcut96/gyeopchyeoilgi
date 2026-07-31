# -*- coding: utf-8 -*-
"""
「겹쳐읽기」 무료 자동 리포트 웹앱 v3 (확정 디자인 반영)
- 디자인: 옥색 흰빛 배경 + 12사인·12지지 겹친 천문반 워터마크. 로고 없이 제목부터.
- 입력: 양력/음력(+조건부 윤달) · 출생지(주요 도시 하드코딩 + 검색/지오코딩) · 시간 모름(정오)
- 흐름: 입력 → (대기화면 스피너 + 배너) → 리포트 + 배너
- 생성: AI 붓(있으면) / 템플릿 폴백
- 실행:  python3 web_app.py  →  http://localhost:8000
※ 라이브러리(승환님 환경): pip install anthropic korean_lunar_calendar geopy timezonefinder
"""
import http.server, socketserver, urllib.parse, html, re, os, time, threading
import gyeopchyeoilgi as G
from auto_chart import compute_palja
import ephemeris
try:
    import ai_brush
except Exception:
    ai_brush = None

TIER = "유료"   # 무료 서비스지만 풀 리포트를 값싼 하이쿠로
PORT = int(os.environ.get("PORT", 8000))   # 호스팅이 지정하는 포트 자동 인식
CONTACT = "coolcut96@gmail.com"            # 처리방침 문의처 (교체 가능)
SITE_URL = "https://port-0-gyeopchyeoilgi-ms6u5ojjac33edd8.sel3.cloudtype.app"  # 배포 주소(og:image 절대경로용)
OG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "og.png")     # 카톡 미리보기 썸네일

# ── 남용 방지: IP별 요청 제한 (in-memory, 요금 폭탄·봇 스팸 차단) ──
_RATE = {}                       # ip -> [timestamps]
_RATE_LOCK = threading.Lock()
LIMIT_HOUR, LIMIT_DAY = 8, 25    # IP당 시간/일 최대 리포트 수
def rate_ok(ip):
    now = time.time()
    with _RATE_LOCK:
        hist = [t for t in _RATE.get(ip, []) if now - t < 86400]
        if sum(1 for t in hist if now - t < 3600) >= LIMIT_HOUR or len(hist) >= LIMIT_DAY:
            _RATE[ip] = hist; return False
        hist.append(now); _RATE[ip] = hist; return True

# ── 책 배너 (URL은 판매 링크 나오면 교체) ──
# 각 책의 서점별 링크. ▼▼ 나중에 실제 판매 주소로 교체 ▼▼ (없는 서점은 그 줄을 지우면 버튼도 사라짐)
BOOKS = [
    {"title": "별을 보다가 사주를 펼쳤다", "brtitle": "별을 보다가<br>사주를 펼쳤다", "sub": "사주인을 위한 점성술 입문", "cls": "c1", "emoji": "📘",
     "stores": {"리디북스": "https://리디북스-링크-1권", "교보문고": "https://교보문고-링크-1권", "예스24": "https://예스24-링크-1권"}},
    {"title": "여덟 글자 뒤의 별들", "brtitle": "여덟 글자<br>뒤의 별들", "sub": "점성술 렌즈로 본 사주의 구조", "cls": "c2", "emoji": "📗",
     "stores": {"리디북스": "https://리디북스-링크-2권", "교보문고": "https://교보문고-링크-2권", "예스24": "https://예스24-링크-2권"}},
    {"title": "일단 해보자 점성술", "brtitle": "일단 해보자<br>점성술", "sub": "직접 따라 하며 익히는 실전 점성술", "cls": "c3", "emoji": "📙",
     "stores": {"리디북스": "https://리디북스-링크-3권", "교보문고": "https://교보문고-링크-3권", "예스24": "https://예스24-링크-3권"}},
]
PUBLISHER = "별읽기 · Star Reading"

# ── 주요 도시 하드코딩: 이름 → (위도, 경도, IANA 시간대) ──
CITIES = {
 # 국내 (모두 Asia/Seoul)
 "서울":(37.5665,126.9780,"Asia/Seoul"), "부산":(35.1796,129.0756,"Asia/Seoul"),
 "대구":(35.8714,128.6014,"Asia/Seoul"), "인천":(37.4563,126.7052,"Asia/Seoul"),
 "광주":(35.1595,126.8526,"Asia/Seoul"), "대전":(36.3504,127.3845,"Asia/Seoul"),
 "울산":(35.5384,129.3114,"Asia/Seoul"), "세종":(36.4800,127.2890,"Asia/Seoul"),
 "수원":(37.2636,127.0286,"Asia/Seoul"), "성남":(37.4200,127.1265,"Asia/Seoul"),
 "고양":(37.6584,126.8320,"Asia/Seoul"), "용인":(37.2411,127.1776,"Asia/Seoul"),
 "창원":(35.2280,128.6811,"Asia/Seoul"), "청주":(36.6424,127.4890,"Asia/Seoul"),
 "천안":(36.8151,127.1139,"Asia/Seoul"), "전주":(35.8242,127.1480,"Asia/Seoul"),
 "포항":(36.0190,129.3435,"Asia/Seoul"), "김해":(35.2285,128.8894,"Asia/Seoul"),
 "제주":(33.4996,126.5312,"Asia/Seoul"), "춘천":(37.8813,127.7300,"Asia/Seoul"),
 "원주":(37.3422,127.9202,"Asia/Seoul"), "강릉":(37.7519,128.8761,"Asia/Seoul"),
 "목포":(34.8118,126.3922,"Asia/Seoul"), "여수":(34.7604,127.6622,"Asia/Seoul"),
 "안동":(36.5684,128.7294,"Asia/Seoul"),
 # 일본·중국
 "도쿄":(35.6762,139.6503,"Asia/Tokyo"), "오사카":(34.6937,135.5023,"Asia/Tokyo"),
 "나고야":(35.1815,136.9066,"Asia/Tokyo"), "후쿠오카":(33.5904,130.4017,"Asia/Tokyo"),
 "베이징":(39.9042,116.4074,"Asia/Shanghai"), "상하이":(31.2304,121.4737,"Asia/Shanghai"),
 "칭다오":(36.0671,120.3826,"Asia/Shanghai"), "선양":(41.8057,123.4315,"Asia/Shanghai"),
 "옌지(연길)":(42.9048,129.5091,"Asia/Shanghai"),
 # 미국·캐나다
 "뉴욕":(40.7128,-74.0060,"America/New_York"), "로스앤젤레스(LA)":(34.0522,-118.2437,"America/Los_Angeles"),
 "시카고":(41.8781,-87.6298,"America/Chicago"), "샌프란시스코":(37.7749,-122.4194,"America/Los_Angeles"),
 "시애틀":(47.6062,-122.3321,"America/Los_Angeles"), "애틀랜타":(33.7490,-84.3880,"America/New_York"),
 "워싱턴DC":(38.9072,-77.0369,"America/New_York"), "휴스턴":(29.7604,-95.3698,"America/Chicago"),
 "댈러스":(32.7767,-96.7970,"America/Chicago"), "보스턴":(42.3601,-71.0589,"America/New_York"),
 "호놀룰루":(21.3069,-157.8583,"Pacific/Honolulu"),
 "토론토":(43.6532,-79.3832,"America/Toronto"), "밴쿠버":(49.2827,-123.1207,"America/Vancouver"),
 # 유럽·기타
 "런던":(51.5074,-0.1278,"Europe/London"), "파리":(48.8566,2.3522,"Europe/Paris"),
 "프랑크푸르트":(50.1109,8.6821,"Europe/Berlin"), "두바이":(25.2048,55.2708,"Asia/Dubai"),
 "싱가포르":(1.3521,103.8198,"Asia/Singapore"), "홍콩":(22.3193,114.1694,"Asia/Hong_Kong"),
 "시드니":(-33.8688,151.2093,"Australia/Sydney"), "멜버른":(-37.8136,144.9631,"Australia/Melbourne"),
 "오클랜드":(-36.8485,174.7633,"Pacific/Auckland"),
}
# 드롭다운 표시 순서(지역별 그룹)
CITY_GROUPS = [
 ("국내", ["서울","부산","대구","인천","광주","대전","울산","세종","수원","성남","고양","용인",
          "창원","청주","천안","전주","포항","김해","제주","춘천","원주","강릉","목포","여수","안동"]),
 ("일본·중국", ["도쿄","오사카","나고야","후쿠오카","베이징","상하이","칭다오","선양","옌지(연길)"]),
 ("미국·캐나다", ["뉴욕","로스앤젤레스(LA)","시카고","샌프란시스코","시애틀","애틀랜타","워싱턴DC",
               "휴스턴","댈러스","보스턴","호놀룰루","토론토","밴쿠버"]),
 ("유럽·기타", ["런던","파리","프랑크푸르트","두바이","싱가포르","홍콩","시드니","멜버른","오클랜드"]),
]

# ── 훅: 음력→양력 (korean_lunar_calendar 필요) ──
def lunar_to_solar(y, m, d, is_leap=False):
    try:
        from korean_lunar_calendar import KoreanLunarCalendar
        c = KoreanLunarCalendar(); c.setLunarDate(y, m, d, is_leap)
        yy, mm, dd = map(int, c.SolarIsoFormat().split("-"))
        return yy, mm, dd, None
    except ImportError:
        return y, m, d, "음력 변환 라이브러리(korean_lunar_calendar) 미설치 — 우선 양력으로 처리."

# ── 훅: 도시명 → (위도, 경도, 시간대) (geopy + timezonefinder 필요) ──
def geocode_city(name):
    try:
        from geopy.geocoders import Nominatim
        from timezonefinder import TimezoneFinder
        loc = Nominatim(user_agent="gyeopchyeoilgi").geocode(name)
        if not loc: return None
        tz = TimezoneFinder().timezone_at(lat=loc.latitude, lng=loc.longitude)
        return (round(loc.latitude,4), round(loc.longitude,4), tz or "Asia/Seoul")
    except ImportError:
        return None

def resolve_place(city, custom):
    if city and city in CITIES:
        lat,lon,tz = CITIES[city]; return lat,lon,tz,city,None
    if custom:
        g = geocode_city(custom)
        if g: return g[0],g[1],g[2],custom,None
        return CITIES["서울"][0],CITIES["서울"][1],CITIES["서울"][2],custom,"도시 검색(지오코딩) 미설치/실패 — 서울 기준으로 처리."
    lat,lon,tz = CITIES["서울"]; return lat,lon,tz,"서울",None

def resolve_date(cal, y, m, d, leap):
    if cal == "음력":
        return lunar_to_solar(y, m, d, leap)
    return y, m, d, None

# ── 리포트 생성 ──
def make_report(fields):
    warns = []
    y,mo,d,w1 = resolve_date(fields["cal"], fields["y"], fields["mo"], fields["d"], fields["leap"]);  warns += [w1] if w1 else []
    lat,lon,tz,place,w2 = resolve_place(fields["city"], fields["custom"]);  warns += [w2] if w2 else []
    tu = fields["time_unknown"]
    hh,mm = (12,0) if tu else (fields["hh"], fields["mm"])
    palja = compute_palja(y,mo,d,hh,mm, lon, tz)
    chart = ephemeris.compute_chart(y,mo,d,hh,mm, lat, lon, tz)
    case = dict(palja=palja, **chart)
    a = G.analyze(case)
    key = os.environ.get("ANTHROPIC_API_KEY")
    if ai_brush and key:
        text, path = ai_brush.final_report(a, TIER, api_key=key, time_unknown=tu)
    else:
        text = G.render(a, TIER, time_unknown=tu)
    return text, palja, warns

# ── 마크다운 → HTML ──
def md(text):
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    out = []
    for p in text.split("\n\n"):
        p = p.strip()
        if not p: continue
        if p.startswith("## "): out.append(f"<h2>{p[3:].strip()}</h2>")
        elif p.startswith("---"): out.append("<hr>")
        elif p.startswith("※"): out.append(f'<p class="note">{p}</p>')
        elif p.startswith("*") and p.endswith("*"): out.append(f'<p class="sig">{p.strip("*").strip()}</p>')
        else: out.append(f"<p>{p}</p>")
    return "\n".join(out)

def book_banner(heading="이 풀이의 원리가 궁금하다면"):
    covers = "".join(
        f'<div class="minibook"><div class="cover {b["cls"]}">{b["emoji"]}</div>'
        f'<div class="mbt">{b.get("brtitle", b["title"])}</div></div>'
        for b in BOOKS)
    return (f'<div class="banner"><div class="bh">{heading}</div>'
            f'<div class="bsub">사주와 별을 나란히 읽는 법 · 오승환 3부작</div>'
            f'<div class="bookrow">{covers}</div>'
            f'<a class="bookcta" href="/books" onclick="return openBooks(event)">책 보러 가기 →</a></div>')

def _books_cards():
    cards = ""
    for b in BOOKS:
        btns = "".join(f'<a class="store" href="{u}" target="_blank">{n} →</a>' for n, u in b["stores"].items())
        cards += (f'<div class="card bookbuy"><div class="bmeta">'
                  f'<div class="cover {b["cls"]}">{b["emoji"]}</div>'
                  f'<div><div class="bt">{b["title"]}</div><div class="bs">{b["sub"]}</div></div></div>'
                  f'<div class="stores">{btns}</div></div>')
    return cards

def books_page():   # JS 꺼진 브라우저용 폴백(별도 페이지)
    body = ('<div class="pagetitle"><h1>책 사러 가기</h1>'
            '<p>편한 서점을 골라 주세요 — 어디서 사셔도 같은 책이에요.</p></div>'
            + _books_cards() +
            '<div class="backlink"><a href="/">← 리포트로 돌아가기</a></div>'
            f'<div class="foot">{PUBLISHER}</div>')
    return PAGE.replace("%%BODY%%", body)

# ── CSS ──
CSS = """
:root{
  --jade-1:#fafdfb; --jade-2:#eef6f1; --jade-line:#5f9280;
  --ink:#173a33; --ink-soft:#3c5b53; --text:#1f2a27; --muted:#6a7d76;
  --card:#fcfcf9; --card-line:#e2e8e2; --gold:#b0872f; --gold-soft:#f4ecd8;
}
*{box-sizing:border-box}
html,body{margin:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;
  color:var(--text);line-height:1.68;
  background:linear-gradient(170deg,var(--jade-1) 0%,var(--jade-2) 100%);
  background-attachment:fixed;min-height:100vh}
#sky{position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none}
#sky svg{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  width:min(155vw,960px);height:auto;opacity:.13}
.wrap{position:relative;z-index:1;max-width:640px;margin:0 auto;padding:0 18px 56px}
.hero{text-align:center;padding:28px 8px 26px}
.hero h1{font-size:27px;line-height:1.35;margin:0;color:var(--ink);font-weight:800;letter-spacing:-.01em}
.rule{width:46px;height:2px;background:var(--ink);opacity:.35;margin:18px auto 0;border-radius:2px}
.hook{font-size:14.5px;color:var(--ink-soft);margin:13px 0 0;line-height:1.65}
.discover{text-align:center;color:var(--ink-soft);font-size:14.5px;line-height:1.65;margin:20px 6px 14px}
.card{background:var(--card);border:1px solid var(--card-line);border-radius:18px;
  padding:24px 22px;box-shadow:0 10px 30px -14px rgba(23,58,51,.28);margin-bottom:20px}
label{display:block;font-size:12.5px;color:var(--ink-soft);margin:14px 0 5px;font-weight:600}
.row{display:flex;gap:9px}.row>div{flex:1}
input,select{width:100%;padding:11px 12px;border:1px solid #d3ded6;border-radius:11px;
  font-size:15px;color:var(--text);background:#fff;font-family:inherit}
input:focus,select:focus{outline:none;border-color:var(--ink-soft);box-shadow:0 0 0 3px rgba(95,146,128,.18)}
input:disabled{background:#eef2ee;color:#a9b6af}
.radio{display:flex;gap:10px;margin-top:2px}
.radio label{flex:1;display:flex;align-items:center;justify-content:center;gap:6px;margin:0;
  padding:10px;border:1px solid #d3ded6;border-radius:11px;cursor:pointer;font-weight:500;color:var(--text)}
.radio input{width:auto;accent-color:var(--ink)}
.radio label.on{border-color:var(--ink);background:#eef4f0;color:var(--ink);font-weight:700}
.chk{display:flex;align-items:center;gap:8px;font-size:13.5px;color:var(--ink-soft);margin-top:11px;cursor:pointer}
.chk input{width:auto;accent-color:var(--ink)}
.muted{color:var(--muted)}
.hide{display:none}
button.go{margin-top:20px;width:100%;padding:15px;border:0;border-radius:13px;
  background:var(--ink);color:#f4f8f5;font-size:16px;font-weight:800;letter-spacing:.02em;cursor:pointer;
  box-shadow:0 8px 20px -8px rgba(23,58,51,.6)}
button.go:active{transform:translateY(1px)}
.consent{font-size:11px;color:var(--muted);margin-top:11px;text-align:center}
.loadcard{text-align:center;padding:48px 22px 44px;margin-top:24px}
.spin{width:36px;height:36px;border:3px solid #e2ebe5;border-top-color:var(--ink);
  border-radius:50%;margin:0 auto 15px;animation:sp .9s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}
.loadmsg{color:var(--ink-soft);font-size:14.5px}
.report h2{font-size:20px;color:var(--ink);margin:0 0 6px;line-height:1.4;font-weight:800}
.report .who{font-size:13px;color:var(--muted);margin:0 0 18px}
.report p{margin:0 0 15px;font-size:15.5px}
.report strong{color:var(--ink);font-weight:700}
.report hr{border:0;border-top:1px solid #eef1ee;margin:20px 0}
.report .note{font-size:12.5px;color:#8a6d3b;background:var(--gold-soft);border-radius:9px;padding:10px 12px}
.report .sig{font-size:13px;color:var(--muted);font-style:italic;line-height:1.6}
.warn{background:#fff7ed;border:1px solid #fdba74;color:#9a3412;font-size:12px;border-radius:9px;padding:9px 12px;margin-bottom:12px}
.banner{background:linear-gradient(160deg,#fffdf6,#fbf6e8);border:1.5px solid #efe4c9;border-radius:18px;padding:20px;margin-bottom:20px}
.bh{font-weight:800;color:var(--ink);font-size:15px;margin-bottom:3px}
.bsub{font-size:12.5px;color:var(--muted);margin-bottom:14px}
.book{display:flex;gap:13px;align-items:center;text-decoration:none;color:inherit;
  background:#fff;border:1px solid #f0e9d8;border-radius:12px;padding:12px;margin-bottom:9px;transition:.15s}
.book:hover{border-color:var(--gold);transform:translateX(2px)}
.cover{width:42px;height:56px;flex:none;border-radius:5px;display:flex;align-items:center;justify-content:center;
  font-size:22px;color:#fff;box-shadow:0 3px 8px -3px rgba(0,0,0,.4)}
.c1{background:linear-gradient(150deg,#2e5d52,#173a33)}
.c2{background:linear-gradient(150deg,#3a4a7a,#1f2a52)}
.c3{background:linear-gradient(150deg,#9a7b2e,#6e5518)}
.bt{font-weight:700;font-size:14.5px;color:var(--text)}
.bs{font-size:12px;color:var(--muted);margin-top:1px}
.buy{font-size:12.5px;color:var(--gold);font-weight:700;margin-top:4px}
.foot{text-align:center;font-size:12px;color:var(--muted);margin-top:8px}
.bookcta{display:block;text-align:center;text-decoration:none;margin-top:12px;padding:14px;border-radius:11px;background:var(--ink);color:#f4f8f5;font-weight:800;font-size:15px}
.bookrow{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:2px}
.minibook{text-align:center}
.minibook .cover{width:46px;height:62px;margin:0 auto 7px}
.mbt{font-size:11px;color:var(--ink);font-weight:700;line-height:1.32}
.pagetitle{text-align:center;padding:24px 8px 6px}
.pagetitle h1{font-size:22px;color:var(--ink);margin:0;font-weight:800}
.pagetitle p{font-size:13px;color:var(--muted);margin:8px 0 0}
.bookbuy{padding:18px}
.bmeta{display:flex;gap:13px;align-items:center;margin-bottom:14px}
.stores{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.store{text-align:center;text-decoration:none;padding:11px 6px;border-radius:10px;border:1.5px solid #d8d4cc;color:var(--ink);font-weight:700;font-size:13px;background:#fff}
.store:hover{border-color:var(--gold);color:var(--gold)}
.backlink{text-align:center;margin-top:14px}
.backlink a{color:var(--ink);font-size:14px;font-weight:600;text-decoration:underline}
.modal{position:fixed;inset:0;z-index:20;overflow-y:auto;background:linear-gradient(170deg,var(--jade-1),var(--jade-2))}
.modal .minner{max-width:640px;margin:0 auto;padding:0 18px 44px}
.modalbar{position:sticky;top:0;background:rgba(250,253,251,.94);padding:14px 2px;margin-bottom:2px}
.modalbar a{display:inline-block;background:var(--ink);color:#f4f8f5;font-weight:700;font-size:13.5px;text-decoration:none;padding:9px 16px;border-radius:20px}
.sharebtn{display:block;width:100%;margin-top:14px;padding:13px;border-radius:11px;background:#fff;border:1.5px solid var(--ink);color:var(--ink);font-weight:800;font-size:15px;cursor:pointer}
.sharebtn:active{transform:translateY(1px)}
.toast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:var(--ink);color:#eaf2ee;padding:11px 18px;border-radius:22px;font-size:13.5px;font-weight:700;z-index:40;display:none}
@media(min-width:560px){.hero h1{font-size:30px}.card{padding:28px 30px}}
"""

# ── 폼 (프론트) ──
FORM = """
<div id="top">
<div class="hero"><h1>사주와 별,<br>두 시계로 나를 겹쳐 봅니다</h1><p class="hook">내 여덟 글자가, 하늘의 어느 별과 겹치는지 —</p><div class="rule"></div></div>
<div class="card">
<form id="f" onsubmit="return submitForm(event)">
<label>이름 (선택)</label><input name="name" placeholder="예: 홍길동">
<label>달력</label>
<div class="radio">
  <label class="on"><input type="radio" name="cal" value="양력" checked onchange="cal()"> 양력</label>
  <label><input type="radio" name="cal" value="음력" onchange="cal()"> 음력</label>
</div>
<label class="chk hide" id="leapbox"><input type="checkbox" name="leap"> 그 달이 윤달이었어요 <span class="muted">(해당될 때만)</span></label>
<label>생년월일</label>
<div class="row">
  <div><input name="y" type="text" inputmode="numeric" maxlength="4" placeholder="1980년" required></div>
  <div><input name="mo" type="text" inputmode="numeric" maxlength="2" placeholder="5월" required></div>
  <div><input name="d" type="text" inputmode="numeric" maxlength="2" placeholder="15일" required></div>
</div>
<label>태어난 시각</label>
<div class="row">
  <div><input name="hh" id="hh" type="text" inputmode="numeric" maxlength="2" placeholder="시 (0~23)"></div>
  <div><input name="mm" id="mm" type="text" inputmode="numeric" maxlength="2" placeholder="분"></div>
</div>
<label class="chk"><input type="checkbox" name="tu" id="tu" onchange="togTime()"> 태어난 시각을 몰라요 <span class="muted">(정오 기준)</span></label>
<label>출생지</label>
<select name="city" id="city" required onchange="togCity()"><option value="" disabled selected>출생지를 선택하세요</option>%%CITIES%%<option value="__custom__">▸ 목록에 없어요 (직접 검색)</option></select>
<div id="custombox" class="hide" style="margin-top:9px"><input name="custom" placeholder="도시, 나라 · 예: 청주 / Lyon, France"></div>
<button type="submit" class="go">무료로 내 리포트 보기</button>
<div class="consent">입력 정보는 저장하지 않습니다 · <a href="/privacy" target="_blank" style="color:var(--ink-soft)">개인정보 처리방침</a></div>
</form>
</div>
</div>
<div id="bnr" class="hide">%%LOADBANNER%%</div>
<div id="out"></div>
<div class="foot">%%PUBLISHER%%</div>
<div id="booksModal" class="modal hide"><div class="minner">
<div class="modalbar"><a href="#" onclick="closeBooks();return false">← 리포트로 돌아가기</a></div>
<div class="pagetitle"><h1>책 사러 가기</h1><p>편한 서점을 골라 주세요 — 어디서 사셔도 같은 책이에요.</p></div>
%%BOOKSMODAL%%
</div></div>
<div id="copytoast" class="toast">링크가 복사됐어요 ✓</div>
<script>
var f=document.getElementById('f');
function cal(){var m=(f.cal.value=='음력');document.getElementById('leapbox').className='chk'+(m?'':' hide');
  document.querySelectorAll('.radio label').forEach(function(l){l.classList.toggle('on',l.querySelector('input').checked);});}
function togTime(){var u=document.getElementById('tu').checked;hh.disabled=u;mm.disabled=u;}
function togCity(){document.getElementById('custombox').className=(city.value=='__custom__')?'':'hide';}
function openBooks(e){e.preventDefault();document.getElementById('booksModal').classList.remove('hide');window.scrollTo(0,0);return false;}
function closeBooks(){document.getElementById('booksModal').classList.add('hide');}
function shareSite(){
  var url=location.origin+'/';
  if(navigator.share){navigator.share({title:'사주와 별, 두 시계로 나를 겹쳐 봅니다',text:'사주와 점성술로 나를 교차 검토한 무료 리포트, 나도 받아봤어요 🌗',url:url}).catch(function(){});return;}
  if(navigator.clipboard){navigator.clipboard.writeText(url).catch(function(){});}
  var t=document.getElementById('copytoast');if(t){t.style.display='block';setTimeout(function(){t.style.display='none';},2000);}
}
function submitForm(e){
  e.preventDefault();
  var out=document.getElementById('out');
  document.getElementById('top').style.display='none';   // 입력 폼 감추기(로딩 붕뜸 방지)
  out.innerHTML='<div class="card loadcard"><div class="spin"></div><div class="loadmsg">사주와 별을 나란히 맞춰보는 중…</div></div>'
    +document.getElementById('bnr').innerHTML;
  window.scrollTo({top:0,behavior:'smooth'});
  fetch('/generate',{method:'POST',body:new URLSearchParams(new FormData(f))})
    .then(function(r){return r.text();})
    .then(function(t){out.innerHTML=t;window.scrollTo({top:0,behavior:'smooth'});})
    .catch(function(_){out.innerHTML='<div class="card">잠시 문제가 생겼어요. 다시 시도해 주세요.</div>';});
  return false;
}
</script>
"""

PAGE = ("<!DOCTYPE html><html lang=ko><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>겹쳐읽기 · 사주와 점성술로 보는 나</title>"
        "<meta property='og:title' content='사주와 별, 두 시계로 나를 겹쳐 봅니다'>"
        "<meta property='og:description' content='생년월일시만 넣으면 사주와 점성술로 나를 교차 검토한 리포트를 무료로 받아보세요.'>"
        "<meta property='og:type' content='website'>"
        "<meta property='og:image' content='"+SITE_URL+"/og.png'>"
        "<meta property='og:url' content='"+SITE_URL+"/'>"
        "<meta name='twitter:card' content='summary_large_image'>"
        "<meta name='twitter:image' content='"+SITE_URL+"/og.png'>"
        "<style>"+CSS+"</style></head>"
        "<body><div id=sky></div><div class=wrap>%%BODY%%</div>"
        "<script>"+ """
(function(){var NS="http://www.w3.org/2000/svg",J="#5f9280";
var signs="♈♉♊♋♌♍♎♏♐♑♒♓".split("").map(function(c){return c+"︎";}); // ︎=text presentation(단색 강제)
var jiji="子丑寅卯辰巳午未申酉戌亥".split("");
var svg=document.createElementNS(NS,"svg");svg.setAttribute("viewBox","0 0 440 300");
function E(n,a){var e=document.createElementNS(NS,n);for(var k in a)e.setAttribute(k,a[k]);return e;}
function ring(cx,cy,r,dash){var o={cx:cx,cy:cy,r:r,fill:"none",stroke:J,"stroke-width":1};if(dash)o["stroke-dasharray"]=dash;svg.appendChild(E("circle",o));}
function spokes(cx,cy,r1,r2){for(var i=0;i<12;i++){var a=(i*30-90)*Math.PI/180;svg.appendChild(E("line",{x1:cx+r1*Math.cos(a),y1:cy+r1*Math.sin(a),x2:cx+r2*Math.cos(a),y2:cy+r2*Math.sin(a),stroke:J,"stroke-width":.5}));}}
function glyphs(cx,cy,r,arr){for(var i=0;i<12;i++){var a=(i*30-90+15)*Math.PI/180;var t=E("text",{x:cx+r*Math.cos(a),y:cy+r*Math.sin(a),fill:J,"font-size":13,"text-anchor":"middle","dominant-baseline":"central"});t.textContent=arr[i];svg.appendChild(t);}}
function star(cx,cy){for(var i=0;i<8;i++){var a=i*Math.PI/4,L=(i%2?5:11);svg.appendChild(E("line",{x1:cx,y1:cy,x2:cx+L*Math.cos(a),y2:cy+L*Math.sin(a),stroke:J,"stroke-width":.7}));}}
function wheel(cx,cy,arr){ring(cx,cy,120);ring(cx,cy,98,"2 4");ring(cx,cy,66);spokes(cx,cy,66,120);glyphs(cx,cy,109,arr);star(cx,cy);}
wheel(150,150,signs);   // 왼쪽 = 12 별자리
wheel(290,150,jiji);    // 오른쪽 = 12 지지 (옆으로 겹침)
document.getElementById("sky").appendChild(svg);})();
""" + "</script></body></html>")

def form_page():
    opts = "".join(
        f'<optgroup label="{g}">' + "".join(f'<option value="{c}">{c}</option>' for c in names) + '</optgroup>'
        for g, names in CITY_GROUPS)
    body = (FORM.replace("%%CITIES%%", opts)
                .replace("%%LOADBANNER%%", book_banner("기다리는 동안 — 이 풀이의 원리가 궁금하다면"))
                .replace("%%BOOKSMODAL%%", _books_cards())
                .replace("%%PUBLISHER%%", PUBLISHER))
    return PAGE.replace("%%BODY%%", body)

PRIVACY = """
<div class="hero"><h1 style="font-size:22px">개인정보 처리방침</h1><div class="rule"></div></div>
<div class="card" style="line-height:1.75">
<p><strong>1. 수집하는 항목</strong><br>리포트를 만드는 데 필요한 <strong>생년월일·태어난 시각·출생지</strong>를 입력받습니다. 이름은 선택이며 넣지 않아도 됩니다.</p>
<p><strong>2. 이용 목적</strong><br>입력하신 정보는 오직 <strong>그 자리에서 사주·점성술 리포트를 만드는 데에만</strong> 쓰입니다.</p>
<p><strong>3. 보관 — 저장하지 않습니다</strong><br>입력값은 리포트를 만든 즉시 사라지며, <strong>서버에 따로 저장·기록하지 않습니다(보관 0일).</strong> 브라우저를 닫으면 아무 흔적도 남지 않습니다.</p>
<p><strong>4. 제3자 처리</strong><br>리포트 <em>문장</em>을 다듬기 위해 AI(Anthropic Claude)에 판정 결과 재료가 전달될 수 있으나, <strong>생년월일 원본 자체는 전달되지 않으며</strong> 개인을 식별할 수 없는 형태로만 처리됩니다.</p>
<p><strong>5. 문의</strong><br>개인정보 관련 문의: """ + CONTACT + """</p>
<p style="margin-top:18px"><a href="/" style="color:var(--ink)">← 리포트 만들러 돌아가기</a></p>
</div>
<div class="foot">""" + PUBLISHER + """</div>
"""
def privacy_page():
    return PAGE.replace("%%BODY%%", PRIVACY)

def report_fragment(name, text, palja, warns):
    who = f"{name} 님 · " if name else ""
    pj = " · ".join(a+b for a,b in palja)
    who_line = f'<p class="who">🌗 {html.escape(who)}사주 {pj}</p>'
    body_html = md(text).replace("</h2>", "</h2>\n" + who_line, 1)
    w = "".join(f'<div class="warn">⚠️ {html.escape(x)}</div>' for x in warns)
    return (w + f'<div class="report card">{body_html}</div>'
            + '<p class="discover">여기까지가 맛보기예요. 두 시계가 왜 같은 자리를 가리키는지, 그 겹침을 끝까지 따라가 보고 싶다면 —</p>'
            + book_banner()
            + '<button class="sharebtn" onclick="shareSite()">🔗 친구에게 소개하기</button>'
            + '<div class="backlink"><a href="/">🔄 다른 사주 보기</a></div>')

class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, s, code=200):
        b = s.encode("utf-8")
        self.send_response(code); self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _ip(self):
        xff = self.headers.get("X-Forwarded-For")
        return xff.split(",")[0].strip() if xff else self.client_address[0]
    def do_GET(self):
        if self.path.startswith("/og.png"):
            try:
                with open(OG_PATH, "rb") as fh: data = fh.read()
                self.send_response(200); self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            except FileNotFoundError:
                self.send_response(404); self.end_headers()
            return
        if self.path.startswith("/privacy"):
            self._send(privacy_page()); return
        if self.path.startswith("/books"):
            self._send(books_page()); return
        if self.path == "/favicon.ico":
            self.send_response(204); self.end_headers(); return
        self._send(form_page())
    def do_POST(self):
        if self.path != "/generate":
            self._send(form_page()); return
        if not rate_ok(self._ip()):
            self._send('<div class="card">오늘 요청이 많았어요. 잠시 후(또는 내일) 다시 시도해 주세요. 🌙</div>'); return
        n = int(self.headers.get("Content-Length", 0))
        q = urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8"))
        g = lambda k, d="": q.get(k, [d])[0]
        try:
            fields = dict(
                name=g("name").strip(), cal=g("cal","양력"), leap=(g("leap")=="on"),
                y=int(g("y")), mo=int(g("mo")), d=int(g("d")),
                hh=int(g("hh") or 12), mm=int(g("mm") or 0), time_unknown=(g("tu")=="on"),
                city=g("city","서울"), custom=g("custom").strip())
            text, palja, warns = make_report(fields)
            self._send(report_fragment(fields["name"], text, palja, warns))
        except Exception as e:
            self._send(f'<div class="card">입력값을 확인해 주세요. ({html.escape(str(e))})</div>', 400)

if __name__ == "__main__":
    # ThreadingHTTPServer: AI 붓 응답이 몇 초 걸려도 다른 손님이 안 막힘(동시 접속)
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"→ http://localhost:{PORT}  (Ctrl+C 종료)")
    httpd.serve_forever()
