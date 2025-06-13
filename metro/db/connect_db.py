# Compatibility patch for mongoengine <1.0 with PyMongo >=4.9 where `_check_name` was removed.
# The patch must run *before* mongoengine is imported so we place it at the very top of this file.
import pymongo.database as _pymongo_database
from pymongo.errors import InvalidName as _InvalidName

if not hasattr(_pymongo_database, "_check_name"):

    def _check_name(name: str) -> None:  # type: ignore
        """Basic replica of the old private helper removed in PyMongo 4.9.
        It performs minimal validation to keep legacy libraries (e.g., mongoengine
        < 0.30) functional.
        """
        if not name:
            raise _InvalidName("database name cannot be the empty string")

        for invalid_char in [" ", ".", "$", "/", "\\", "\x00", '"']:
            if invalid_char in name:
                raise _InvalidName(
                    "database names cannot contain the character %r" % invalid_char
                )

    # Expose the helper where mongoengine expects it.
    _pymongo_database._check_name = _check_name  # type: ignore


from mongoengine import connect, register_connection
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import certifi
from metro.logger import logger


class DatabaseManager:
    def __init__(self):
        self.connections = {}
        self.default_alias = None

    def connect_db(
        self,
        alias: str,
        db_name: str,
        db_url: str,
        is_default: bool = False,
        ssl_reqs: bool = False,
        **kwargs,
    ):
        db_host = f"{db_url}/{db_name}?retryWrites=true&w=majority"
        ssl_kwargs = {} if not ssl_reqs else {"ssl": True, "tlsCAFile": certifi.where()}

        logger.info(
            f"Connecting to database '{db_name}' with alias '{alias}' at: {db_host}..."
        )

        try:
            # Create a MongoClient instance
            client = MongoClient(db_host, **ssl_kwargs, **kwargs)

            # Test the connection
            client.admin.command("ismaster")

            # Register the connection
            if is_default or not self.default_alias:
                connect(db=db_name, host=db_host, alias=alias, **ssl_kwargs, **kwargs)
                self.default_alias = alias
            else:
                register_connection(
                    alias=alias, db=db_name, host=db_host, **ssl_kwargs, **kwargs
                )

            # Store the connection
            self.connections[alias] = client

            logger.info(
                f"Connected to database '{db_name}' with alias '{alias}' at: {db_host}"
            )
            if is_default or self.default_alias == alias:
                logger.info(f"Set as default database connection.")
        except PyMongoError as e:
            logger.error(
                f"Failed to connect to MongoDB '{db_name}' with alias '{alias}': {e}"
            )
            raise

    def get_connection(self, alias: str = None) -> MongoClient:
        if alias is None:
            alias = self.default_alias
        return self.connections.get(alias)

    def close_connections(self):
        for client in self.connections.values():
            client.close()
        self.connections.clear()


# Global instance of DatabaseManager
db_manager = DatabaseManager()
