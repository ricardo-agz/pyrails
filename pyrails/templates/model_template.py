model_template = """from pyrails.models import *


class {resource_name_pascal}(BaseModel):
{fields}
    meta = {{
        "collection": "{resource_name_snake}"
    }}
"""
