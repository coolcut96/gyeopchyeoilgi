"""사주(만세력)+네이탈 계산엔진 (프로젝트 도구 복사본). 순수 파이썬."""
import sys, math
R=math.radians; D=math.degrees
def norm(x): return x%360.0
def jd_from_cal(y,m,d,ut_hours=0.0):
    if m<=2: y-=1; m+=12
    A=y//100; B=2-A+A//4
    jd=math.floor(365.25*(y+4716))+math.floor(30.6001*(m+1))+d+B-1524.5
    return jd+ut_hours/24.0
def jdn_noon(y,m,d): return int(jd_from_cal(y,m,d,12.0)+0.5)
def sun_lon(jd):
    T=(jd-2451545.0)/36525.0
    L0=norm(280.46646+36000.76983*T+0.0003032*T*T)
    M=norm(357.52911+35999.05029*T-0.0001537*T*T); Mr=R(M)
    C=(1.914602-0.004817*T-0.000014*T*T)*math.sin(Mr)+(0.019993-0.000101*T)*math.sin(2*Mr)+0.000289*math.sin(3*Mr)
    true=L0+C; om=125.04-1934.136*T
    lam=true-0.00569-0.00478*math.sin(R(om))
    return norm(lam), M
def obliquity(jd):
    T=(jd-2451545.0)/36525.0
    e=23.0+26.0/60+21.448/3600-(46.8150*T+0.00059*T*T-0.001813*T*T*T)/3600
    om=125.04-1934.136*T
    return e+0.00256*math.cos(R(om))
def eot_minutes(jd):
    T=(jd-2451545.0)/36525.0
    L0=norm(280.46646+36000.76983*T)
    lam,M=sun_lon(jd); eps=obliquity(jd)
    ra=D(math.atan2(math.cos(R(eps))*math.sin(R(lam)),math.cos(R(lam))))
    E=L0-0.0057183-ra; E=(E+180)%360-180
    return E*4.0
def moon_lon(jd):
    T=(jd-2451545.0)/36525.0
    Lp=norm(218.3164477+481267.88123421*T-0.0015786*T*T+T*T*T/538841-T**4/65194000)
    Dm=norm(297.8501921+445267.1114034*T-0.0018819*T*T+T*T*T/545868-T**4/113065000)
    M=norm(357.5291092+35999.0502909*T-0.0001536*T*T+T*T*T/24490000)
    Mp=norm(134.9633964+477198.8675055*T+0.0087414*T*T+T*T*T/69699-T**4/14712000)
    Fp=norm(93.2720950+483202.0175233*T-0.0036539*T*T-T*T*T/3526000+T**4/863310000)
    A1=norm(119.75+131.849*T); A2=norm(53.09+479264.290*T)
    E=1-0.002516*T-0.0000074*T*T
    terms=[(0,0,1,0,6288774),(2,0,-1,0,1274027),(2,0,0,0,658314),(0,0,2,0,213618),
    (0,1,0,0,-185116),(0,0,0,2,-114332),(2,0,-2,0,58793),(2,-1,-1,0,57066),
    (2,0,1,0,53322),(2,-1,0,0,45758),(0,1,-1,0,-40923),(1,0,0,0,-34720),
    (0,1,1,0,-30383),(2,0,0,-2,15327),(0,0,1,2,-12528),(0,0,1,-2,10980),
    (4,0,-1,0,10675),(0,0,3,0,10034),(4,0,-2,0,8548),(2,1,-1,0,-7888),
    (2,1,0,0,-6766),(1,0,-1,0,-5163),(1,1,0,0,4987),(2,-1,1,0,4036),
    (2,0,2,0,3994),(4,0,0,0,3861),(2,0,-3,0,3665),(0,1,-2,0,-2689),
    (2,0,-1,2,-2602),(2,-1,-2,0,2390),(1,0,1,0,-2348),(2,-2,0,0,2236),
    (0,1,2,0,-2120),(0,2,0,0,-2069),(2,-2,-1,0,2048)]
    s=0.0
    for dd,mm,mp,ff,c in terms:
        arg=R(dd*Dm+mm*M+mp*Mp+ff*Fp); e=E**abs(mm); s+=c*e*math.sin(arg)
    s+=3958*math.sin(R(A1))+1962*math.sin(R(Lp-Fp))+318*math.sin(R(A2))
    return norm(Lp+s/1e6)
