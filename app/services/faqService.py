from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.faqRepository import FAQRepository
from app.repositories.ticketCategoryRepository import TicketCategoryRepository
from app.models.system import FAQArticle
from app.schemas.faqSchema import FAQCreate, FAQUpdate
from typing import List, Optional, Tuple
import uuid
import time

VIEW_CACHE = {}
SPAM_COOLDOWN_SECONDS = 300

class FAQService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FAQRepository(db)
        self.category_repo = TicketCategoryRepository(db)

    def create_article(self, data: FAQCreate, author_id: uuid.UUID) -> FAQArticle:
        category = self.category_repo.get_by_id(str(data.id_category))
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")

        article = FAQArticle(
            title=data.title,
            content=data.content,
            is_published=data.is_published,
            id_category=data.id_category,
            id_author=author_id
        )
        return self.repo.create(article)

    def get_all_articles(self) -> List[FAQArticle]:
        return self.repo.get_all_articles()

    def get_public_articles(self) -> List[FAQArticle]:
        return self.repo.get_public_articles()

    def get_private_articles(self) -> List[FAQArticle]:
        return self.repo.get_private_articles()

    def get_public_articles_paginated(
        self,
        page: int = 1,
        limit: int = 20,
        category_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None
    ) -> Tuple[List[FAQArticle], int]:
        """Get paginated list of public FAQ articles with total count."""
        return self.repo.get_public_articles_paginated(page, limit, category_id, search)

    def get_public_article_detail(self, article_id: uuid.UUID, client_ip: str) -> FAQArticle:
        """Get a single public (published) FAQ article by ID. Raises 404 if not found or not published."""
        article = self.repo.get_public_article_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài viết!")

        current_time = time.time()
        cache_key = f"{client_ip}_{article_id}"

        if cache_key not in VIEW_CACHE or (current_time - VIEW_CACHE[cache_key]) > SPAM_COOLDOWN_SECONDS:
            self.repo.increment_view(article)
            VIEW_CACHE[cache_key] = current_time
            self._cleanup_cache(current_time)

        return article

    def read_article_detail(self, article_id: uuid.UUID, client_ip: str) -> FAQArticle:
        # Security fix: Only return published articles (use get_public_article_by_id)
        article = self.repo.get_public_article_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài viết!")

        current_time = time.time()
        cache_key = f"{client_ip}_{article_id}"

        if cache_key not in VIEW_CACHE or (current_time - VIEW_CACHE[cache_key]) > SPAM_COOLDOWN_SECONDS:
            self.repo.increment_view(article)
            VIEW_CACHE[cache_key] = current_time
            self._cleanup_cache(current_time)

        return article

    def update_article(self, article_id: uuid.UUID, data: FAQUpdate) -> FAQArticle:
        article = self.repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài viết!")

        update_data = data.model_dump(exclude_unset=True)

        if "id_category" in update_data and update_data["id_category"] != article.id_category:
            category = self.category_repo.get_by_id(str(update_data["id_category"]))
            if not category:
                raise HTTPException(status_code=404, detail="Không tìm thấy danh mục!")

        for key, value in update_data.items():
            setattr(article, key, value)

        return self.repo.update(article)

    def delete_article(self, article_id: uuid.UUID):
        article = self.repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài viết!")
        self.repo.delete(article)

    def _cleanup_cache(self, current_time: float):
        keys_to_delete = [k for k, v in VIEW_CACHE.items() if (current_time - v) > SPAM_COOLDOWN_SECONDS]
        for k in keys_to_delete:
            del VIEW_CACHE[k]