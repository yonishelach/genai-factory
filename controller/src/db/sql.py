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

import datetime
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Column,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    declared_attr,
    foreign,
    mapped_column,
    relationship,
)

# Create a base class for declarative class definitions
Base = declarative_base()

ID_LENGTH = 32


def make_label(table: str) -> Base:
    """
    Create a label table for a given table.

    :param table: The table name of the parent table.

    :return: The label table.
    """

    class Label(Base):
        """
        The label table that stores labels for a parent table.
        """

        __tablename__ = f"{table}_labels"
        __table_args__ = (
            UniqueConstraint("name", "parent", name=f"_{table}_labels_uc"),
            Index(f"idx_{table}_labels_name_value", "name", "value"),
        )

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]  # in mysql collation="utf8_bin"
        value: Mapped[str]
        parent: Mapped[int] = mapped_column(ForeignKey(f"{table}.name"))

    return Label


def update_labels(obj: Base, labels: dict):
    """
    Update the labels of a table object.

    :param obj:     The table object.
    :param labels:  The labels to update.

    :return: None
    """
    old = {label.name: label for label in obj.labels}
    obj.labels.clear()
    for name, value in labels.items():
        if name in old:
            old[name].value = value
            obj.labels.append(old[name])
        else:
            obj.labels.append(obj.Label(name=name, value=value, parent=obj.name))


# ingestions = Table(
#     "ingestions",
#     Base.metadata,
#     Column(
#         "data_source_id",
#         String(length=ID_LENGTH),
#         ForeignKey("data_sources.id"),
#         primary_key=True,
#     ),
#     Column(
#         "data_source_version",
#         String,
#         ForeignKey("data_sources.version"),
#         primary_key=True,
#     ),
#     Column("extra_data", JSON),
# )


class BaseTable(Base):
    """
    Base class for all tables.
    We use this class to define common columns and methods for all tables.

    :arg  id: unique identifier for each entry.
    :arg  name: entry's name.
    :arg  version: The entry's version.
    :arg  description: The entry's description.
    :arg  owner_id: The entry's owner's id.

    The following columns are automatically added to each table:
    - date_created: The entry's creation date.
    - date_updated: The entry's last update date.

    """

    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        return "base_table"

    @declared_attr
    def Label(cls):
        return make_label(cls.__tablename__)

    @declared_attr
    def labels(cls):
        return relationship(cls.Label, cascade="all, delete-orphan")

    # Columns:
    id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    name: Mapped[str]
    version: Mapped[str] = mapped_column(default="")
    description: Mapped[Optional[str]]
    owner_id: Mapped[Optional[str]] = mapped_column(
        String(ID_LENGTH), ForeignKey("users.id")
    )
    date_created: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.utcnow
    )
    date_updated: Mapped[Optional[datetime.datetime]] = mapped_column(
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    def __init__(
        self, id, name, version=None, description=None, owner_id=None, labels=None
    ):
        self.id = id
        self.name = name
        self.version = version
        self.description = description
        self.owner_id = owner_id
        self.labels = labels or []


class Project(BaseTable):
    """
    The Project table which is used as a workspace. The other tables are associated with a project.
    """

    __tablename__ = "projects"

    # Relationships (All the relationships here are one-to-many):
    relationship_args = {"back_populates": "project", "cascade": "all, delete-orphan"}
    models: Mapped[List["Model"]] = relationship(**relationship_args)
    prompt_templates: Mapped[List["PromptTemplate"]] = relationship(**relationship_args)
    data_sources: Mapped[List["DataSource"]] = relationship(**relationship_args)
    datasets: Mapped[List["Dataset"]] = relationship(**relationship_args)
    documents: Mapped[List["Document"]] = relationship(**relationship_args)
    workflows: Mapped[List["Workflow"]] = relationship(**relationship_args)

    def __init__(
        self,
        id,
        name,
        version=None,
        description=None,
        owner_id=None,
        labels=None,
    ):
        super().__init__(id, name, version, description, owner_id, labels)
        print(self.labels)
        update_labels(self, {"_GENAI_FACTORY": True})


class DataSource(BaseTable):
    """
    The DataSource table which is used to define data sources for the project.

    :arg  project_id:       The project's id.
    :arg  secret_keys:      The secret keys for the data source.
    :arg  data_source_type: The type of the data source.
                            Can be one of the values in controller.src.schemas.data_source.DataSourceType.
    :arg  database_kwargs:  The database keyword arguments.
    """

    __tablename__ = "data_sources"

    # Columns:
    project_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("projects.id")
    )
    secret_keys: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    data_source_type: Mapped[str]
    database_kwargs: Mapped[Optional[JSON]] = mapped_column(type_=JSON)

    # Relationships:

    # Many-to-one relationship with projects:
    project: Mapped["Project"] = relationship(back_populates="data_sources")
    # One-to-many relationship with documents:
    document: Mapped["Document"] = relationship(back_populates="data_sources")
    # documents: Mapped["Document"] = relationship(back_populates="data_source")

    def __init__(
        self,
        id,
        name,
        version,
        description,
        owner_id,
        project_id,
        secret_keys=None,
        data_source_type=None,
        database_kwargs=None,
        labels=None,
    ):
        super().__init__(id, name, version, description, owner_id, labels=labels)
        self.project_id = project_id
        self.secret_keys = secret_keys
        self.data_source_type = data_source_type
        self.database_kwargs = database_kwargs


