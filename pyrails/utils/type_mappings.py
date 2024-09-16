mongoengine_type_mapping = {
    "str": "StringField()",
    "text": "StringField()",
    "int": "IntField()",
    "bool": "BooleanField()",
    "float": "FloatField()",
    "datetime": "DateTimeField()",
    "date": "DateTimeField()",
    "time": "DateTimeField()",
    "uuid": "UUIDField()",
    "json": "DictField()",
    "decimal": "DecimalField()",
    "list": "ListField()",
    "list[str]": "ListField(StringField())",
    "list[int]": "ListField(IntField())",
    "list[bool]": "ListField(BooleanField())",
    "list[float]": "ListField(FloatField())",
    "list[datetime]": "ListField(DateTimeField())",
}

tortoise_type_mapping = {
    "str": "CharField(max_length=255)",
    "text": "TextField()",
    "int": "IntField()",
    "bool": "BooleanField()",
    "float": "FloatField()",
    "datetime": "DatetimeField()",
    "date": "DateField()",
    "time": "TimeField()",
    "uuid": "UUIDField()",
    "json": "JSONField()",
    "decimal": "DecimalField(max_digits=18, decimal_places=2)",
}

pydantic_type_mapping = {
    "str": "str",
    "text": "str",
    "int": "int",
    "bool": "bool",
    "float": "float",
    "datetime": "datetime",
    "date": "datetime",
    "time": "datetime",
    "uuid": "str",
    "json": "dict",
    "decimal": "float",
    "list": "list",
    "list[str]": "list[str]",
    "list[int]": "list[int]",
    "list[bool]": "list[bool]",
    "list[float]": "list[float]",
    "list[datetime]": "list[datetime]",
}
