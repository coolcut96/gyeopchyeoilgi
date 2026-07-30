# -*- coding: utf-8 -*-
"""
유료용 AI 붓 층 — 엔진 재료를 자연스러운 문장으로 옷 입히기.
원리: 엔진=진실(판정) / AI=붓(문장만). 계산·해석은 절대 AI에 안 넘김.
흐름: 재료 → 프롬프트(톤+가드레일) → Claude API → 금지어 사후 점검 → 실패 시 템플릿 강등.
"""
import os, re
import gyeopchyeoilgi as G

# ※ 2026-07 확인: Claude 3.5 Haiku는 (메인 API) 퇴역. 현행 최저가 = Claude Haiku 4.5.
MODEL_FREE = "claude-haiku-4-5"   # 값싼 하이쿠 (요금 $1/$5 per M). 정확한 모델 id는 API 문서 확인.
MODEL_PAID = "claude-haiku-4-5"

# ── 금지어 그물 (출력에 새면 안 되는 관법 용어) ──
FORBIDDEN = [
 '십성','비견','겁재','식신','상관','정재','편재','정관','편관','칠살','정인','편인',
 '신강','신약','득령','통근','지장간','일간','월령',
 '디트리먼트','디트리','도머사일','엑절테이션','컴버스트','언더선빔','카지미',
 '섹트','in-sect','out-of-sect','디그니티','바운드','프로펙션','피르다리아',
 '어센던트','어센','룰러','하우스','역행','텀',
 '목성','토성','화성','금성','수성',   # 비루미너리 별 이름(개인 리포트에 나올 일 없음)
]
def leak_check(text):
    hits = [w for w in FORBIDDEN if w in text]
    if re.search(r'\d\s*하우스', text): hits.append('N하우스')
    return sorted(set(hits))

# ── 재료를 '쉬운 말 building block'으로 (LLM 입력) ──
def material_brief(a, tier='유료', time_unknown=False):
    dom, sk, dsc, find, cats = a['dom'], a['sinkang'], a['dsc'], a['find'], a['cats']; dom2 = a.get('dom2')
    L = []
    L.append(f"- 자기 힘: {'단단하고 잘 안 흔들림' if sk else '주변에 유연하게 맞춤'}")
    L.append(f"- 주 강점: {G.DOM_STRENGTH[dom]}" + (f" + {G.DOM_STRENGTH[dom2]}(나란히)" if dom2 else ""))
    L.append(f"- 삶의 기울기: {G.DOM_TXT[dom]}")
    if cats['比劫'] >= 2: L.append("- 겨룸·경쟁이 자주 따라붙음")
    for k, t in find:
        if t == '밖으로 나가는 힘':
            L.append("- 사주·점성술 두 방식이 함께 강조하는 강점: 일과 사회적 성취(커리어) — 직업적 인정·자기 위치 만들기·눈에 보이는 성과. ※'밖에서 자리를 잡는 힘' 같은 추상적 표현 말고 '일·커리어·성취'로 구체적으로 풀 것")
        if t == '밖으로 나가는 방식':
            L.append(f"- 그 방식도 둘 다 강조: {G.TERM_COLOR[dsc['사회적 위상'][2]]}")
        if t == '자기 힘' and not time_unknown:
            if sk:
                L.append("- 겉과 속: 겉은 강하게 밀고 나가도 속은 신중하게 되짚는 사람. 약점이 아니라 밀어붙이는 힘과 신중함을 한 몸에 지님")
            else:
                L.append("- 겉과 속: 겉은 부드럽고 유연해 보여도 안에는 생각보다 단단한 심지가 있는 사람. 상황에 따라 부드러움과 단단함을 오감")
    if not any(t == '밖으로 나가는 힘' for _, t in find):
        best = max([d for d in dsc if d != '사회적 위상' and not (time_unknown and d == '속마음·기질')],
                   key=lambda d: dsc[d][0], default=None)
        if best and dsc[best][0] >= 1:
            L.append(f"- 영역 중 가장 단단: {G.DOM_NAME.get(best,best)}")
    if tier == '유료':
        for g, (s, l, tl) in dsc.items():
            if g == '사회적 위상' or (time_unknown and g == '속마음·기질'): continue
            L.append(f"- {G.DOM_NAME.get(g,g)}: {l} / {G.TERM_COLOR[tl]} 방식")
        for ln in G.advice_lines(a, time_unknown):
            L.append("- 조언: " + ln)
    if time_unknown:
        L.append("- ※시각 모름: 태어난 시각을 몰라 정오(낮 12시) 기준으로 봄. 속마음·기질의 세부와 겉으로 드러나는 첫인상은 확정이 아니니, 리포트 맨 끝에 '태어난 시각을 몰라 정오 기준으로 보았고, 시각에 따라 달라지는 부분은 참고로만 봐 달라'는 안내를 한 줄 담을 것")
    return "\n".join(L)