class Dataset(BaseTable):
    """
    The Dataset table which is used to define datasets for the project.

    :arg  project_id:       The project's id.
    :arg  credential_id:    The credential's id.
    :arg  sources:          The sources of the dataset.
    :arg  task:             The task of the dataset.
    :arg  path:             The path to the dataset.
    :arg  producer:         The producer of the dataset.
    """

    __tablename__ = "datasets"

    # Columns:
    project_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("projects.id")
    )
    credential_id: Mapped[str] = mapped_column(String(ID_LENGTH))
    sources: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    task: Mapped[Optional[str]]
    path: Mapped[Optional[str]]
    producer: Mapped[Optional[JSON]] = mapped_column(type_=JSON)

    # Relationships:

    # Many-to-one relationship with projects:
    project: Mapped["Project"] = relationship(back_populates="datasets")


class Model(BaseTable):
    """
    The Model table which is used to define models for the project.

    :arg  project_id:       The project's id.
    :arg  model_type:       The type of the model. Can be one of the values in controller.src.schemas.model.ModelType.
    :arg  base_model:       The base model.
    :arg  task:             The task of the model. For example, "classification", "text-generation", etc.
    :arg  path:             The path to the model.
    :arg  producer:         The producer of the model. Link to the logging function –
                            either the training run or manual log from the user.
    :arg  deployment:       A serving function URI for the model server or gateway.
                            In future versions we might want to allow multiple deployments for a model.

    """

    __tablename__ = "models"

    # Columns:
    project_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("projects.id")
    )
    model_type: Mapped[str]
    base_model: Mapped[str]
    task: Mapped[Optional[str]]
    path: Mapped[Optional[str]]
    producer: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    deployment: Mapped[Optional[str]]

    # Relationships:

    # Many-to-one relationship with projects:
    project: Mapped["Project"] = relationship(back_populates="models")
    # One-to-one relationship with prompt_templates:
    prompt_template: Mapped["PromptTemplate"] = relationship(
        back_populates="model",
        foreign_keys="[PromptTemplate.model_id]"
    )


class PromptTemplate(BaseTable):
    """
    The PromptTemplate table which is used to define prompt templates for the project.
    Each prompt template is associated with a model.

    :arg    project_id:         The project's id.
    :arg    text:               The text of the prompt.
    :arg    arguments:          The arguments of the prompt. Those arguments are used to fill the prompt template.
    :arg    model_id:           The model's id.
    :arg    model_version:      The model's version.
    :arg    generation_config:  The model's generation configuration when using this prompt.
    """

    __tablename__ = "prompt_templates"

    # Columns:
    project_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("projects.id")
    )
    text: Mapped[str]
    arguments: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    model_id: Mapped[Optional[str]] = mapped_column(
        String(ID_LENGTH), ForeignKey("models.id")
    )
    model_version: Mapped[Optional[str]] = mapped_column(ForeignKey("models.version"))
    generation_config: Mapped[Optional[JSON]] = mapped_column(type_=JSON)

    # Relationships:

    # Many-to-one relationship with projects:
    project: Mapped["Project"] = relationship(back_populates="prompt_templates")
    # One-to-one relationship with models:
    model: Mapped["Model"] = relationship(
        back_populates="prompt_template",
        foreign_keys="[PromptTemplate.model_id]"
    )


