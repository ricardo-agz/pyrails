import os

import click

from ..templates import (
    controller_template,
    model_template,
    scaffold_controller_template,
)
from ..utils import (
    pluralize,
    to_snake_case,
    to_pascal_case,
    mongoengine_type_mapping,
    pydantic_type_mapping,
)
from ..utils.file_operations import insert_line_without_duplicating


@click.group()
def generate():
    """Generate code."""
    pass


@generate.command()
@click.argument("model_name")
@click.argument("fields", nargs=-1)
def model(model_name, fields):
    """Generate a new model."""
    snake_case_name = to_snake_case(model_name)
    pascal_case_name = to_pascal_case(model_name)

    fields_code = ""
    pydantic_code = ""
    for field in fields:
        # Split into name and type_ based on the first colon only
        name, type_ = field.split(":", 1)

        # Determine if the field should be unique or optional
        unique = name.endswith("^")
        optional = name.endswith("_")

        # Remove the markers from the name
        name = name.rstrip("^_")

        # Check for special naming conventions
        if name.endswith("_hashed"):
            fields_code += f"    {name} = HashedField(required={not optional})\n"
            pydantic_code += f"    {name}: str  # Hashed field\n"
        elif name.endswith("_encrypted"):
            fields_code += f"    {name} = EncryptedField(required={not optional})\n"
            pydantic_code += f"    {name}: str  # Encrypted field\n"
        elif type_.startswith("ref:"):
            # One-to-many relationship
            ref_model = type_[4:]  # Extract the model name after ref:
            fields_code += (
                f"    {name} = ReferenceField('{ref_model}', required={not optional})\n"
            )
            # For Pydantic, use ObjectId as string
            pydantic_code += f"    {name}: str  # ObjectId reference to {ref_model}\n"
        elif type_.startswith("list:"):
            # List of types or references
            inner_type = type_[5:]
            if inner_type.startswith("ref:"):
                # Many-to-many relationship
                ref_model = inner_type[4:]  # Extract the model name within ref:
                fields_code += f"    {name} = ListField(ReferenceField('{ref_model}'), required={not optional})\n"
                # For Pydantic, use a list of ObjectIds as strings
                pydantic_code += f"    {name}: list[str]  # List of ObjectId references to {ref_model}\n"
            else:
                # List of standard types
                mongo_field = mongoengine_type_mapping.get(
                    f"list[{inner_type}]", "ListField()"
                )
                pydantic_type = f'list[{pydantic_type_mapping.get(inner_type, "str")}]'
                fields_code += f"    {name} = {mongo_field}\n"
                pydantic_code += f"    {name}: {pydantic_type}\n"
        elif type_.startswith("dict:"):
            # Dict with specific key-value types (e.g., dict:str,int)
            key_value_types = type_[5:].split(",")
            key_type = pydantic_type_mapping.get(key_value_types[0].strip(), "str")
            value_type = pydantic_type_mapping.get(key_value_types[1].strip(), "Any")
            fields_code += f"    {name} = DictField(required={not optional})\n"
            pydantic_code += f"    {name}: dict[{key_type}, {value_type}]\n"
        else:
            # Standard field types
            mongo_field = mongoengine_type_mapping.get(type_.lower(), "StringField()")
            # Add required and unique attributes
            if not optional:
                mongo_field = mongo_field.replace("()", "(required=True)")
            if unique:
                mongo_field = mongo_field.replace(")", ", unique=True)")
            pydantic_type = pydantic_type_mapping.get(type_.lower(), "str")
            fields_code += f"    {name} = {mongo_field}\n"
            pydantic_code += f"    {name}: {pydantic_type}\n"

    content = model_template.format(
        model_name=pascal_case_name,
        fields=fields_code,
        table_name=snake_case_name,
    )
    model_path = f"app/models/{snake_case_name}.py"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, "w") as f:
        f.write(content)

    # Update models __init__.py
    init_path = "app/models/__init__.py"
    line_to_insert = f"from .{snake_case_name} import {pascal_case_name}"
    insert_line_without_duplicating(init_path, line_to_insert)

    click.echo(
        f"Model '{pascal_case_name}' generated at '{model_path}' and added to {init_path}."
    )


@generate.command()
@click.argument("controller_name")
@click.argument("methods", nargs=-1)  # Accept multiple methods
def controller(controller_name, methods):
    """Generate a new controller."""
    snake_case_name = to_snake_case(controller_name)
    pascal_case_name = to_pascal_case(controller_name)
    kebab_case_name = snake_case_name.replace("_", "-")

    methods_code = "    pass\n" if not methods else ""

    # Loop through provided methods and generate code for each
    for method in methods:
        http_method, action = method.split(":")
        action_snake = to_snake_case(action)
        action_kebab = action_snake.replace("_", "-")

        if http_method.lower() == "get":
            methods_code += f"    @get('/{kebab_case_name}/{action_kebab}')\n    async def {action_snake}(self, request):\n        pass\n\n"
        elif http_method.lower() == "post":
            methods_code += f"    @post('/{kebab_case_name}/{action_kebab}')\n    async def {action_snake}(self, request):\n        pass\n\n"
        elif http_method.lower() == "put":
            methods_code += f"    @put('/{kebab_case_name}/{action_kebab}')\n    async def {action_snake}(self, request):\n        pass\n\n"
        elif http_method.lower() == "delete":
            methods_code += f"    @delete('/{kebab_case_name}/{action_kebab}')\n    async def {action_snake}(self, request):\n        pass\n\n"
        else:
            click.echo(
                f"Invalid HTTP method '{http_method}' provided for action '{action}'."
            )

    content = controller_template.format(
        pascal_case_name=pascal_case_name,
        methods_code=methods_code,
    ).rstrip()
    content += "\n"

    controller_path = f"app/controllers/{snake_case_name}_controller.py"
    os.makedirs(os.path.dirname(controller_path), exist_ok=True)
    with open(controller_path, "w") as f:
        f.write(content)

    # Update controllers __init__.py
    init_path = "app/controllers/__init__.py"
    line_to_insert = f"from .{snake_case_name}_controller import {pascal_case_name}Controller"
    insert_line_without_duplicating(init_path, line_to_insert)

    click.echo(f"Controller '{pascal_case_name}' generated at '{controller_path}'.")


