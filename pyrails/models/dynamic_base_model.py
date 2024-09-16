from mongoengine import DynamicDocument
from .base_logic import BaseModelLogic
from datetime import datetime


class DynamicBaseModel(BaseModelLogic, DynamicDocument):
    """
    Abstract base class for dynamic MongoEngine Documents,
    inheriting from both DynamicDocument and BaseModelLogic.
    """

    meta = {
        "abstract": True,
        "db_alias": "default",
    }

    def save(self, *args, **kwargs) -> "DynamicBaseModel":
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
