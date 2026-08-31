from abc import ABC, abstractmethod
from typing import Generic, List, Type, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import Base
from database.models import Ad, Group, User

ModelType = TypeVar("ModelType", bound=Base)


class AbstractRepository(ABC, Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    @abstractmethod
    async def add(self, instance: ModelType) -> ModelType: ...

    @abstractmethod
    async def get_by_id(self, item_id: int) -> ModelType | None: ...

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> ModelType | None: ...

    @abstractmethod
    async def get_random(self) -> ModelType | None: ...

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]: ...

    @abstractmethod
    async def update(self, item_id: int, data: dict) -> ModelType | None: ...

    @abstractmethod
    async def delete(self, item_id: int) -> None: ...

    @abstractmethod
    async def delete_by_telegram_id(self, telegram_id: int) -> None: ...


class SQLAlchemyRepository(AbstractRepository[ModelType]):
    async def add(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, item_id: int) -> ModelType | None:
        result = await self.session.execute(select(self.model).where(self.model.id == item_id))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(self.model.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_random(self) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).order_by(func.random()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        result = await self.session.execute(select(self.model).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def update(self, item_id: int, data: dict) -> ModelType | None:
        result = await self.session.execute(
            update(self.model)
            .where(self.model.id == item_id)
            .values(**data)
            .returning(self.model)
        )
        return result.scalar_one_or_none()

    async def delete(self, item_id: int) -> None:
        await self.session.execute(delete(self.model).where(self.model.id == item_id))

    async def delete_by_telegram_id(self, telegram_id: int) -> None:
        await self.session.execute(
            delete(self.model).where(self.model.telegram_id == telegram_id)
        )


class UserRepository(SQLAlchemyRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)


class GroupRepository(SQLAlchemyRepository[Group]):
    def __init__(self, session: AsyncSession):
        super().__init__(Group, session)


class AdRepository(SQLAlchemyRepository[Ad]):
    def __init__(self, session: AsyncSession):
        super().__init__(Ad, session)

    async def get_by_telegram_id(self, telegram_id: int) -> Ad | None:
        return None

    async def delete_by_telegram_id(self, telegram_id: int) -> None:
        return None
