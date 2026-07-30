# -*- coding: utf-8 -*-
"""
겹쳐읽기 풀이 프로그램 (통합 MVP)
입력(구조화) → 확인 관문 → 판정 → 매칭·겹침 → 리포트(무료/유료 템플릿)
* 점성 좌표: 사인 + 정확한 도수(텀·오브 계산에 필요). 이미지→이 표는 사람이 확인.
* 사주: 팔자 8자 글자.
"""

# ══════════ 테이블 ══════════
STEM_OH={'갑':'목','을':'목','병':'화','정':'화','무':'토','기':'토','경':'금','신':'금','임':'수','계':'수'}
STEM_YY={'갑':'양','병':'양','무':'양','경':'양','임':'양','을':'음','정':'음','기':'음','신':'음','계':'음'}
BR_OH={'자':'수','축':'토','인':'목','묘':'목','진':'토','사':'화','오':'화','미':'토','신':'금','유':'금','술':'토','해':'수'}
BR_MAIN={'자':'계','축':'기','인':'갑','묘':'을','진':'무','사':'병','오':'정','미':'기','신':'경','유':'신','술':'무','해':'임'}
SIGNS=['양자리','황소','쌍둥이','게','사자','처녀','천칭','전갈','사수','염소','물병','물고기']
SHENG={'목':'화','화':'토','토':'금','금':'수','수':'목'}; KE={'목':'토','토':'수','수':'화','화':'금','금':'목'}
RULER={'양자리':'화성','황소':'금성','쌍둥이':'수성','게':'달','사자':'태양','처녀':'수성','천칭':'금성','전갈':'화성','사수':'목성','염소':'토성','물병':'토성','물고기':'목성'}
DIGNITY={'태양':{'제집':{'사자'},'고양':{'양자리'},'디트리먼트':{'물병'},'폴':{'천칭'}},'달':{'제집':{'게'},'고양':{'황소'},'디트리먼트':{'염소'},'폴':{'전갈'}},'수성':{'제집':{'쌍둥이','처녀'},'고양':{'처녀'},'디트리먼트':{'사수','물고기'},'폴':{'물고기'}},'금성':{'제집':{'황소','천칭'},'고양':{'물고기'},'디트리먼트':{'전갈','양자리'},'폴':{'처녀'}},'화성':{'제집':{'양자리','전갈'},'고양':{'염소'},'디트리먼트':{'천칭','황소'},'폴':{'게'}},'목성':{'제집':{'사수','물고기'},'고양':{'게'},'디트리먼트':{'쌍둥이','처녀'},'폴':{'염소'}},'토성':{'제집':{'염소','물병'},'고양':{'천칭'},'디트리먼트':{'게','사자'},'폴':{'양자리'}}}
TERMS={'양자리':[(6,'목성'),(12,'금성'),(20,'수성'),(25,'화성'),(30,'토성')],'황소':[(8,'금성'),(14,'수성'),(22,'목성'),(27,'토성'),(30,'화성')],'쌍둥이':[(6,'수성'),(12,'목성'),(17,'금성'),(24,'화성'),(30,'토성')],'게':[(6,'화성'),(13,'금성'),(20,'수성'),(27,'목성'),(30,'토성')],'사자':[(6,'목성'),(11,'금성'),(18,'토성'),(24,'수성'),(30,'화성')],'처녀':[(7,'수성'),(17,'금성'),(21,'목성'),(28,'화성'),(30,'토성')],'천칭':[(6,'토성'),(11,'금성'),(19,'수성'),(24,'목성'),(30,'화성')],'전갈':[(6,'화성'),(14,'목성'),(21,'금성'),(27,'수성'),(30,'토성')],'사수':[(8,'목성'),(14,'금성'),(19,'수성'),(25,'토성'),(30,'화성')],'염소':[(7,'수성'),(14,'목성'),(22,'금성'),(26,'토성'),(30,'화성')],'물병':[(7,'수성'),(13,'금성'),(20,'목성'),(25,'화성'),(30,'토성')],'물고기':[(12,'금성'),(16,'목성'),(19,'수성'),(28,'화성'),(30,'토성')]}
TERM_COLOR={'화성':'앞장서서 밀어붙이고 경쟁하는','금성':'조화롭게 관계로 풀어가는','수성':'말과 헤아림·실무로 다지는','목성':'크게 넓히고 너그럽게 품는','토성':'진중하게 참고 견디는'}
CAT={'비견':'比劫','겁재':'比劫','식신':'食傷','상관':'食傷','정재':'財','편재':'財','정관':'官','편관':'官','정인':'印','편인':'印'}

