# ---------------------------------------------------------------------------
# Compatibility shim
# ---------------------------------------------------------------------------
# PyMongo 4.9+ removed the private helper `pymongo.database._check_name` that
# older versions of MongoEngine (< 0.30) still import. To avoid a hard runtime
# failure we recreate a minimal implementation *before* any third-party code
# has a chance to import MongoEngine.
#
# This file is usually the first thing user code imports (`import metro`), so
# placing the shim here guarantees it runs early.
from importlib import import_module

try:
    _pymongo_database = import_module("pymongo.database")  # type: ignore
    if not hasattr(_pymongo_database, "_check_name"):
        from pymongo.errors import InvalidName as _InvalidName

        def _check_name(name):  # type: ignore
            if not isinstance(name, str) or not name:
                raise _InvalidName("database name must be a non-empty string")

        _pymongo_database._check_name = _check_name  # type: ignore
except ModuleNotFoundError:
    # PyMongo not installed yet. The user might install it later (e.g. in a
    # deferred import). In that unlikely scenario they will need to call this
    # shim manually via `import metro.compat` after installing PyMongo.
    pass

from metro.app import Metro
from metro.requests import Request
from metro.controllers import (
    Controller,
    get,
    post,
    put,
    delete,
    before_request,
    after_request,
    on_connect,
    on_disconnect,
)
from metro.exceptions import (
    HTTPException,
    NotFoundError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    TooManyRequestsError,
)
from metro.params import (
    Body,
    Path,
    Query,
    Depends,
    Header,
    Cookie,
    Form,
    File,
    Security,
)

from fastapi import APIRouter


__all__ = [
    "Metro",
    "Request",
    "Controller",
    "get",
    "post",
    "put",
    "delete",
    "before_request",
    "after_request",
    "on_connect",
    "on_disconnect",
    "APIRouter",
    "HTTPException",
    "NotFoundError",
    "BadRequestError",
    "UnauthorizedError",
    "ForbiddenError",
    "TooManyRequestsError",
    "Body",
    "Path",
    "Query",
    "Depends",
    "Header",
    "Cookie",
    "Form",
    "File",
    "Security",
]