@generate.command()
@click.argument("name")
@click.argument("fields", nargs=-1)
def scaffold(name, fields):
    """Generate a model and controller with CRUD functionality."""
    snake_case_name = to_snake_case(name)
    pascal_case_name = to_pascal_case(name)
    plural_snake_case = to_snake_case(pluralize(name))
    plural_pascal_case = to_pascal_case(pluralize(name))
    plural_kebab_case = plural_snake_case.replace("_", "-")

    # Generate model
    fields_code = ""
    pydantic_code = ""
    for field in fields:
        # Split into name and type_ based on the first colon only
        name, type_ = field.split(":", 1)

        # Determine if the field should be unique or optional
        unique = name.endswith("^")
        optional = name.endswith("_")

        # Remove the markers from the name
        name = name.rstrip("^_")

        # Check for special naming conventions
        if name.endswith("_hashed"):
            fields_code += f"    {name} = HashedField(required={not optional})\n"
            pydantic_code += f"    {name}: str  # Hashed field\n"
        elif name.endswith("_encrypted"):
            fields_code += f"    {name} = EncryptedField(required={not optional})\n"
            pydantic_code += f"    {name}: str  # Encrypted field\n"
        elif type_.startswith("ref:"):
            # One-to-many relationship
            ref_model = type_[4:]  # Extract the model name after ref:
            fields_code += (
                f"    {name} = ReferenceField('{ref_model}', required={not optional})\n"
            )
            # For Pydantic, use ObjectId as string
            pydantic_code += f"    {name}: str  # ObjectId reference to {ref_model}\n"
        elif type_.startswith("list:"):
            # List of types or references
            inner_type = type_[5:]
            if inner_type.startswith("ref:"):
                # Many-to-many relationship
                ref_model = inner_type[4:]  # Extract the model name within ref:
                fields_code += f"    {name} = ListField(ReferenceField('{ref_model}'), required={not optional})\n"
                # For Pydantic, use a list of ObjectIds as strings
                pydantic_code += f"    {name}: list[str]  # List of ObjectId references to {ref_model}\n"
            else:
                # List of standard types
                mongo_field = mongoengine_type_mapping.get(
                    f"list[{inner_type}]", "ListField()"
                )
                pydantic_type = f'list[{pydantic_type_mapping.get(inner_type, "str")}]'
                fields_code += f"    {name} = {mongo_field}\n"
                pydantic_code += f"    {name}: {pydantic_type}\n"
        elif type_.startswith("dict:"):
            # Dict with specific key-value types (e.g., dict:str,int)
            key_value_types = type_[5:].split(",")
            key_type = pydantic_type_mapping.get(key_value_types[0].strip(), "str")
            value_type = pydantic_type_mapping.get(key_value_types[1].strip(), "Any")
            fields_code += f"    {name} = DictField(required={not optional})\n"
            pydantic_code += f"    {name}: dict[{key_type}, {value_type}]\n"
        else:
            # Standard field types
            mongo_field = mongoengine_type_mapping.get(type_.lower(), "StringField()")
            # Add required and unique attributes
            field_attrs = []
            if not optional:
                field_attrs.append("required=True")
            if unique:
                field_attrs.append("unique=True")
            if field_attrs:
                mongo_field = mongo_field.replace("()", f"({', '.join(field_attrs)})")
            pydantic_type = pydantic_type_mapping.get(type_.lower(), "str")
            fields_code += f"    {name} = {mongo_field}\n"
            pydantic_code += f"    {name}: {pydantic_type}\n"

    model_content = model_template.format(
        resource_name_pascal=pascal_case_name,
        resource_name_snake=snake_case_name,
        resource_name_plural_pascal=plural_pascal_case,
        resource_name_plural_kebab=plural_kebab_case,
        resource_name_plural_snake=plural_snake_case,
        fields=fields_code,
    )
    model_path = f"app/models/{snake_case_name}.py"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, "w") as f:
        f.write(model_content)

    # Generate controller
    controller_content = scaffold_controller_template.format(
        resource_name_pascal=pascal_case_name,
        resource_name_snake=snake_case_name,
        resource_name_plural_pascal=plural_pascal_case,
        resource_name_plural_kebab=plural_kebab_case,
        pydantic_fields=pydantic_code,
    )
    controller_path = f"app/controllers/{plural_snake_case}_controller.py"
    os.makedirs(os.path.dirname(controller_path), exist_ok=True)
    with open(controller_path, "w") as f:
        f.write(controller_content)

    # Update controllers __init__.py
    init_path = "app/controllers/__init__.py"
    line_to_insert = f"from .{plural_snake_case}_controller import {plural_pascal_case}Controller"
    insert_line_without_duplicating(init_path, line_to_insert)

    # Update models __init__.py
    init_path = "app/models/__init__.py"
    line_to_insert = f"from .{snake_case_name} import {pascal_case_name}"
    insert_line_without_duplicating(init_path, line_to_insert)

    click.echo(f"Scaffold for '{pascal_case_name}' generated.")