# ══════════ 판정 함수 ══════════
def sipsin(day,t):
    do,to=STEM_OH[day],STEM_OH[t]; s=STEM_YY[day]==STEM_YY[t]
    if do==to: return '비견' if s else '겁재'
    if SHENG[do]==to: return '식신' if s else '상관'
    if SHENG[to]==do: return '편인' if s else '정인'
    if KE[do]==to: return '편재' if s else '정재'
    return '편관' if s else '정관'
def cheoji(pl,sg):
    g=[k for k,v in DIGNITY[pl].items() if sg in v]; return g if g else ['평범']
def term_lord(sg,dg):
    for hi,l in TERMS[sg]:
        if dg<hi: return l
    return TERMS[sg][-1][1]
def sect(pl,day): return '중립' if pl=='수성' else ('in-sect' if((pl in{'태양','목성','토성'})==day) else 'out-of-sect')
def ang(h): return '앵글' if h in(1,4,7,10) else('석시던트' if h in(2,5,8,11) else'케이던트')
def house_of(sg,asc): return (SIGNS.index(sg)-SIGNS.index(asc))%12+1
def score(dig,se,h,comb=None):
    s=sum({'제집':2,'고양':2,'평범':0,'디트리먼트':-2,'폴':-2}[d] for d in dig)
    return s+{'in-sect':1,'out-of-sect':-1,'중립':0}[se]+(1 if ang(h)=='앵글' else 0)-(2 if comb=='컴버스트' else 0)
def lab(s): return '든든' if s>=3 else('무던~약간 든든' if s>=1 else('무던' if s==0 else('눌림' if s>-3 else'강하게 눌림')))

# ══════════ 파이프라인 ══════════
def analyze(case):
    palja=case['palja']; day=palja[2][0]; asc=case['asc']; is_day=case['day']; natal=case['natal']
    cats={'印':0,'食傷':0,'財':0,'官':0,'比劫':0}
    for i,(g,b) in enumerate(palja):
        if i!=2: cats[CAT[sipsin(day,g)]]+=1
        cats[CAT[sipsin(day,BR_MAIN[b])]]+=1
    ranked=sorted(cats.items(), key=lambda kv: kv[1], reverse=True)
    dom=ranked[0][0]; dom2=ranked[1][0] if (ranked[1][1]==ranked[0][1] and ranked[0][1]>=2) else None
    do=STEM_OH[day]; mo=BR_OH[palja[1][1]]
    deuk=2 if(mo==do or SHENG[mo]==do) else -1; tong=sum(1 for _,b in palja if BR_OH[b]==do or SHENG[BR_OH[b]]==do)
    sinkang=(deuk+tong+cats['比劫']+cats['印']-(cats['財']+cats['官']+cats['食傷'])*0.5)>0
    dsc={}
    for gung,pl in [('사회적 위상','목성'),('개인 권위','태양'),('일상·감정','달'),('속마음·기질','ASC')]:
        if pl=='ASC':
            sg,dg=asc; rp=RULER[sg]; rsg,rdg,comb,rt=natal[rp]
            s=score(cheoji(rp,rsg),sect(rp,is_day),house_of(rsg,asc[0]),comb); tl=term_lord(sg,dg)
        else:
            sg,dg,comb,rt=natal[pl]; s=score(cheoji(pl,sg),sect(pl,is_day),house_of(sg,asc[0]),comb); tl=term_lord(sg,dg)
        dsc[gung]=(s,lab(s),tl)
    self_s=dsc['속마음·기질'][0]; find=[]
    if not((sinkang and self_s>0) or (not sinkang and self_s<0)):
        find.append(('어긋남','자기 힘'))
    outer=(dsc['사회적 위상'][0]+dsc['개인 권위'][0])/2
    if dom in('財','官','食傷') and outer>0: find.append(('포갬','밖으로 나가는 힘'))
    if dsc['사회적 위상'][2]=='화성' and (cats['比劫']>=2 or dom=='財'): find.append(('포갬','밖으로 나가는 방식'))
    return dict(cats=cats,dom=dom,dom2=dom2,sinkang=sinkang,dsc=dsc,find=find)