class Document(BaseTable):
    """
    The Document table which is used to define documents for the project. The documents are ingested into data sources.

    :arg    project_id:     The project's id.
    :arg    path:           The path to the document. Can be a remote file or a web page.
    :arg    origin:         The origin location of the document.
    """
    __tablename__ = "documents"

    # Columns:
    project_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("projects.id")
    )
    path: Mapped[str]
    origin: Mapped[Optional[str]]
    # TODO: This is for the relationship with data_sources, need to solve this relationship
    data_source_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("data_sources.id")
    )

    # Relationships:

    # Many-to-one relationship with projects:
    project: Mapped["Project"] = relationship(back_populates="documents")
    # One-to-many relationship with ingestion:
    data_sources: Mapped[List["DataSource"]] = relationship(back_populates="document")


class Workflow(BaseTable):
    """
    The Workflow table which is used to define workflows for the project.
    All workflows are a DAG of steps, each with its dedicated task.

    :arg    project_id:     The project's id.
    :arg    workflow_type:  The type of the workflow.
                            Can be one of the values in controller.src.schemas.workflow.WorkflowType.
    :arg    function:       The pipeline python file path. If the workflow was built from code.
    :arg    configuration:  The configuration of the workflow.
    :arg    graph:          The graph of steps that define the workflow.
    :arg    deployment:     The serving function URI for the workflow server or gateway.
                            In future versions we might want to allow multiple deployments for a workflow.
    """
    __tablename__ = "workflows"

    # Columns:
    project_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("projects.id")
    )
    workflow_type: Mapped[str]
    function: Mapped[Optional[str]]
    configuration: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    graph: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    deployment: Mapped[Optional[str]]

    # Relationships:

    # Many-to-one relationship with projects:
    project: Mapped["Project"] = relationship(back_populates="workflows")
    # One-to-many relationship with sessions:
    sessions: Mapped[List["ChatSession"]] = relationship(back_populates="workflow")


# Many-to-many relationship between users and projects:
user_projects = Table(
    "user_projects",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id")),
    Column("user_id", ForeignKey("users.id")),
)


class User(BaseTable):
    """
    The User table which is used to define users.

    :arg    full_name:  The user's full name.
    :arg    email:      The user's email.
    :arg    policy:     The user's policy.
    :arg    features:   The user's features. Like the user's role, age, etc.
    :arg    is_admin:   Whether the user is an admin or not.
    """
    __tablename__ = "users"

    # Columns:
    full_name: Mapped[str]
    email: Mapped[str]
    policy: Mapped[Optional[str]]
    features: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    is_admin: Mapped[bool] = mapped_column(default=False)

    # Relationships:

    # Many-to-many relationship with projects:
    projects: Mapped[List["Project"]] = relationship(secondary=user_projects)
    # One-to-many relationship with sessions:
    sessions: Mapped[List["ChatSession"]] = relationship(back_populates="user", foreign_keys="ChatSession.user_id")

    def __init__(
        self,
        id,
        name,
        version,
        description,
        owner_id,
        full_name,
        email,
        policy=None,
        features=None,
        is_admin=False,
        labels=None,
    ):
        super().__init__(id, name, version, description, owner_id, labels=labels)
        self.email = email
        self.full_name = full_name
        self.is_admin = is_admin
        self.policy = policy
        self.features = features


class ChatSession(BaseTable):
    """
    The Chat Session table which is used to define chat sessions of an application workflow per user.

    :arg    workflow_id:    The workflow's id.
    :arg    user_id:        The user's id.
    :arg    history:        The chat session's history. List of messages sent in the session.

    """
    __tablename__ = "sessions"

    # Columns:
    workflow_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("workflows.id")
    )
    user_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("users.id"))
    history: Mapped[Optional[bytes]] = mapped_column(LargeBinary)  # BLOB in MySQL

    # Relationships:

    # Many-to-one relationship with workflows:
    workflow: Mapped["Workflow"] = relationship(back_populates="sessions")
    # Many-to-one relationship with users:
    user: Mapped["User"] = relationship(back_populates="sessions", foreign_keys=[user_id])

    def __init__(
        self,
        id,
        name,
        project_id,
        version=None,
        description=None,
        owner_id=None,
        labels=None,
        workflow_id=None,
        user_id=None,
        history=None,
    ):
        super().__init__(id, name, version, description, owner_id, labels)
        self.project_id = project_id
        self.workflow_id = workflow_id
        self.user_id = user_id
        self.history_fields = [
            "role",
            "body",
            "extra_data",
            "sources",
            "human_feedback",
        ]
        if history:
            for message in history:
                if not all(key in message for key in self.history_fields):
                    raise ValueError("History message missing required fields")
            self.history = history
