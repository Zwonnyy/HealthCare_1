import hashlib
import logging

from qdrant_client.models import PointStruct

from app.services.rag.client import get_client
from app.services.rag.embeddings import embed

logger = logging.getLogger(__name__)

_COLLECTION = "drug_info"

DRUG_DATA = [
    {
        "id": "amlodipine",
        "name": "암로디핀 (Amlodipine)",
        "category": "칼슘채널차단제 / 고혈압약",
        "info": (
            "암로디핀은 칼슘채널을 차단하여 혈관을 이완시키고 혈압을 낮추는 항고혈압제입니다. "
            "주요 적응증: 고혈압, 안정형 협심증, 혈관경련성 협심증. "
            "일반 용량: 1일 1회 5~10mg 경구 복용. "
            "흔한 부작용: 발목 부종(10~20%), 두통, 홍조, 어지러움, 피로감. "
            "심각한 부작용: 저혈압, 심박수 증가, 간기능 이상(드물게). "
            "상호작용: CYP3A4 억제제(케토코나졸, 클라리스로마이신)와 병용 시 암로디핀 혈중 농도 상승 위험. "
            "심바스타틴과 병용 시 심바스타틴 용량 20mg 이하로 제한 권장 (심바스타틴 혈중 농도 최대 77% 상승). "
            "주의사항: 자몽 주스 섭취 피하기, 갑자기 복용 중단 금지."
        ),
    },
    {
        "id": "losartan",
        "name": "로사르탄 (Losartan)",
        "category": "ARB / 고혈압약",
        "info": (
            "로사르탄은 안지오텐신 II 수용체 차단제(ARB)로서 혈압을 낮추고 신장을 보호합니다. "
            "주요 적응증: 고혈압, 당뇨병성 신증, 좌심실 비대. "
            "일반 용량: 1일 1회 50~100mg 경구 복용. "
            "흔한 부작용: 어지러움, 저혈압, 고칼륨혈증, 피로감. "
            "심각한 부작용: 혈관부종(드물게), 신기능 악화, 태아 독성(임신 중 금기). "
            "상호작용: ACE 억제제와 병용 금기(이중 레닌-안지오텐신 차단). "
            "NSAIDs(이부프로펜 등)와 병용 시 항고혈압 효과 감소 및 신기능 저하 위험. "
            "칼륨 보충제 또는 칼륨 보존 이뇨제와 병용 시 고칼륨혈증 위험. "
            "리튬과 병용 시 리튬 독성 증가. "
            "주의사항: 임신 중 절대 금기, 신기능 정기 모니터링 필요."
        ),
    },
    {
        "id": "metformin",
        "name": "메트포르민 (Metformin)",
        "category": "바이구아나이드 / 당뇨병약",
        "info": (
            "메트포르민은 제2형 당뇨병의 1차 치료제로 간에서의 포도당 생성을 억제하고 인슐린 감수성을 향상시킵니다. "
            "주요 적응증: 제2형 당뇨병, 인슐린 저항성, PCOS. "
            "일반 용량: 1일 2~3회 500~1000mg 식사와 함께 복용. "
            "흔한 부작용: 오심, 구토, 설사, 복통(복용 초기), 식욕 감소. "
            "심각한 부작용: 유산산증(드물지만 치명적 — 신기능 저하 환자에서 위험 증가). "
            "상호작용: 요오드 조영제 사용 전 48시간 중단 필요(유산산증 위험). "
            "알코올과 병용 시 유산산증 위험 증가. "
            "시메티딘과 병용 시 메트포르민 혈중 농도 상승. "
            "주의사항: eGFR 30 미만에서 금기, 수술 전 중단, 비타민 B12 결핍 모니터링."
        ),
    },
    {
        "id": "aspirin",
        "name": "아스피린 (Aspirin)",
        "category": "살리실산계 / 항혈소판제 / 해열진통제",
        "info": (
            "아스피린은 COX-1/COX-2를 비가역적으로 억제하는 비스테로이드성 항염증제(NSAID)이자 항혈소판제입니다. "
            "주요 적응증: 심근경색 및 뇌졸중 예방(저용량), 통증/발열 완화(고용량), 관절염. "
            "일반 용량: 항혈소판 목적 100mg/일, 진통/해열 500~1000mg 4~6시간마다. "
            "흔한 부작용: 위장관 자극, 오심, 소화불량, 출혈 시간 연장. "
            "심각한 부작용: 위장관 출혈, 뇌출혈(고용량), 살리실산 중독, 라이 증후군(소아). "
            "상호작용: 와파린과 병용 시 출혈 위험 매우 증가(INR 모니터링 필수). "
            "클로피도그렐과 이중 항혈소판 요법 — 출혈 위험 증가하나 심장 스텐트 환자에서 병용 권장. "
            "NSAIDs(이부프로펜)와 동시 복용 시 아스피린의 항혈소판 효과 감소. "
            "메토트렉세이트 독성 증가. "
            "주의사항: 공복 복용 피하기, 음주 자제, 알레르기 환자 주의."
        ),
    },
    {
        "id": "omeprazole",
        "name": "오메프라졸 (Omeprazole)",
        "category": "양성자펌프억제제 (PPI)",
        "info": (
            "오메프라졸은 양성자펌프를 억제하여 위산 분비를 강력하게 감소시키는 PPI입니다. "
            "주요 적응증: 위궤양, 십이지장궤양, GERD(역류성 식도염), H.pylori 제균 요법. "
            "일반 용량: 1일 1회 20~40mg 식사 30분 전 복용. "
            "흔한 부작용: 두통, 설사, 복통, 오심, 복부팽만. "
            "장기 부작용: 마그네슘 결핍, 비타민 B12 흡수 감소, 골다공증 위험 증가, C.difficile 감염 위험. "
            "상호작용: 클로피도그렐과 병용 시 클로피도그렐 항혈소판 효과 감소(CYP2C19 억제). "
            "메토트렉세이트 혈중 농도 상승 가능. "
            "아타자나비르/넬피나비르 흡수 감소. "
            "주의사항: 장기 복용 시 골밀도 검사 권장, 마그네슘 수치 모니터링."
        ),
    },
    {
        "id": "simvastatin",
        "name": "심바스타틴 (Simvastatin)",
        "category": "스타틴 / 이상지혈증약",
        "info": (
            "심바스타틴은 HMG-CoA 환원효소를 억제하여 콜레스테롤 합성을 감소시키는 스타틴 계열 약물입니다. "
            "주요 적응증: 고콜레스테롤혈증, 심혈관질환 예방. "
            "일반 용량: 1일 1회 20~40mg 저녁에 복용. "
            "흔한 부작용: 근육통, 두통, 복통, AST/ALT 상승. "
            "심각한 부작용: 횡문근융해증(드물지만 신부전 유발 가능), 간독성. "
            "상호작용: 암로디핀과 병용 시 심바스타틴 용량 20mg 이하 제한. "
            "CYP3A4 강력 억제제(이트라코나졸, 케토코나졸, HIV 프로테아제 억제제)와 병용 금기. "
            "자몽 주스 섭취 시 혈중 농도 증가. "
            "피브레이트(젬피브로질)와 병용 시 근병증 위험 크게 증가. "
            "와파린 효과 증가 가능(INR 모니터링). "
            "주의사항: 간기능 검사 정기 모니터링, 근육통 발생 시 즉시 의사에게 보고."
        ),
    },
    {
        "id": "ibuprofen",
        "name": "이부프로펜 (Ibuprofen)",
        "category": "비스테로이드성 항염증제 (NSAID)",
        "info": (
            "이부프로펜은 COX-1/COX-2를 가역적으로 억제하는 NSAID로 소염, 진통, 해열 작용을 합니다. "
            "주요 적응증: 통증(두통, 치통, 생리통, 근육통), 발열, 관절염. "
            "일반 용량: 1회 400~600mg, 1일 3회 식사와 함께 복용(최대 2400mg/일). "
            "흔한 부작용: 위장관 자극, 소화불량, 오심, 복통, 두통, 어지러움. "
            "심각한 부작용: 위궤양/출혈, 신기능 저하, 심혈관 위험 증가, 간독성. "
            "상호작용: 아스피린과 동시 복용 시 아스피린 항혈소판 효과 차단. "
            "로사르탄/ACE억제제와 병용 시 항고혈압 효과 감소 및 신독성 위험(트리플 위험 조합). "
            "와파린과 병용 시 출혈 위험 증가. "
            "리튬 독성 증가. "
            "주의사항: 공복 복용 피하기, 신기능 저하 환자 주의, 장기 복용 시 위장관 보호제 병용 권장."
        ),
    },
    {
        "id": "acetaminophen",
        "name": "아세트아미노펜 (Acetaminophen / 타이레놀)",
        "category": "해열진통제",
        "info": (
            "아세트아미노펜은 중추신경계에서 통증 신호를 차단하는 해열진통제로 소염 효과는 없습니다. "
            "주요 적응증: 경증~중등도 통증, 발열. "
            "일반 용량: 1회 500~1000mg, 4~6시간 간격(최대 4000mg/일, 간질환자 2000mg/일). "
            "흔한 부작용: 치료 용량에서 부작용 드묾. "
            "심각한 부작용: 과용량 시 간부전(치명적) — N-아세틸시스테인으로 해독. "
            "상호작용: 알코올과 병용 시 간독성 위험 크게 증가. "
            "와파린과 장기 병용 시 INR 상승 가능. "
            "리팜핀 등 간 효소 유도제와 병용 시 독성 대사체 증가. "
            "주의사항: 다른 아세트아미노펜 함유 제품(감기약, 복합 진통제)과 중복 복용 주의, "
            "간질환/만성 음주자 용량 감량, 총 일일 용량 엄수."
        ),
    },
    {
        "id": "clopidogrel",
        "name": "클로피도그렐 (Clopidogrel / 플라빅스)",
        "category": "항혈소판제 / P2Y12 차단제",
        "info": (
            "클로피도그렐은 혈소판 ADP 수용체(P2Y12)를 비가역적으로 차단하여 혈소판 응집을 억제합니다. "
            "주요 적응증: 급성 관상동맥증후군, 관상동맥 스텐트 시술 후, 뇌졸중/TIA 예방. "
            "일반 용량: 부하 용량 300~600mg 후 유지 75mg/일. "
            "흔한 부작용: 출혈(멍, 코피, 잇몸 출혈), 위장관 불편감, 두통. "
            "심각한 부작용: 심각한 출혈(위장관, 두개내), 혈전성 혈소판감소성 자반(TTP, 드물게). "
            "상호작용: 오메프라졸/에소메프라졸과 병용 시 클로피도그렐 활성 대사체 감소(CYP2C19 억제) — "
            "판토프라졸 등 다른 PPI 권장. "
            "아스피린과 이중 항혈소판 요법 — 출혈 위험 증가하나 스텐트 혈전증 예방에 필수. "
            "주의사항: 수술/시술 전 5~7일 중단, CYP2C19 다형성에 따른 효과 차이."
        ),
    },
    {
        "id": "warfarin",
        "name": "와파린 (Warfarin / 쿠마딘)",
        "category": "경구 항응고제 / 비타민 K 길항제",
        "info": (
            "와파린은 비타민 K 의존성 응고인자(II, VII, IX, X) 합성을 억제하는 경구 항응고제입니다. "
            "주요 적응증: 심방세동, 정맥혈전증(DVT/PE), 인공심장판막. "
            "일반 용량: INR 목표치(보통 2.0~3.0)에 따라 개별화, 평균 2~10mg/일. "
            "흔한 부작용: 출혈(멍, 코피, 혈뇨, 혈변), 탈모. "
            "심각한 부작용: 두개내 출혈, 위장관 대출혈, 피부 괴사(드물게). "
            "상호작용(매우 많음): 아스피린/NSAIDs — 출혈 위험 크게 증가. "
            "클로피도그렐 병용 — 출혈 위험 더욱 증가. "
            "심바스타틴 — 와파린 효과 증가(INR 상승). "
            "항생제(메트로니다졸, 플루코나졸 등) — INR 크게 상승. "
            "비타민 K 함유 식품(시금치, 케일, 브로콜리) 과다 섭취 시 와파린 효과 감소. "
            "주의사항: 정기적 INR 모니터링(최소 4주마다), 식이 비타민 K 일정하게 유지, "
            "새로운 약물 추가/중단 시 반드시 INR 재확인."
        ),
    },
]