# ══════════ 템플릿 렌더러 ══════════
DOM_TXT={'財':'삶이 성과와 실리 쪽으로 기울어, 손에 쥐고 이뤄내는 데 관심이 많은 편이에요.','官':'책임과 의무를 앞자리에 두고, 마땅히 해야 할 것을 먼저 짊어지는 편이에요.','印':'배우고 받쳐 주는 힘 안에서 차분히 자라는 결이 강해요.','食傷':'표현하고 뻗어 나가며 자기를 드러내는 편이에요.','比劫':'스스로 서고 겨루며 나아가는 힘이 강해요.'}
DOM_STRENGTH={'印':'배우고 흡수하는 힘','食傷':'표현하고 드러내는 재주','財':'실리를 챙기고 이뤄내는 힘','官':'책임지고 자기를 다스리는 힘','比劫':'스스로 서고 밀고 나가는 힘'}
FORM_TXT={'든든':'든든하게 자리 잡았고','무던~약간 든든':'무던하게 서 있고','무던':'무던하고','눌림':'다소 눌려 있고','강하게 눌림':'꽤 눌려 있고'}
DOM_NAME={'개인 권위':'인정과 명예','일상·감정':'감정과 일상','속마음·기질':'속마음과 타고난 성향'}
STRENGTH={'든든':['탄탄하게 자리 잡고 있어요','아주 든든해요'],
 '무던~약간 든든':['제법 안정적이에요','무난하게 자리 잡고 있어요'],
 '무던':['크게 튀지 않고 담담해요','무난한 편이에요'],
 '눌림':['겉보다 조금 조심스러운 편이에요','살짝 눌려 있는 편이에요'],
 '강하게 눌림':['다소 억눌려 있어요','제법 눌려 있는 편이에요']}
STYLE={'화성':'앞장서서 밀어붙이는','금성':'부드럽게 관계로 풀어가는','수성':'말과 헤아림으로 차근차근 다지는','목성':'크게 품고 넉넉하게 가는','토성':'묵묵히 참고 견디는'}

def josa(w,a,b):
    c=w[-1]
    return a if (('가'<=c<='힣') and (ord(c)-0xAC00)%28!=0) else b

def advice_lines(a, time_unknown=False):
    dom,cats,dsc,find=a['dom'],a['cats'],a['dsc'],a['find']
    L=[]
    if any(t=='밖으로 나가는 힘' for _,t in find):
        L.append("일과 커리어에서 자리를 만드는 힘은 확실하니, 망설이지 말고 앞에 나서세요. 당신은 성과로 증명하는 자리, 주목받는 위치에서 더 살아납니다.")
    if dom=='財':
        if cats['比劫']>=2:
            L.append("혼자 다 거머쥐려 하기보다 겨루던 사람들과 함께 크는 판을 만들면, 그 추진력이 훨씬 오래갑니다.")
        else:
            L.append("여러 개를 한꺼번에 벌이기보다 하나에 힘을 몰아 끝을 보는 편이, 당신에겐 성과가 큽니다.")
    if dom=='比劫':
        L.append("자기 힘으로 판을 만드는 사람이니, 남의 틀에 맞추기보다 스스로 주도권을 쥐는 자리를 택하세요. 뚝심은 큰 강점이지만, 혼자 다 짊어지기보다 곁의 사람과 힘을 나누면 그 힘이 훨씬 오래갑니다.")
    if dsc['사회적 위상'][2]=='화성':
        L.append("밀어붙이는 방식이 잘 맞지만, 속도를 한 박자 늦춰 상대를 살피면 같은 힘으로 더 멀리 갑니다.")
    if (not time_unknown) and any(t=='자기 힘' for _,t in find):
        L.append("겉으로 보이는 모습과 속마음이 조금 다른 편이니, 큰 결정 앞에서는 겉의 기세나 분위기에 떠밀리지 말고 속마음을 충분히 들여다보세요.")
    if dsc.get('일상·감정',(0,))[0] > 0:
        L.append("감정의 바탕이 단단하니, 주변이 흔들릴 때 오히려 당신이 중심을 잡아 주는 자리에 서면 좋습니다.")
    if (not time_unknown) and dsc.get('속마음·기질',(0,))[0] < 0:
        L.append("결정을 혼자 안으로 삭이기보다 믿는 사람에게 소리 내어 정리하면, 마음이 한결 가벼워집니다.")
    return L

