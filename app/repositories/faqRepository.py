from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.system import FAQArticle
from typing import List, Optional, Tuple
import uuid

class FAQRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_articles(self) -> List[FAQArticle]:
        return self.db.query(FAQArticle)\
            .options(joinedload(FAQArticle.author), joinedload(FAQArticle.category))\
            .order_by(FAQArticle.updated_at.desc())\
            .all()

    def get_public_articles(self) -> List[FAQArticle]:
        return self.db.query(FAQArticle)\
            .options(joinedload(FAQArticle.author), joinedload(FAQArticle.category))\
            .filter(FAQArticle.is_published == True)\
            .order_by(FAQArticle.updated_at.desc())\
            .all()

    def get_private_articles(self) -> List[FAQArticle]:
        return self.db.query(FAQArticle)\
            .options(joinedload(FAQArticle.author), joinedload(FAQArticle.category))\
            .filter(FAQArticle.is_published == False)\
            .order_by(FAQArticle.updated_at.desc())\
            .all()

    def get_by_id(self, article_id: uuid.UUID) -> Optional[FAQArticle]:
        return self.db.query(FAQArticle)\
            .options(joinedload(FAQArticle.author), joinedload(FAQArticle.category))\
            .filter(FAQArticle.id_article == article_id)\
            .first()

    def get_public_article_by_id(self, article_id: uuid.UUID) -> Optional[FAQArticle]:
        """Get a single public (published) FAQ article by ID. Returns None if not found or not published."""
        return self.db.query(FAQArticle)\
            .options(joinedload(FAQArticle.author), joinedload(FAQArticle.category))\
            .filter(FAQArticle.id_article == article_id)\
            .filter(FAQArticle.is_published == True)\
            .first()

    def get_public_articles_paginated(
        self,
        page: int = 1,
        limit: int = 20,
        category_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None
    ) -> Tuple[List[FAQArticle], int]:
        """
        Get paginated list of public (published) FAQ articles.
        Returns tuple of (articles, total_count).
        """
        query = self.db.query(FAQArticle)\
            .options(joinedload(FAQArticle.author), joinedload(FAQArticle.category))\
            .filter(FAQArticle.is_published == True)

        # Apply category filter
        if category_id:
            query = query.filter(FAQArticle.id_category == category_id)

        # Apply search filter (search in title and content)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    FAQArticle.title.ilike(search_pattern),
                    FAQArticle.content.ilike(search_pattern)
                )
            )

        # Get total count before pagination
        total = query.count()

        # Apply pagination and ordering
        offset = (page - 1) * limit
        articles = query\
            .order_by(FAQArticle.updated_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()

        return articles, total

    def create(self, article: FAQArticle) -> FAQArticle:
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article

    def update(self, article: FAQArticle) -> FAQArticle:
        self.db.commit()
        self.db.refresh(article)
        return article

    def increment_view(self, article: FAQArticle):
        article.view_count += 1
        self.db.commit()
        self.db.refresh(article)

    def delete(self, article: FAQArticle):
        self.db.delete(article)
        self.db.commit()