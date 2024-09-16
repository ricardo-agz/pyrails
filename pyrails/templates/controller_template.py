controller_template = """from pyrails.controllers import Controller, get, post, put, delete


class {resource_name_plural}Controller(Controller):
    @get('/{resource_name_plural_lower}')
    async def index(self, request):
        pass

    @get('/{resource_name_plural_lower}/{{id}}')
    async def show(self, request, id: int):
        pass

    @post('/{resource_name_plural_lower}')
    async def create(self, request):
        pass

    @put('/{resource_name_plural_lower}/{{id}}')
    async def update(self, request, id: int):
        pass

    @delete('/{resource_name_plural_lower}/{{id}}')
    async def delete(self, request, id: int):
        pass
        
"""
