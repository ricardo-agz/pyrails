from mongoengine import Document
from .base_logic import BaseModelLogic
from datetime import datetime


class BaseModel(BaseModelLogic, Document):
    """
    Abstract base class for MongoEngine Documents, inheriting from both
    Document and BaseModelMixin.
    """

    meta = {
        "abstract": True,
        "db_alias": "default",
    }

    def save(self, *args, **kwargs) -> "BaseModel":
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
