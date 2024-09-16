# PyRails

PyRails is a lightweight, opinionated, batteries-included Python web framework built on top of FastAPI and MongoEngine.   
It is means to provide helpful, lightweight abstractions to enable standard ways of implementing common patters to 
prevent the SaaSification of the developer stack. 

**The goal is to enhance not inhibit.**


## Features

- Built on top of FastAPI and MongoEngine ODM
- CLI tool for project management and code generation
- Built-in database management (MongoDB)
- Support for both local and Docker-based development
- Environment-specific configurations
- Automatic API documentation


## Installation

Install PyRails using pip:

`pip install pyrails`

## Creating a New Project

Create a new PyRails project using the `new` command:

```
pyrails new my_project
cd my_project
```

This will create a new directory `myapp` with the default project structure:

```
myapp/
├── app/
│   ├── controllers/
│   ├── models/
│   └── __init__.py
├── config/
│   ├── development.py
│   ├── production.py  
│   └── __init__.py
├── main.py
├── Dockerfile
└── docker-compose.yml
```

## Starting the Development Server

Start the development server using the `run` command:

```
pyrails run
```

This will start the development server on http://localhost:8000.


You can also run the service using Docker:

```
pyrails run --docker
```


## Scaffolding Resources

PyRails includes a scaffold generator to quickly create models, controllers, and route definitions for a new resource.

To generate a scaffold for a `Post` resource with `title` and `body` fields:

```
pyrails generate scaffold Post title:str body:str
```

This will generate:

- `app/models/post.py` with a `Post` model class
- `app/controllers/posts_controller.py` with CRUD route handlers
- Update `app/controllers/__init__.py` to import the new controller
- Update `app/models/__init__.py` to import the new model 

## Generating Models and Controllers

You can also generate models and controllers individually.

### Generating a Model

To generate a `Comment` model with `post_id`, `author`, and `content` fields:

```
pyrails generate model Comment post_id:str author:str content:str
```

### Generating a Controller

To generate a controller for `Comment` resources:

```
pyrails generate controller Comments
```

### More field types

#### Defining Relationships and Field Options

When generating models, you can define relationships between models and specify field options.

- **One-to-Many Relationship**: Use the `ref:` prefix followed by the related model name.

```
pyrails generate model Post author:ref:User
```

This will generate a `Post` model with an `author` field referencing the `User` model.

- **Many-to-Many Relationship**: Use `list:` and `ref:` together.

```
pyrails generate model Student courses:list:ref:Course
```

This will generate a `Student` model with a `courses` field that is a list of references to `Course` models.

- **Optional Field**: Append `_` to the field name to mark it as optional.

```
pyrails generate model User email_:str
```

This will generate a `User` model with an optional `email` field.

- **Unique Field**: Append `^` to the field name to specify it as unique.

```
pyrails generate model User username^:str
```

This will generate a `User` model with a unique `username` field.

#### Specialty Field Types

- **Hashed Field**: Use `_hashed:` suffix to store the field as a hashed value.

```
pyrails generate model User name:str password_hashed:str
```

This will generate a `User` model with a `password` field stored as a hashed value.

- **Encrypted Field**: Use `_encrypted:` suffix to store the field as an encrypted value.

```
pyrails generate model User name:str email_encrypted:str secret_note_encrypted:str
```

This will generate a `User` model with `email` and `secret_note` fields stored as encrypted values.

PyRails supports the following field types: `str`, `int`, `float`, `bool`, `datetime`, `date`, `dict`, `list`.

## Database Management

PyRails provides commands to manage your MongoDB database.

### Starting a Local MongoDB Instance

To start a local MongoDB instance for development:

```
pyrails db up
```

### Stopping the Local MongoDB Instance

To stop the local MongoDB instance:

```
pyrails db down
```

### Running MongoDB in a Docker Container

You can also specify the environment and run MongoDB in a Docker container:

```
pyrails db up --env production --docker
```

## Configuration

Environment-specific configuration files are located in the `config` directory:

- `config/development.py`
- `config/production.py`

Here you can set your `DATABASE_URL`, API keys, and other settings that vary between environments.

## Testing

Write tests in the `tests` directory. You can run your test suite using:

```
python -m pytest
```

## Documentation and Help

- **API Documentation**: http://localhost:8000/docs
- **CLI help**: `pyrails --help`

For guides, tutorials, and detailed API references, check out the PyRails documentation site.


## License

PyRails is open-source software licensed under the MIT license.
