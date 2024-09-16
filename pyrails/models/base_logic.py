from typing import Optional, TypeVar, Type, Union, List

from bson import SON
from mongoengine import (
    Document,
    DateTimeField,
    DoesNotExist,
    MultipleObjectsReturned,
    EmbeddedDocument,
    DynamicDocument,
)
from datetime import datetime
from bson.objectid import ObjectId
from abc import ABC, abstractmethod

T = TypeVar("T", bound=Union[Document, DynamicDocument])


class BaseModelLogic:
    meta = {"abstract": True}

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        def _handle_value(val):
            if isinstance(val, ObjectId):
                return str(val)
            elif isinstance(val, (dict, Document, EmbeddedDocument)):
                return _dictify(val)
            elif isinstance(val, list):
                return [_handle_value(v) for v in val]
            else:
                return val

        def _dictify(d):
            return {k: _handle_value(v) for k, v in d.items()}

        return _dictify(self.to_mongo().to_dict())

    @classmethod
    def _execute_query(cls, operation, *args, **kwargs) -> Optional[T]:
        try:
            return operation(*args, **kwargs)
        except (DoesNotExist, MultipleObjectsReturned):
            return None

    @classmethod
    def find_by_id(cls, id: str | ObjectId) -> Optional[T]:
        cls._check_objects_attribute()

        if isinstance(id, ObjectId) or ObjectId.is_valid(id):
            return cls._execute_query(cls.objects(id=id).first)  # type: ignore
        else:
            return None

    @classmethod
    def find_one(cls, **kwargs) -> Optional[T]:
        cls._check_objects_attribute()

        return cls._execute_query(cls.objects(**kwargs).first)  # type: ignore

    @classmethod
    def find(cls, page: int = None, per_page: int = None, **kwargs) -> List[T]:
        cls._check_objects_attribute()

        if page is not None and per_page is not None:
            start = (page - 1) * per_page
            end = start + per_page
            return cls._execute_query(cls.objects(**kwargs).skip(start).limit(per_page))  # type: ignore
        else:
            return cls._execute_query(cls.objects(**kwargs))  # type: ignore

    @classmethod
    def find_by_id_and_update(cls, id: str, **kwargs) -> Optional[T]:
        cls._check_objects_attribute()

        if isinstance(id, ObjectId) or ObjectId.is_valid(id):
            cls._execute_query(cls.objects(id=id).update, **kwargs)  # type: ignore
            return cls.find_by_id(str(id))
        else:
            return None

    @classmethod
    def find_by_id_and_delete(cls, id: str) -> Optional[T]:
        cls._check_objects_attribute()

        if isinstance(id, ObjectId) or ObjectId.is_valid(id):
            doc = cls._execute_query(cls.objects(id=id).first)  # type: ignore
            if doc:
                doc.delete()
            return doc
        else:
            return None

    @classmethod
    def count(cls, **kwargs) -> int:
        cls._check_objects_attribute()

        return cls.objects(**kwargs).count()  # type: ignore

    @classmethod
    def _check_objects_attribute(cls):
        if not hasattr(cls, "objects"):
            raise AttributeError(f"{cls.__name__} must have an 'objects' attribute.")
