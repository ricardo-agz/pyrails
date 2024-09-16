import subprocess
import shutil
import os
import click


def start_mongodb(config, method):
    db_url = getattr(config, "DATABASE_URL", None)
    click.echo(f"Current DATABASE_URL: {db_url}")

    if not db_url or not db_url.startswith("mongodb://"):
        db_url = f"mongodb://localhost:27017/{config.DB_NAME}"
        click.echo(f"Setting DATABASE_URL to: {db_url}")
        config.update_config_file("DATABASE_URL", db_url)

    if method == "docker":
        start_docker_mongodb(config.DB_NAME, config.ENV)
    elif method == "local":
        start_local_mongodb(config.DB_NAME)
    else:
        provide_manual_instructions(db_url)


def stop_mongodb(env, method):
    if method == "docker":
        stop_docker_mongodb(env)
    elif method == "local":
        stop_local_mongodb()
    else:
        click.echo(
            "For manual setups, please stop your MongoDB instance using your preferred method."
        )


def start_docker_mongodb(db_name, env):
    if not shutil.which("docker"):
        click.echo(
            "Docker is not installed. Please install Docker to use this feature."
        )
        return

    container_name = f"pyrails-mongodb-{env}"
    cmd = [
        "docker",
        "run",
        "-d",
        "--name",
        container_name,
        "-p",
        "27017:27017",
        "-e",
        f"MONGO_INITDB_DATABASE={db_name}",
        "mongo:latest",
    ]

    try:
        subprocess.run(cmd, check=True)
        click.echo(f"MongoDB container '{container_name}' is running.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to start MongoDB container: {e}")


def start_local_mongodb(db_name):
    if not shutil.which("mongod"):
        click.echo(
            "MongoDB is not installed. Please install MongoDB to use this feature."
        )
        return

    data_dir = os.path.join(os.getcwd(), "data", "db")
    os.makedirs(data_dir, exist_ok=True)

    cmd = [
        "mongod",
        "--dbpath",
        data_dir,
        "--fork",  # Run in background
        "--logpath",
        os.path.join(os.getcwd(), "mongodb.log"),
    ]

    try:
        subprocess.run(cmd, check=True)
        click.echo(f"Local MongoDB instance started. Data directory: {data_dir}")
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to start local MongoDB: {e}")


def provide_manual_instructions(db_url):
    click.echo("Manual database setup instructions:")
    click.echo(f"1. Install MongoDB on your system if not already installed.")
    click.echo(f"2. Start MongoDB using your preferred method.")
    click.echo(f"3. Ensure your MongoDB is accessible at: {db_url}")
    click.echo(f"4. Create a database named: {db_url.split('/')[-1]}")
    click.echo("5. Update your PyRails configuration if necessary.")


def stop_docker_mongodb(env):
    container_name = f"pyrails-mongodb-{env}"
    try:
        subprocess.run(["docker", "stop", container_name], check=True)
        subprocess.run(["docker", "rm", container_name], check=True)
        click.echo(
            f"MongoDB container '{container_name}' has been stopped and removed."
        )
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to stop or remove MongoDB container: {e}")


def stop_local_mongodb():
    try:
        subprocess.run(["mongod", "--shutdown"], check=True)
        click.echo("Local MongoDB instance has been stopped.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to stop local MongoDB: {e}")
