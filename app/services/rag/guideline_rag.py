import hashlib
import logging

from qdrant_client.models import PointStruct

from app.services.rag.client import get_client
from app.services.rag.embeddings import embed

logger = logging.getLogger(__name__)

_COLLECTION = "medical_guidelines"

GUIDELINE_DATA = [
    {
        "id": "hypertension_guideline",
        "title": "고혈압 치료 가이드라인",
        "category": "고혈압",
        "content": (
            "대한고혈압학회 2022년 고혈압 진료 지침 요약.\n"
            "혈압 분류: 정상 <120/80mmHg, 주의혈압 120~129/<80mmHg, "
            "고혈압 1기 130~139/80~89mmHg, 고혈압 2기 ≥140/90mmHg.\n"
            "목표 혈압: 일반 환자 <130/80mmHg, 당뇨/만성신장질환 <130/80mmHg, "
            "80세 이상 노인 <140/90mmHg.\n"
            "생활습관 개선: 나트륨 섭취 감소(하루 2g 이하), DASH 식이 요법, "
            "규칙적 유산소 운동(주 150분 이상, 중강도), 체중 감량(BMI 23 미만 유지), "
            "금연, 절주(남성 하루 2잔 이하, 여성 1잔 이하).\n"
            "약물 치료 1차 선택: ARB, ACE억제제, 칼슘채널차단제(CCB), 이뇨제(티아지드). "
            "당뇨 동반 시 ARB/ACE억제제 우선. 협심증 동반 시 베타차단제 추가. "
            "2제 병용 요법: ARB+CCB, ARB+이뇨제, CCB+이뇨제 조합 권장.\n"
            "추적 관리: 초기 1~3개월마다 혈압 측정, 안정 후 3~6개월마다 측정. "
            "전해질, 신기능, 혈당, 지질 검사 연 1회."
        ),
    },
    {
        "id": "diabetes_type2_guideline",
        "title": "제2형 당뇨병 관리 가이드라인",
        "category": "제2형 당뇨병",
        "content": (
            "대한당뇨병학회 2023년 당뇨병 진료 지침 요약.\n"
            "혈당 조절 목표: 당화혈색소(HbA1c) <6.5%(일반), <7.0%(개별화), "
            "공복혈당 80~130mg/dL, 식후 2시간 혈당 <180mg/dL.\n"
            "약물 치료: 1차 메트포르민(금기 없을 시), eGFR 30~45에서 용량 감량, "
            "eGFR <30에서 중단. 2차 약제: SGLT-2 억제제(심부전/신장질환 동반 시 우선), "
            "GLP-1 수용체 작용제(비만 동반 시 우선), DPP-4 억제제, 설폰요소제.\n"
            "생활습관: 탄수화물 에너지 비율 45~65%, 포화지방 7% 미만, "
            "주 150분 이상 중강도 유산소 운동 + 주 2~3회 근력 운동. "
            "표준체중 5~7% 감량 시 혈당 조절 현저히 개선.\n"
            "합병증 예방: 혈압 <130/80mmHg 유지, LDL 콜레스테롤 <70mg/dL(심혈관질환 동반), "
            "금연, 연 1회 미세단백뇨/망막 검사, 발 검사 매 방문마다.\n"
            "저혈당 대처: 혈당 <70mg/dL 시 속효성 탄수화물 15g 섭취 후 15분 재측정."
        ),
    },
    {
        "id": "chronic_pain_guideline",
        "title": "만성 통증 관리 가이드라인",
        "category": "만성통증",
        "content": (
            "대한통증학회 만성 비암성 통증 치료 가이드라인.\n"
            "정의: 3개월 이상 지속되는 통증으로 조직 손상의 예상 치유 기간을 초과.\n"
            "평가: VAS/NRS(0~10) 통증 척도, 통증 부위·성질·악화/완화 요인, "
            "기능 장애 및 삶의 질 평가, 심리사회적 요인(우울·불안·수면) 평가.\n"
            "비약물 치료(1차): 인지행동치료(CBT), 물리치료, 운동 치료(수중 운동, 저강도 유산소), "
            "경피적 전기신경자극(TENS), 마음챙김 명상.\n"
            "약물 치료: 1단계 아세트아미노펜(최대 4g/일), NSAIDs(단기, 위장관 보호제 병용), "
            "2단계 삼환계 항우울제(아미트립틸린 10~75mg/일), SNRI(둘록세틴 30~120mg/일), "
            "가바펜티노이드(가바펜틴, 프레가발린 — 신경병성 통증), "
            "3단계 약한 오피오이드(트라마돌 최대 400mg/일). "
            "강한 오피오이드는 다른 치료 실패 시 신중하게 사용.\n"
            "특수 치료: 신경차단술, 척수 자극술(SCS), 다학제적 통증 클리닉 의뢰."
        ),
    },
    {
        "id": "dyslipidemia_guideline",
        "title": "이상지혈증 관리 가이드라인",
        "category": "이상지혈증",
        "content": (
            "한국지질·동맥경화학회 2022년 이상지혈증 진료 지침.\n"
            "LDL 콜레스테롤 목표치: 초고위험군(기존 심혈관질환) <55mg/dL, "
            "고위험군(당뇨병, 중등도 이상 만성신장질환) <70mg/dL, "
            "중위험군(주요 위험 인자 2개 이상) <100mg/dL, 저위험군 <130mg/dL.\n"
            "생활습관: 포화지방 총 칼로리 7% 미만, 트랜스지방 최소화, "
            "식이 콜레스테롤 하루 200mg 미만, 수용성 식이섬유 10~25g/일, "
            "식물 스타놀/스테롤 2g/일, 오메가-3 지방산 섭취 권장.\n"
            "약물 치료: 스타틴(1차 선택) — 아토르바스타틴 10~80mg, 로수바스타틴 5~40mg. "
            "LDL 목표 미달성 시 에제티미브 추가(10mg/일). "
            "스타틴+에제티미브로도 목표 미달성 시 PCSK9 억제제 고려(초고위험군). "
            "중성지방 ≥500mg/dL: 피브레이트 또는 고용량 오메가-3 지방산.\n"
            "근육 부작용: 스타틴 복용 중 근육통 발생 시 CK 측정, "
            "CK >10×ULN 시 즉시 중단, 3~4배 상승 시 2~4주 모니터링."
        ),
    },
    {
        "id": "cardiovascular_prevention_guideline",
        "title": "심혈관질환 예방 가이드라인",
        "category": "심혈관 예방",
        "content": (
            "대한심장학회 심혈관질환 1·2차 예방 권고문.\n"
            "위험 인자: 고혈압, 당뇨병, 이상지혈증, 흡연, 비만, 가족력, 만성신장질환, 염증성 질환.\n"
            "1차 예방(기존 심혈관질환 없음): 10년 심혈관 위험도 계산(Framingham, SCORE). "
            "고위험군 항혈소판제(저용량 아스피린) — 출혈 위험 대비 이득 개별 평가. "
            "스타틴 고려(LDL >130mg/dL + 고위험군). 혈압 <130/80mmHg, 혈당 HbA1c <7% 목표.\n"
            "2차 예방(기존 심근경색/뇌졸중/관상동맥질환): "
            "아스피린 100mg/일(영구), 스타틴(고강도: 아토르바스타틴 40~80mg), "
            "ACE억제제/ARB(좌심실 기능 저하 시), 베타차단제(심근경색 후). "
            "스텐트 후 이중 항혈소판 요법(아스피린+P2Y12 차단제) 6~12개월.\n"
            "생활습관 중재: 금연(1년 내 위험도 50% 감소), "
            "지중해식 또는 DASH 식이, 주 150~300분 중강도 유산소 운동, "
            "심장 재활 프로그램 참여. 심리 지원(우울증 스크리닝).\n"
            "추적 관리: 심장 초음파, 운동 부하 검사, 지질·혈당 정기 검사."
        ),
    },
]