ELEM={'earth':(1.00000261,0.00000562,0.01671123,-0.00004392,-0.00001531,-0.01294668,100.46457166,35999.37244981,102.93768193,0.32327364,0.0,0.0),
 'mercury':(0.38709927,0.00000037,0.20563593,0.00001906,7.00497902,-0.00594749,252.25032350,149472.67411175,77.45779628,0.16047689,48.33076593,-0.12534081),
 'venus':(0.72333566,0.00000390,0.00677672,-0.00004107,3.39467605,-0.00078890,181.97909950,58517.81538729,131.60246718,0.00268329,76.67984255,-0.27769418),
 'mars':(1.52371034,0.00001847,0.09339410,0.00007882,1.84969142,-0.00813131,-4.55343205,19140.30268499,-23.94362959,0.44441088,49.55953891,-0.29257343),
 'jupiter':(5.20288700,-0.00011607,0.04838624,-0.00013253,1.30439695,-0.00183714,34.39644051,3034.74612775,14.72847983,0.21252668,100.47390909,0.20469106),
 'saturn':(9.53667594,-0.00125060,0.05386179,-0.00050991,2.48599187,0.00193609,49.95424423,1222.49362201,92.59887831,-0.41897216,113.66242448,-0.28867794)}
JUP_C=0.06064060; JUP_S=-0.35635438; JUP_F=38.35125000; JUP_B=-0.00012452
def kepler(M,e):
    M=R(M); E=M+e*math.sin(M)
    for _ in range(50):
        dE=(E-e*math.sin(E)-M)/(1-e*math.cos(E)); E-=dE
        if abs(dE)<1e-9: break
    return E
def helio_xyz(body,T):
    a0,ad,e0,ed,I0,Id,L0,Ld,w0,wd,O0,Od=ELEM[body]
    a=a0+ad*T; e=e0+ed*T; I=I0+Id*T; L=L0+Ld*T; wbar=w0+wd*T; Om=O0+Od*T
    w=wbar-Om; M=L-wbar
    if body=='jupiter': M+=JUP_B*T*T+JUP_C*math.cos(R(JUP_F*T))+JUP_S*math.sin(R(JUP_F*T))
    M=(M+180)%360-180; E=kepler(M,e)
    xp=a*(math.cos(E)-e); yp=a*math.sqrt(1-e*e)*math.sin(E)
    Ir=R(I); Or=R(Om); wr=R(w)
    xecl=(math.cos(wr)*math.cos(Or)-math.sin(wr)*math.sin(Or)*math.cos(Ir))*xp+(-math.sin(wr)*math.cos(Or)-math.cos(wr)*math.sin(Or)*math.cos(Ir))*yp
    yecl=(math.cos(wr)*math.sin(Or)+math.sin(wr)*math.cos(Or)*math.cos(Ir))*xp+(-math.sin(wr)*math.sin(Or)+math.cos(wr)*math.cos(Or)*math.cos(Ir))*yp
    return xecl,yecl,0
def planet_geo_lon(body,jd):
    T=(jd-2451545.0)/36525.0
    xp,yp,_=helio_xyz(body,T); xe,ye,_=helio_xyz('earth',T)
    x=xp-xe; y=yp-ye
    lam2000=norm(D(math.atan2(y,x)))
    prec=(1.396971+0.0003086*T)*T
    return norm(lam2000+prec)
def jupiter_lon(jd): return planet_geo_lon('jupiter',jd)
def gmst_deg(jd):
    T=(jd-2451545.0)/36525.0
    th=280.46061837+360.98564736629*(jd-2451545.0)+0.000387933*T*T-T*T*T/38710000
    return norm(th)
