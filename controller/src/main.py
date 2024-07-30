# Copyright 2023 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# main file with cli commands using python click library
# include two click commands: 1. data ingestion (using the data loader), 2. query (using the agent)
import json

import click
import yaml
from tabulate import tabulate

# from controller.src.sqlclient import client
from controller.src.db_clients import client
from controller.src.schemas import User, DataSource, Project, QueryItem
# from controller.src.model import User, DocCollection, QueryItem
from controller.src.config import config
# import controller.src.api as api
from controller.src.api.utils import _send_to_application


@click.group()
def cli():
    pass


# click command for initializing the database tables
@click.command()
def initdb():
    """Initialize the database (delete old tables)"""
    click.echo("Running Init DB")
    session = client.get_db_session()
    client.create_tables(True)

    # Create admin user:
    click.echo("Creating admin user")
    client.create_user(
        User(
            name="admin",
            email="example@example.com",
            full_name="Admin User",
            is_admin=True,
        ),
        session=session,
    )
    user = client.get_user("admin", session=session).data
    # Create project:
    click.echo("Creating default project")
    client.create_project(
        Project(
            name="default",
            description="Default Project",
            owner_id=user.id,
        ),
        session=session,
    )
    project = client.get_project("default", session=session).data

    # Create data source:
    click.echo("Creating default data source")
    client.create_data_source(
        DataSource(
            name="default",
            description="Default Data Source",
            owner_id=user.id,
            project_id=project.id,
            data_source_type="vector",
        ),
        session=session,
    )
    session.close()


@click.command("config")
def print_config():
    """Print the config as a yaml file"""
    click.echo("Running Config")
    click.echo(yaml.dump(config.dict()))


@click.command()
@click.argument("path", type=str)
@click.option("-l", "--loader", type=str, help="Type of data loader")
@click.option(
    "-m", "--metadata", type=(str, str), multiple=True, help="Metadata Key value pair"
)
@click.option("-v", "--version", type=str, help="document version")
@click.option("-c", "--collection", type=str, help="Vector DB collection name")
@click.option(
    "-f", "--from-file", is_flag=True, help="Take the document paths from the file"
)
def ingest(path, loader, metadata, version, collection, from_file):
    """Ingest documents into the vector database"""
    params = {
        "path": path,
        "from_file": from_file,
        "version": version,
    }
    if metadata:
        print(metadata)
        params["metadata"] = json.dumps({metadata[0]: metadata[1]})

    collection = collection or "default"
    click.echo(f"Running Data Ingestion from: {path} with loader: {loader}")
    response = _send_to_application(
        path=f"collections/{collection}/{loader}/ingest",
        method="POST",
        params=params,
    )
    if response["status"] == "ok":
        click.echo("Ingestion completed successfully")
    else:
        click.echo("Ingestion failed")


@click.command()
@click.argument("question", type=str)
@click.option(
    "-f",
    "--filter",
    type=(str, str),
    multiple=True,
    help="Search filter Key value pair",
)
@click.option("-c", "--collection", type=str, help="Vector DB collection name")
@click.option("-u", "--user", type=str, help="Username")
@click.option("-s", "--session", type=str, help="Session ID")
@click.option(
    "-n", "--pipeline-name", type=str, default="default", help="Pipeline name"
)
def query(question, filter, collection, user, session, pipeline_name):
    """Run a chat query on the vector database collection"""
    click.echo(f"Running Query for: {question}")
    search_args = [filter] if filter else None
    query_item = QueryItem(
        question=question,
        session_id=session,
        filter=search_args,
        collection=collection,
    )
    data = json.dumps(query_item.dict())

    headers = {"x_username": user} if user else {}
    response = _send_to_application(
        path=f"pipeline/{pipeline_name}/run",
        method="POST",
        data=data,
        headers=headers,
    )
    result = response["data"]
    click.echo(result["answer"])
    click.echo(sources_to_text(result["sources"]))


@click.group()
def list():
    """List the different objects in the database (by category)"""
    pass


@click.group()
def update():
    """Create or update an object in the database"""
    pass


