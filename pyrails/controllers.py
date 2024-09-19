from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException
from functools import wraps
import inspect
from pyrails.logger import logger


def websocket(path: str):
    def decorator(func):
        func._websocket_route_info = {"path": path}
        return func

    return decorator


def route(path: str, methods: list[str]):
    def decorator(func):
        func._route_info = {"path": path, "methods": methods}
        return func

    return decorator


def get(path: str):
    return route(path, ["GET"])


def post(path: str):
    return route(path, ["POST"])


def put(path: str):
    return route(path, ["PUT"])


def delete(path: str):
    return route(path, ["DELETE"])


class WebSocketManager:
    def __init__(self):
        # Maps path to list of active WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)
        # Maps room name to set of WebSocket connections
        self.active_rooms: dict[str, set[WebSocket]] = defaultdict(set)
        # Maps WebSocket connections to the rooms they have joined
        self.connection_rooms: dict[WebSocket, set[str]] = defaultdict(set)

    async def connect(self, path: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[path].append(websocket)
        logger.info(f"WebSocket connected: {websocket.client} at path: {path}")

    def disconnect(self, path: str, websocket: WebSocket):
        if websocket in self.active_connections[path]:
            self.active_connections[path].remove(websocket)
            logger.info(f"WebSocket disconnected: {websocket.client} from path: {path}")
            # Remove from any rooms
            rooms = self.connection_rooms.pop(websocket, set())
            for room in rooms:
                self.active_rooms[room].discard(websocket)
                logger.info(f"WebSocket {websocket.client} left room: {room}")
            if not self.active_connections[path]:
                del self.active_connections[path]

    async def broadcast(self, path: str, message: str):
        connections = self.active_connections.get(path, [])
        logger.info(
            f"Broadcasting message to {len(connections)} connections at path: {path}"
        )
        for connection in connections:
            try:
                await connection.send_text(message)
            except WebSocketException as e:
                logger.error(f"Error sending message to {connection.client}: {e}")
                self.disconnect(path, connection)

    async def send_to_room(self, room: str, message: str):
        connections = self.active_rooms.get(room, set())
        logger.info(
            f"Sending message to room '{room}' with {len(connections)} connections"
        )
        for connection in connections:
            try:
                await connection.send_text(message)
            except WebSocketException as e:
                logger.error(f"Error sending message to {connection.client}: {e}")
                # Assuming path is known; alternatively, track path per connection
                # Here, we skip disconnecting for simplicity
                continue

    def join_room(self, websocket: WebSocket, room: str):
        self.active_rooms[room].add(websocket)
        self.connection_rooms[websocket].add(room)
        logger.info(f"WebSocket {websocket.client} joined room: {room}")

    def leave_room(self, websocket: WebSocket, room: str):
        self.active_rooms[room].discard(websocket)
        self.connection_rooms[websocket].discard(room)
        logger.info(f"WebSocket {websocket.client} left room: {room}")
        if not self.active_rooms[room]:
            del self.active_rooms[room]


class ControllerMeta(type):
    def __new__(cls, name, bases, attrs):
        router = APIRouter()
        new_cls = super().__new__(cls, name, bases, attrs)
        new_cls.router = router
        new_cls.websocket_manager = WebSocketManager()
        instance = new_cls()

        def create_websocket_endpoint(bound_method, path):
            @router.websocket(path)
            async def websocket_endpoint(websocket: WebSocket):
                logger.info(f"Establishing WebSocket connection at path: {path}")
                try:
                    await new_cls.websocket_manager.connect(path, websocket)
                    # Call on_connect lifecycle method
                    await instance.on_websocket_connect(websocket)
                    # Call the user-defined WebSocket handler
                    await bound_method(websocket)
                except WebSocketDisconnect:
                    logger.info(f"WebSocket {websocket.client} disconnected")
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                finally:
                    # Call on_disconnect lifecycle method
                    await instance.on_websocket_disconnect(websocket)
                    new_cls.websocket_manager.disconnect(path, websocket)

        def create_http_endpoint(bound_method):
            sig = inspect.signature(bound_method)
            params = list(sig.parameters.values())
            if params and params[0].name == "self":
                params = params[1:]
            new_sig = sig.replace(parameters=params)

            @wraps(bound_method)
            async def endpoint(*args, **kwargs):
                if inspect.iscoroutinefunction(bound_method):
                    return await bound_method(*args, **kwargs)
                else:
                    return bound_method(*args, **kwargs)

            endpoint.__signature__ = new_sig
            return endpoint

        # Register both HTTP and WebSocket routes
        for attr_name, method in attrs.items():
            # HTTP Routes
            if hasattr(method, "_route_info"):
                route_info = method._route_info
                path = route_info["path"]
                methods = route_info["methods"]

                bound_method = method.__get__(instance, new_cls)
                endpoint = create_http_endpoint(bound_method)

                for http_method in methods:
                    getattr(router, http_method.lower())(path)(endpoint)

            # WebSocket Routes
            elif hasattr(method, "_websocket_route_info"):
                route_info = method._websocket_route_info
                path = route_info["path"]

                bound_method = method.__get__(instance, new_cls)

                # Use factory function to avoid late binding
                create_websocket_endpoint(bound_method, path)

        return new_cls


class Controller(metaclass=ControllerMeta):
    async def on_websocket_connect(self, websocket: WebSocket):
        """Override this method to handle actions when a WebSocket connects."""
        pass

    async def on_websocket_disconnect(self, websocket: WebSocket):
        """Override this method to handle actions when a WebSocket disconnects."""
        pass
