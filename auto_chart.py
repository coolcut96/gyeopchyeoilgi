# -*- coding: utf-8 -*-
"""
자동화 래퍼 — 생시+출생지 → (팔자: 사주엔진) + (정확 차트: pyswisseph) → 겹쳐읽기 리포트.
· 사주: 프로젝트 사주엔진(순수 파이썬, 검증됨).
· 별  : pyswisseph(정확·7행성+어센). 승환님 환경에서:  pip install pyswisseph
· 시간: zoneinfo(Asia/Seoul)로 한국 표준시·과거 DST 자동 보정.
"""
import math
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
import saju_natal_engine as S
import gyeopchyeoilgi as G

SIGNS = S.SIGNS
try:
    import swisseph as swe
    HAVE_SWE = True
except Exception:
    HAVE_SWE = False

# ────────── 팔자 (사주엔진 재사용, zoneinfo로 UTC 정확화) ──────────
def compute_palja(y, mo, d, hh, mm, lon_e=126.978, tzname='Asia/Seoul'):
    if ZoneInfo:
        utc = datetime(y, mo, d, hh, mm, tzinfo=ZoneInfo(tzname)).astimezone(ZoneInfo('UTC'))
    else:
        utc = datetime(y, mo, d, hh, mm) - timedelta(hours=9)   # 폴백: +9 고정
    ut_h = utc.hour + utc.minute/60 + utc.second/3600
    jd = S.jd_from_cal(utc.year, utc.month, utc.day, ut_h)
    tst = (ut_h + lon_e/15.0 + S.eot_minutes(jd)/60.0) % 24      # 진태양시(DST-무관)
    std = utc + timedelta(hours=9)                              # 한국 표준(+9) 달력일 = 일주 기준
    lam, _ = S.sun_lon(jd); gy = std.year
    if (std.month == 1) or (std.month == 2 and lam < 315): gy = std.year - 1
    yidx = (gy-4) % 60; ystem = yidx % 10; ybr = yidx % 12
    mbr = (2 + int(((lam-315) % 360)//30)) % 12
    mstart = {0:2,5:2,1:4,6:4,2:6,7:6,3:8,8:8,4:0,9:0}[ystem]
    mstem = (mstart + ((mbr-2) % 12)) % 10
    jdn = S.jdn_noon(std.year, std.month, std.day); didx = (jdn+49) % 60; dstem = didx % 10; dbr = didx % 12
    hbr = int(((tst+1)//2)) % 12
    hstart = {0:0,5:0,1:2,6:2,2:4,7:4,3:6,8:6,4:8,9:8}[dstem]
    hstem = (hstart + hbr) % 10
    P = [(ystem,ybr),(mstem,mbr),(dstem,dbr),(hstem,hbr)]
    return [(S.STEMS[st], S.BRANCHES[br]) for st, br in P]

# ────────── 정확한 차트 (pyswisseph) ──────────
def _sun_alt(jd_ut, sun_lon, lat, lon_e):
    T=(jd_ut-2451545.0)/36525.0
    eps=math.radians(23.439291-0.0130042*T)
    lam=math.radians(sun_lon)
    ra=math.atan2(math.cos(eps)*math.sin(lam), math.cos(lam))
    dec=math.asin(math.sin(eps)*math.sin(lam))
    gmst=280.46061837+360.98564736629*(jd_ut-2451545.0)
    H=math.radians((gmst+lon_e) % 360)-ra
    return math.degrees(math.asin(math.sin(math.radians(lat))*math.sin(dec)
                                  +math.cos(math.radians(lat))*math.cos(dec)*math.cos(H)))

def compute_chart(y, mo, d, hh, mm, lat=37.5665, lon=126.978, tzname='Asia/Seoul'):
    if not HAVE_SWE:
        raise RuntimeError("pyswisseph 필요 →  pip install pyswisseph")
    utc = datetime(y, mo, d, hh, mm, tzinfo=ZoneInfo(tzname)).astimezone(ZoneInfo('UTC'))
    ut_h = utc.hour + utc.minute/60 + utc.second/3600
    jd = swe.julday(utc.year, utc.month, utc.day, ut_h)
    flags = swe.FLG_MOSEPH | swe.FLG_SPEED            # Moshier: 데이터파일 불필요
    ids = [('태양',swe.SUN),('달',swe.MOON),('수성',swe.MERCURY),('금성',swe.VENUS),
           ('화성',swe.MARS),('목성',swe.JUPITER),('토성',swe.SATURN)]
    pos, retro = {}, {}
    for nm, pid in ids:
        xx, _ = swe.calc_ut(jd, pid, flags); pos[nm] = xx[0] % 360; retro[nm] = xx[3] < 0
    natal = {}
    for nm in pos:
        comb = None
        if nm != '태양':
            el = abs((pos[nm]-pos['태양']+180) % 360 - 180)
            comb = '카지미' if el < 17/60 else ('컴버스트' if el < 8.5 else ('언더선빔' if el < 17 else None))
        natal[nm] = (SIGNS[int(pos[nm]//30) % 12], round(pos[nm] % 30, 2), comb, retro[nm])
    _, ascmc = swe.houses(jd, lat, lon, b'W')
    asc = (SIGNS[int(ascmc[0]//30) % 12], round(ascmc[0] % 30, 2))
    day = _sun_alt(jd, pos['태양'], lat, lon) > 0
    return dict(asc=asc, day=day, natal=natal)

# ────────── 생시 → 리포트 케이스 ──────────
def birth_to_case(y, mo, d, hh, mm, lat=37.5665, lon=126.978, place='서울'):
    return dict(palja=compute_palja(y, mo, d, hh, mm, lon),
                **compute_chart(y, mo, d, hh, mm, lat, lon))

# ────────── 정본 대조 검증 ──────────
def validate_chart(natal, expected):   # expected={'달':('황소',23.6),...}  1° 이내면 통과
    print("  배우   계산            기대            판정")
    for nm,(esg,edeg) in expected.items():
        csg,cdeg = natal[nm][0], natal[nm][1]
        ok = (csg==esg) and abs(cdeg-edeg) < 1.0
        print(f"  {nm:3s} {csg} {cdeg:5.2f}°   {esg} {edeg:5.2f}°   {'✓' if ok else '✗ 차이 %.1f°'%abs(cdeg-edeg) if csg==esg else '✗ 사인다름'}")

# ════════ 데모 ════════
if __name__ == '__main__':
    print("="*60)
    print("【A】 생시 → 팔자 자동계산 (zoneinfo 적용) — 사주엔진 대조")
    pj = compute_palja(1989, 12, 28, 8, 30)
    print("  1989-12-28 08:30 서울 →", "  ".join(a+b for a,b in pj))
    print("  기대(예제38): 기사 병자 임술 갑진")

    print("\n【B】 정확한 별 계산 (pyswisseph)")
    print(f"  swisseph 설치됨? {HAVE_SWE}")
    if not HAVE_SWE:
        print("  → 이 샌드박스엔 없음. 승환님 환경:  pip install pyswisseph")
        print("  → 설치되면 compute_chart()가 7행성+어센을 정확히 계산(달·어센 5° 오차 해결).")

    print("\n【C】 통합 배관 (mock 차트로 birth_to_case→리포트 흐름 확인)")
    # swe 없을 때 데모용: 실입력 인물의 확정 차트를 mock으로 (실제론 compute_chart가 채움)
    mock = dict(palja=[('정','사'),('임','자'),('계','축'),('무','오')],
                asc=('양자리',13.16), day=True,
                natal={'목성':('게',1.19,None,True),'태양':('염소',0.20,None,False),
                       '달':('황소',23.64,None,False),'화성':('사자',10.97,None,True),
                       '토성':('처녀',0.44,None,True),'금성':('사수',22.76,None,False),
                       '수성':('사수',28.81,None,True)})
    a = G.analyze(mock)
    print("  판정:", "지배", a['dom'], "/", "신강" if a['sinkang'] else "신약",
          "/ 겹침·어긋남", [(k,t) for k,t in a['find']])
    print("\n  [무료 리포트]\n")
    print(G.render(a, '무료'))
