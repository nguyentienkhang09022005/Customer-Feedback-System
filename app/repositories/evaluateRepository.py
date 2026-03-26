from sqlalchemy.orm import Session, joinedload
from app.models.interaction import Evaluate
from typing import List, Optional
import uuid

class EvaluateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, evaluate: Evaluate) -> Evaluate:
        self.db.add(evaluate)
        self.db.commit()
        self.db.refresh(evaluate)
        return evaluate

    def get_by_id(self, evaluate_id: uuid.UUID) -> Optional[Evaluate]:
        return self.db.query(Evaluate).filter(Evaluate.id_evaluate == evaluate_id).first()

    def get_by_ticket(self, ticket_id: uuid.UUID) -> List[Evaluate]:
        return self.db.query(Evaluate)\
            .options(joinedload(Evaluate.customer))\
            .filter(Evaluate.id_ticket == ticket_id)\
            .order_by(Evaluate.created_at.desc())\
            .all()

    def update(self, evaluate: Evaluate) -> Evaluate:
        self.db.commit()
        self.db.refresh(evaluate)
        return evaluate

    def delete(self, evaluate: Evaluate):
        self.db.delete(evaluate)
        self.db.commit()