async def seed_drug_info() -> None:
    client = get_client()
    try:
        count_result = await client.count(collection_name=_COLLECTION)
        if count_result.count > 0:
            logger.info("Drug info already seeded (%d docs). Skipping.", count_result.count)
            return
    except Exception as e:
        logger.warning("Failed to check drug info count: %s", e)
        return

    points = []
    for drug in DRUG_DATA:
        text = f"{drug['name']}\n{drug['category']}\n{drug['info']}"
        vector = await embed(text)
        if vector is None:
            continue
        point_id = int(hashlib.md5(drug["id"].encode()).hexdigest()[:8], 16)
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload={"id": drug["id"], "name": drug["name"], "category": drug["category"], "info": drug["info"]},
            )
        )

    if points:
        try:
            await client.upsert(collection_name=_COLLECTION, points=points)
            logger.info("Seeded %d drug info documents.", len(points))
        except Exception as e:
            logger.warning("Failed to upsert drug info: %s", e)


async def search_drug_info(medication_names: list[str], limit: int = 2) -> str:
    client = get_client()
    results = []
    for name in medication_names[:5]:
        vector = await embed(name)
        if vector is None:
            continue
        try:
            hits = await client.search(
                collection_name=_COLLECTION,
                query_vector=vector,
                limit=limit,
                score_threshold=0.4,
            )
            for hit in hits:
                payload = hit.payload or {}
                results.append(
                    f"[{payload.get('name', '')}] ({payload.get('category', '')})\n{payload.get('info', '')}"
                )
        except Exception as e:
            logger.warning("Drug info search failed for '%s': %s", name, e)

    return "\n\n".join(results)