async def seed_guidelines() -> None:
    client = get_client()
    try:
        count_result = await client.count(collection_name=_COLLECTION)
        if count_result.count > 0:
            logger.info("Guidelines already seeded (%d docs). Skipping.", count_result.count)
            return
    except Exception as e:
        logger.warning("Failed to check guidelines count: %s", e)
        return

    points = []
    for guideline in GUIDELINE_DATA:
        text = f"{guideline['title']}\n{guideline['category']}\n{guideline['content']}"
        vector = await embed(text)
        if vector is None:
            continue
        point_id = int(hashlib.md5(guideline["id"].encode()).hexdigest()[:8], 16)
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "id": guideline["id"],
                    "title": guideline["title"],
                    "category": guideline["category"],
                    "content": guideline["content"],
                },
            )
        )

    if points:
        try:
            await client.upsert(collection_name=_COLLECTION, points=points)
            logger.info("Seeded %d medical guidelines.", len(points))
        except Exception as e:
            logger.warning("Failed to upsert guidelines: %s", e)


async def search_guidelines(query: str, limit: int = 2) -> str:
    vector = await embed(query)
    if vector is None:
        return ""

    client = get_client()
    try:
        response = await client.query_points(
            collection_name=_COLLECTION,
            query=vector,
            limit=limit,
            score_threshold=0.4,
        )
    except Exception as e:
        logger.warning("Guidelines search failed for query '%s': %s", query, e)
        return ""

    if not response.points:
        return ""

    results = []
    for hit in response.points:
        payload = hit.payload or {}
        results.append(f"[{payload.get('title', '')}]\n{payload.get('content', '')}")
    return "\n\n".join(results)
