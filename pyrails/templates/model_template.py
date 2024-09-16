model_template = """from pyrails.models import *


class {model_name}(BaseModel):
{fields}
    meta = {{
        "collection": "{table_name}"
    }}
"""
