scaffold_controller_template = """from pyrails.controllers import Controller, get, post, put, delete
from app.models.{resource_name_lower} import {resource_name}
from pyrails.exceptions import NotFoundError
from fastapi import Request
from pydantic import BaseModel


class {resource_name}Create(BaseModel):
{pydantic_fields}

class {resource_name}Update(BaseModel):
{pydantic_fields}

class {resource_name_plural}Controller(Controller):
    @get('/{resource_name_plural_lower}')
    async def index(self, request: Request):
        items = {resource_name}.find()
        return [item.to_dict() for item in items]

    @get('/{resource_name_plural_lower}/{{id}}')
    async def show(self, request: Request, id: str):
        item = {resource_name}.find_by_id(id=id)
        if item:
            return item.to_dict()
        raise NotFoundError('{resource_name} not found')

    @post('/{resource_name_plural_lower}')
    async def create(self, request: Request, data: {resource_name}Create):
        item = {resource_name}(**data.dict()).save()
        return item.to_dict()

    @put('/{resource_name_plural_lower}/{{id}}')
    async def update(self, request: Request, id: str, data: {resource_name}Update):
        item = {resource_name}.find_by_id_and_update(id=id, **data.dict(exclude_unset=True))
        if item:
            return item.to_dict()
        raise NotFoundError('{resource_name} not found')

    @delete('/{resource_name_plural_lower}/{{id}}')
    async def delete(self, request: Request, id: str):
        item = {resource_name}.find_by_id_and_delete(id=id)
        if item is None:
            raise NotFoundError('{resource_name} not found')
        return {{'detail': '{resource_name} deleted'}}
"""