# ── 프롬프트 (톤 + 가드레일) ──
def build_prompt(brief, tier):
    length = "8~12문장으로 넉넉하고 입체적으로 쓰고, 마지막에 '활용 조언' 문단을 따로 둔다" if tier == '유료' else "4~5문장으로 짧게"
    return f"""당신은 「겹쳐읽기」 운세 리포트의 문장을 다듬는 작가입니다.
아래 [판정 재료]는 이미 확정된 사실입니다. 이 내용을 자연스럽고 또렷한 한국어 리포트 문장으로 옮기세요.

[판정 재료]
{brief}

[규칙 — 반드시 지킬 것]
0. 맨 앞에 제목 한 줄을 '## 사주와 점성술로 교차 검토한 당신'으로 넣는다.
1. 재료에 있는 내용만 쓴다. 새로운 해석·사실을 지어내지 않는다.
2. 전문 용어 절대 금지: 십성·처지·하우스·역행·별 이름(목성 등)·신강 같은 말을 쓰지 않는다. 재료의 뜻을 오직 쉬운 일상어로만 옮긴다.
2-1. 점성술 쪽을 가리킬 땐 '별로 보면'이 아니라 '점성술로 보면'이라고 쓴다. 두 체계는 '사주'와 '점성술'로 부른다.
3. 톤: 상담가가 눈앞에서 차분히 설명하듯. 구체적이고 바로 알아듣게. 시적·모호한 표현(결·자리·되짚는 남발) 피한다.
3-1. 각 영역(인정과 명예·감정과 일상·속마음 등)은 서로 다른 표현으로, 같은 단어를 반복하지 말고 편안하게 풀어 쓴다.
4. 명확하고 자신 있게 쓴다. 과한 유보('확정은 아니고 참고로요' 같은 표현)는 넣지 않는다. 성격·강점은 단정적으로 짚되, 미래 사건을 예언하지는 않는다.
4-1. 이 풀이는 '타고난 성격·경향성'을 보는 것이지 특정 시기·운세가 아니다. '지금은 / 올해는 / 요즘 / 이 시기엔 / 앞으로 한동안 / ~하는 시기예요' 같은 시간 표현을 절대 쓰지 말고, 늘 그러한 경향으로 서술한다. 조언도 '지금 이렇게 하라'가 아니라 '이런 사람이니 이렇게 살면 좋다'로.
5. 2인칭("당신은")으로 쓴다.
6. '조언' 항목들은 명령이 아니라 따뜻한 권유로 풀어 한 문단 이상으로 넉넉히 담는다.
7. 분량: {length}.
8. 맨 끝 한 문단: 이 풀이가 「겹쳐읽기」의 시선이며, 왜 그런지·그 원리는 아래 소개하는 책들에 담겨 있다는 담백한 안내(강매 아님). 존재하지 않는 특정 책 제목을 지어내지 말 것.

리포트 본문만 출력하세요."""

# ── AI 렌더 (호출 + 점검) ──
def ai_render(a, tier='유료', api_key=None, model=None, time_unknown=False):
    api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None                      # 키 없음 → 상위에서 템플릿 강등
    try:
        import anthropic
    except ImportError:
        return None
    model = model or (MODEL_PAID if tier == '유료' else MODEL_FREE)
    prompt = build_prompt(material_brief(a, tier, time_unknown), tier)
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(model=model, max_tokens=2500, temperature=0.4,
                                     messages=[{"role": "user", "content": prompt}])
        text = msg.content[0].text.strip()
    except Exception as e:
        return {'error': str(e)}
    return {'text': text, 'leaks': leak_check(text)}

# ── 최종 리포트 (유료=AI 우선, 실패·누출 시 템플릿) ──
def final_report(a, tier='유료', api_key=None, time_unknown=False):
    # 무료·유료 모두 AI 붓 우선 (무료는 값싼 모델). 실패·누출 시 템플릿 폴백.
    r = ai_render(a, tier, api_key, time_unknown=time_unknown)
    if r and 'text' in r and not r['leaks']:
        return r['text'], 'AI 붓'
    if r and r.get('leaks'):
        return G.render(a, tier, time_unknown=time_unknown), f"템플릿(강등: AI 출력에 금지어 {r['leaks']})"
    if r and r.get('error'):
        return G.render(a, tier, time_unknown=time_unknown), "템플릿(강등: API 오류)"
    return G.render(a, tier, time_unknown=time_unknown), '템플릿(오프라인)'

# ══════════ 데모 ══════════
if __name__ == '__main__':
    case = dict(
        palja=[('정','사'),('임','자'),('계','축'),('무','오')],
        asc=('양자리',13.16), day=True,
        natal={'목성':('게',1.19,None,True),'태양':('염소',0.20,None,False),
               '달':('황소',23.64,None,False),'화성':('사자',10.97,None,True),
               '토성':('처녀',0.44,None,True),'금성':('사수',22.76,None,False),'수성':('사수',28.81,None,True)})
    a = G.analyze(case)

    print("【1】 LLM에 넘길 재료 (이미 쉬운 말, 관법 용어 없음)")
    print(material_brief(a))

    print("\n【2】 실제로 보내는 프롬프트 (유료)")
    print(build_prompt(material_brief(a), '유료'))

    print("\n【3】 금지어 사후 점검 자가 테스트")
    clean = "당신은 자기 확신이 뚜렷한 사람이에요. 밖에서 자리를 잡는 힘이 강합니다."
    leaky = "당신의 목성은 고양이라 사회적 위상이 좋고, 신강한 사주라 3하우스가 강합니다."
    print(f"  깨끗한 문장 → 누출 {leak_check(clean)}")
    print(f"  새는 문장   → 누출 {leak_check(leaky)}")

    print("\n【4】 최종 리포트 (키 없음 → 템플릿 강등 확인)")
    text, path = final_report(a, '유료')
    print(f"  경로: {path}\n")
    print(text)