@click.command("users")
@click.option("-u", "--user", type=str, help="user name filter")
@click.option("-e", "--email", type=str, help="email filter")
def list_users(user, email):
    """List users"""
    click.echo("Running List Users")

    data = client.list_users(email, user, output_mode="short")
    table = format_table_results(data)
    click.echo(table)


# add a command to list document collections, similar to the list users command
# @click.command("collections")
# @click.option("-o", "--owner", type=str, help="owner filter")
# @click.option(
#     "-m", "--metadata", type=(str, str), multiple=True, help="metadata filter"
# )
# def list_collections(owner, metadata):
#     """List document collections"""
#     click.echo("Running List Collections")
#
#     data = client.list_collections(owner, metadata, output_mode="short")
#     table = format_table_results(data)
#     click.echo(table)


# @click.command("collection")
# @click.argument("name", type=str)
# @click.option("-o", "--owner", type=str, help="owner name")
# @click.option("-d", "--description", type=str, help="collection description")
# @click.option("-c", "--category", type=str, help="collection category")
# @click.option(
#     "-l", "--labels", multiple=True, default=[], help="metadata labels filter"
# )
# def update_collection(name, owner, description, category, labels):
#     """Create or update a document collection"""
#     click.echo("Running Create or Update Collection")
#     labels = fill_params(labels)
#
#     session = client.get_db_session()
#     # check if the collection exists, if it does, update it, otherwise create it
#     collection_exists = client.get_collection(name, session=session).success
#     if collection_exists:
#         client.update_collection(
#             session=session,
#             collection=DocCollection(
#                 name=name, description=description, category=category, labels=labels
#             ),
#         ).with_raise()
#     else:
#         client.create_collection(
#             session=session,
#             collection=DocCollection(
#                 name=name,
#                 description=description,
#                 owner_name=owner,
#                 category=category,
#                 labels=labels,
#             ),
#         ).with_raise()


# add a command to list chat sessions, similar to the list_users command
@click.command("sessions")
@click.option("-u", "--user", type=str, help="user name filter")
@click.option("-l", "--last", type=int, default=0, help="last n sessions")
@click.option("-c", "--created", type=str, help="created after date")
def list_sessions(user, last, created):
    """List chat sessions"""
    click.echo("Running List Sessions")

    data = client.list_sessions(user, created, last, output_mode="short")
    table = format_table_results(data["data"])
    click.echo(table)


def sources_to_text(sources):
    """Convert a list of sources to a string."""
    if not sources:
        return ""
    return "\nSource documents:\n" + "\n".join(
        f"- {get_title(source)} ({source['source']})" for source in sources
    )


def sources_to_md(sources):
    """Convert a list of sources to a Markdown string."""
    if not sources:
        return ""
    sources = {
        source.metadata["source"]: get_title(source.metadata) for source in sources
    }
    return "\n**Source documents:**\n" + "\n".join(
        f"- [{title}]({url})" for url, title in sources.items()
    )


def get_title(metadata):
    """Get title from metadata."""
    if "chunk" in metadata:
        return f"{metadata.get('title', '')}-{metadata['chunk']}"
    if "page" in metadata:
        return f"{metadata.get('title', '')} - page {metadata['page']}"
    return metadata.get("title", "")


def fill_params(params, params_dict=None):
    params_dict = params_dict or {}
    for param in params:
        i = param.find("=")
        if i == -1:
            continue
        key, value = param[:i].strip(), param[i + 1 :].strip()
        if key is None:
            raise ValueError(f"cannot find param key in line ({param})")
        params_dict[key] = value
    if not params_dict:
        return None
    return params_dict


def format_table_results(table_results):
    return tabulate(table_results, headers="keys", tablefmt="fancy_grid")


cli.add_command(ingest)
cli.add_command(query)
cli.add_command(initdb)
cli.add_command(print_config)

cli.add_command(list)
list.add_command(list_users)
# list.add_command(list_collections)
list.add_command(list_sessions)

cli.add_command(update)
# update.add_command(update_collection)

if __name__ == "__main__":
    cli()
