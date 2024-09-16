from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException
from functools import wraps
import inspect
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def websocket_route(path: str):
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
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, path: str, websocket: WebSocket):
        await websocket.accept()
        if path not in self.active_connections:
            self.active_connections[path] = []
        self.active_connections[path].append(websocket)
        logger.info(f"WebSocket connected: {websocket.client}")

    def disconnect(self, path: str, websocket: WebSocket):
        self.active_connections[path].remove(websocket)
        if not self.active_connections[path]:
            del self.active_connections[path]
        logger.info(f"WebSocket disconnected: {websocket.client}")

    async def broadcast(self, path: str, message: str):
        if path in self.active_connections:
            for connection in self.active_connections[path]:
                try:
                    await connection.send_text(message)
                except WebSocketException as e:
                    logger.error(f"Error sending message: {e}")
                    self.disconnect(path, connection)


class ControllerMeta(type):
    def __new__(cls, name, bases, attrs):
        router = APIRouter()
        new_cls = super().__new__(cls, name, bases, attrs)
        new_cls.router = router
        new_cls.websocket_manager = WebSocketManager()
        instance = new_cls()

        def create_endpoint(bound_method):
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
                endpoint = create_endpoint(bound_method)

                for http_method in methods:
                    getattr(router, http_method.lower())(path)(endpoint)

            # WebSocket Routes
            elif hasattr(method, "_websocket_route_info"):
                route_info = method._websocket_route_info
                path = route_info["path"]

                bound_method = method.__get__(instance, new_cls)

                # Properly register the WebSocket endpoint
                @router.websocket(path)
                async def websocket_endpoint(websocket: WebSocket, *args, **kwargs):
                    logger.info(
                        f"Attempting to establish WebSocket connection at path: {path}"
                    )

                    # Handle connection and disconnection
                    try:
                        await new_cls.websocket_manager.connect(path, websocket)
                        await bound_method(websocket, *args, **kwargs)
                    except WebSocketDisconnect:
                        new_cls.websocket_manager.disconnect(path, websocket)
                    except Exception as e:
                        logger.error(f"WebSocket error: {e}")
                        new_cls.websocket_manager.disconnect(path, websocket)

                # Add the WebSocket route explicitly to the router
                router.add_api_websocket_route(path, websocket_endpoint)

        return new_cls


class Controller(metaclass=ControllerMeta):
    async def on_connect(self, websocket: WebSocket):
        """Override this method to handle actions when a WebSocket connects."""
        pass

    async def on_disconnect(self, websocket: WebSocket):
        """Override this method to handle actions when a WebSocket disconnects."""
        pass