def render(a, tier='유료', time_unknown=False):
    dom,cats,sk,dsc,find=a['dom'],a['cats'],a['sinkang'],a['dsc'],a['find']; dom2=a.get('dom2')
    P=["## 사주와 점성술로 교차 검토한 당신"]
    who = "자기 확신이 뚜렷하고, 웬만해선 남에게 휘둘리지 않는 사람입니다" if sk else "주변을 살피며 유연하게 움직이는 사람입니다"
    line = f"당신은 {who}. {DOM_TXT[dom]}"
    if cats['比劫']>=2: line += " 그만큼 비슷한 사람들과 같은 것을 두고 겨루는 자리에 자주 서게 됩니다."
    P.append(line)
    for k,t in find:
        if t=='밖으로 나가는 힘':
            P.append("사주로 봐도 점성술로 봐도, 당신의 가장 뚜렷한 강점은 **일과 사회적 성취 — 커리어**입니다. 직업적으로 인정받고, 자기 위치를 만들고, 눈에 보이는 성과를 내는 쪽으로 확실히 강합니다. 사람들 앞에 서는 자리, 성과로 증명하는 자리가 당신에게 잘 맞습니다.")
        if t=='밖으로 나가는 방식' and tier=='유료':
            P.append(f"일을 밀고 나가는 방식도 분명합니다 — {TERM_COLOR[dsc['사회적 위상'][2]]} 쪽입니다.")
    if not any(t=='밖으로 나가는 힘' for _,t in find):
        s=f"가장 또렷한 강점은 **{DOM_STRENGTH[dom]}**이에요"
        if dom2: s+=f". 거기에 **{DOM_STRENGTH[dom2]}**도 나란히 있고요"
        best=max([d for d in dsc if d!='사회적 위상' and not(time_unknown and d=='속마음·기질')], key=lambda d: dsc[d][0], default=None)
        if best and dsc[best][0]>=1: s+=f". 영역으로 보면 {DOM_NAME.get(best,best)} 쪽이 그중 가장 단단합니다"
        P.append(s+".")
    if tier=='유료':
        seg=[]; i=0
        for g,(s,l,tl) in dsc.items():
            if g=='사회적 위상' or (time_unknown and g=='속마음·기질'): continue
            nm=DOM_NAME.get(g,g); stand=STRENGTH[l][i%2]; j=josa(nm,'은','는')
            if s<0:
                seg.append(f"**{nm}**{j} {stand}. 그럴 땐 {STYLE[tl]} 식으로 풀어내려는 편이고요.")
            else:
                seg.append(f"**{nm}**{j} {stand}. {STYLE[tl]} 쪽이에요.")
            i+=1
        P.append(" ".join(seg))
    if (not time_unknown) and any(t=='자기 힘' for _,t in find):
        if sk:
            P.append("한 결을 더 짚자면, 당신은 **겉은 강하게 밀고 나가도 속은 신중하게 되짚는** 사람입니다. 사주는 심지의 단단함을, 점성술은 그 안쪽의 조심스러움을 가리킵니다. 둘이 어긋난 게 아니라, 밀어붙이는 힘과 신중함을 한 몸에 지녔다는 뜻입니다.")
        else:
            P.append("한 결을 더 짚자면, 당신은 **겉으론 부드럽고 유연해 보여도 안에는 생각보다 단단한 심지가 있는** 사람입니다. 사주는 그 유연함을, 점성술은 안쪽의 야무진 힘을 가리킵니다. 겉과 속이 달라 보이지만, 상황에 따라 부드러움과 단단함을 오갈 줄 안다는 뜻입니다.")
    if tier=='유료':
        adv=advice_lines(a, time_unknown)
        if adv:
            P.append("**삶에 이렇게 써 보세요.** " + " ".join(adv))
    if time_unknown:
        P.append("※ 태어난 시각을 몰라 정오(낮 12시) 기준으로 보았습니다. 시각에 따라 달라지는 부분 — 속마음·기질의 세부, 겉으로 드러나는 첫인상 — 은 참고로만 봐 주세요.")
    P.append("---")
    P.append("*이 풀이는 「겹쳐읽기」의 시선으로, 사주 기둥과 별 차트를 나란히 포개어 짚었습니다. 두 시계가 왜 같은 자리를 가리키는지 — 그 원리는 아래 소개하는 책들에 담아두었습니다.*")
    return "\n\n".join(P)

def confirm_gate(case):
    print("【확인 관문】 아래 값이 정본과 맞는지 눈으로 확인하세요 (사인 + 도수):")
    print(f"  어센 {case['asc'][0]} {case['asc'][1]}° · 차트 {'주간' if case['day'] else '야간'}")
    for pl,(sg,dg,comb,rt) in case['natal'].items():
        print(f"  {pl} {sg} {dg}°{' ℞' if rt else ''}{'  '+comb if comb else ''}")
    print(f"  팔자 "+" ".join(g+b for g,b in case['palja']))
    print("-"*56)

# ══════════ 실행 (샘플=실입력) ══════════
if __name__=='__main__':
    case=dict(
        palja=[('정','사'),('임','자'),('계','축'),('무','오')],
        asc=('양자리',13.16), day=True,
        natal={'목성':('게',1.19,None,True),'태양':('염소',0.20,None,False),
               '달':('황소',23.64,None,False),'화성':('사자',10.97,None,True),
               '토성':('처녀',0.44,None,True),'금성':('사수',22.76,None,False),'수성':('사수',28.81,None,True)})
    confirm_gate(case)
    a=analyze(case)
    for tier in ('무료','유료'):
        print(f"\n{'='*56}\n[{tier} 버전]\n{'='*56}")
        print(render(a,tier))
