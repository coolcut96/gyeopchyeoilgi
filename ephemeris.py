# -*- coding: utf-8 -*-
"""순수 파이썬 7행성 차트 (의존성 0). 승환님 확정 차트 재현 검증 통과."""
from datetime import datetime, timedelta
import saju_natal_engine as S
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
_BODY = {'수성':'mercury','금성':'venus','화성':'mars','목성':'jupiter','토성':'saturn'}

def _retro(body, jd):
    a = S.planet_geo_lon(body, jd-0.5); b = S.planet_geo_lon(body, jd+0.5)
    return ((b-a+180) % 360 - 180) < 0

def compute_chart(y, mo, d, hh, mm, lat=37.5665, lon=126.978, tzname='Asia/Seoul'):
    if ZoneInfo:
        utc = datetime(y, mo, d, hh, mm, tzinfo=ZoneInfo(tzname)).astimezone(ZoneInfo('UTC'))
    else:
        utc = datetime(y, mo, d, hh, mm) - timedelta(hours=9)
    ut_h = utc.hour + utc.minute/60 + utc.second/3600
    jd = S.jd_from_cal(utc.year, utc.month, utc.day, ut_h)
    sun = S.sun_lon(jd)[0]
    pos = {'태양':sun, '달':S.moon_lon(jd),
           '수성':S.planet_geo_lon('mercury',jd), '금성':S.planet_geo_lon('venus',jd),
           '화성':S.planet_geo_lon('mars',jd), '목성':S.planet_geo_lon('jupiter',jd),
           '토성':S.planet_geo_lon('saturn',jd)}
    natal = {}
    for nm, l in pos.items():
        comb = None
        if nm != '태양':
            el = abs((l-sun+180) % 360 - 180)
            comb = '카지미' if el < 17/60 else ('컴버스트' if el < 8.5 else ('언더선빔' if el < 17 else None))
        retro = _retro(_BODY[nm], jd) if nm in _BODY else False
        natal[nm] = (S.SIGNS[S.sign_of(l)], round(S.deg_in_sign(l), 2), comb, retro)
    asc, _ = S.ascendant(jd, lat, lon)
    return dict(asc=(S.SIGNS[S.sign_of(asc)], round(S.deg_in_sign(asc), 2)),
                day=S.sun_altitude(jd, lat, lon) > 0, natal=natal)