def ascendant(jd,lat,lon_east):
    ramc=norm(gmst_deg(jd)+lon_east); eps=obliquity(jd)
    x=math.cos(R(ramc)); y=-(math.sin(R(ramc))*math.cos(R(eps))+math.tan(R(lat))*math.sin(R(eps)))
    return norm(D(math.atan2(x,y))), ramc
def sun_altitude(jd,lat,lon_east):
    lam,_=sun_lon(jd); eps=obliquity(jd)
    ra=math.atan2(math.cos(R(eps))*math.sin(R(lam)),math.cos(R(lam)))
    dec=math.asin(math.sin(R(eps))*math.sin(R(lam)))
    lst=R(norm(gmst_deg(jd)+lon_east)); H=lst-ra
    return D(math.asin(math.sin(R(lat))*math.sin(dec)+math.cos(R(lat))*math.cos(dec)*math.cos(H)))
SIGNS=['양자리','황소','쌍둥이','게','사자','처녀','천칭','전갈','사수','염소','물병','물고기']
def sign_of(lon): return int(lon//30)%12
def deg_in_sign(lon): return lon%30
STEMS=['갑','을','병','정','무','기','경','신','임','계']
BRANCHES=['자','축','인','묘','진','사','오','미','신','유','술','해']
def full(y,m,d,ch,cm,tz,lat,lon_e,place):
    ut=ch+cm/60.0-tz
    jd=jd_from_cal(y,m,d,0)+ut/24.0
    tst=ch+cm/60.0+(lon_e-tz*15)*4/60.0+eot_minutes(jd)/60.0
    lam,_=sun_lon(jd); gy=y
    if (m==1) or (m==2 and lam<315): gy=y-1
    yidx=(gy-4)%60; ystem=yidx%10; ybr=yidx%12
    mb=int(((lam-315)%360)//30); mbr=(2+mb)%12
    mstart={0:2,5:2,1:4,6:4,2:6,7:6,3:8,8:8,4:0,9:0}[ystem]
    mstem=(mstart+((mbr-2)%12))%10
    jdn=jdn_noon(y,m,d); didx=(jdn+49)%60; dstem=didx%10; dbr=didx%12
    hbr=int(((tst+1)//2))%12
    hstart={0:0,5:0,1:2,6:2,2:4,7:4,3:6,8:6,4:8,9:8}[dstem]
    hstem=(hstart+hbr)%10
    pillars={'연':(ystem,ybr),'월':(mstem,mbr),'일':(dstem,dbr),'시':(hstem,hbr)}
    sun,_=sun_lon(jd); moon=moon_lon(jd); jup=jupiter_lon(jd)
    asc,_=ascendant(jd,lat,lon_e); ascs=sign_of(asc)
    alt=sun_altitude(jd,lat,lon_e); day=alt>0
    print(f"입력: {place} {y}-{m:02d}-{d:02d} {ch:02d}:{cm:02d} KST (진태양시 {tst:.2f}h)")
    print("[사주 팔자] "+"  ".join(f"{p}주 {STEMS[st]}{BRANCHES[br]}" for p,(st,br) in pillars.items()))
    print(f"[네이탈] 태양 {SIGNS[sign_of(sun)]} {deg_in_sign(sun):.1f}° · 달 {SIGNS[sign_of(moon)]} {deg_in_sign(moon):.1f}° · 목성 {SIGNS[sign_of(jup)]} {deg_in_sign(jup):.1f}° · 어센 {SIGNS[ascs]} {deg_in_sign(asc):.1f}° · {'주간' if day else '야간'}")
    return pillars
if __name__=="__main__":
    av=sys.argv[1:]
    y,mo,d,hh,mm=[int(x) for x in av[:5]]
    tz=float(av[5]) if len(av)>5 else 9.0
    lat=float(av[6]) if len(av)>6 else 37.5665
    lon=float(av[7]) if len(av)>7 else 126.978
    place=av[8] if len(av)>8 else "서울"
    full(y,mo,d,hh,mm,tz,lat,lon,place)
