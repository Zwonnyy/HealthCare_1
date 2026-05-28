from app.models.guides import Guide


class GuideRepository:
    def __init__(self):
        self._model = Guide

    async def create_guide(self, record_id: int) -> Guide:
        return await self._model.create(record_id=record_id)

    async def get_guide(self, guide_id: int) -> Guide | None:
        return await self._model.get_or_none(id=guide_id)

    async def get_record_guides(self, record_id: int) -> list[Guide]:
        return await self._model.filter(record_id=record_id).order_by("-created_at")