from sqlalchemy.orm import Session, joinedload
from app.models.system import FAQArticle
from typing import List, Optional
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