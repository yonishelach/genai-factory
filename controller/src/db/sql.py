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

from typing import Any, Dict, List, Optional
from sqlalchemy import (JSON, Column, ForeignKey, Index, Enum, BLOB, Table,
                        String, UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, declarative_base, relationship, Mapped, MappedColumn

# Create a base class for declarative class definitions
Base = declarative_base()

ID_LENGTH = 32


def make_label(table):
    class Label(Base):
        __tablename__ = f"{table}_labels"
        __table_args__ = (
            UniqueConstraint("name", "parent", name=f"_{table}_labels_uc"),
            Index(f"idx_{table}_labels_name_value", "name", "value"),
        )

        id: Mapped[int] = MappedColumn(primary_key=True)
        name: Mapped[str]  # in mysql collation="utf8_bin"
        value: Mapped[str]
        parent: Mapped[int] = MappedColumn(ForeignKey(f"{table}.name"))

    return Label


def update_labels(obj, labels: dict):
    old = {label.name: label for label in obj.labels}
    obj.labels.clear()
    for name, value in labels.items():
        if name in old:
            old[name].value = value
            obj.labels.append(old[name])
        else:
            obj.labels.append(obj.Label(name=name, value=value, parent=obj.name))


ingestions = Table(
    "ingestions",
    Base.metadata,
    Column(
        "data_source_id",
        String(length=ID_LENGTH),
        ForeignKey("data_sources.id"),
        primary_key=True,
    ),
    Column(
        "data_source_version",
        String,
        ForeignKey("data_sources.version"),
        primary_key=True,
    ),
    Column(
        "document_id",
        String(length=ID_LENGTH),
        ForeignKey("documents.id"),
        primary_key=True,
    ),
    Column(
        "document_version",
        String,
        ForeignKey("documents.version"),
        primary_key=True,
    ),
    Column("extra_data", JSON),
)


class BaseTable(DeclarativeBase):
    __tablename__ = "base_table"

    id: Mapped[str] = MappedColumn(String(ID_LENGTH), primary_key=True)
    name: Mapped[str]
    version: Mapped[str] = MappedColumn(default="")
    description: Mapped[Optional[str]]
    Label = make_label(__tablename__)
    labels = relationship(Label, cascade="all, delete-orphan")
    owner_id: Mapped[Optional[str]] = MappedColumn(String(ID_LENGTH), ForeignKey("users.name"))
    date_created: Mapped[datetime.datetime] = MappedColumn(default=datetime.datetime.utcnow)
    date_updated: Mapped[Optional[datetime.datetime]] = MappedColumn(
        default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
    )

    def __init__(self, id, name, version=None, description=None, owner_id=None, labels=None):
        super().__init__()
        self.id = id
        self.name = name
        self.version = version
        self.description = description
        self.owner_id = owner_id
        self.labels = labels or []


class Project(BaseTable):
    __tablename__ = "projects"

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
        update_labels(self, {"_GENAI_FACTORY": True})


class SourceType(Enum):
    RELATIONAL = "relational"
    VECTOR = "vector"
    GRAPH = "graph"
    KEY_VALUE = "key-value"
    COLUMN_FAMILY = "column-family"
    STORAGE = "storage"
    OTHER = "other"


class DataSource(BaseTable):
    __tablename__ = "data_sources"
    project_id: Mapped[str] = MappedColumn(String(ID_LENGTH), ForeignKey("projects.id"))
    secret_keys: Mapped[Optional[List[str]]]
    data_source_type: Mapped[SourceType]
    database_kwargs: Mapped[Optional[Dict[str, Any]]]


class Dataset(BaseTable):
    __tablename__ = "datasets"
    project_id: Mapped[str] = MappedColumn(String(ID_LENGTH), ForeignKey("projects.id"))
    credential_id: Mapped[str] = MappedColumn(String(ID_LENGTH), ForeignKey("credentials.id"))
    sources: Mapped[Optional[List[str]]]
    task: Mapped[Optional[str]]
    path: Mapped[Optional[str]]
    producer: Mapped[Optional[JSON]]


class Model(BaseTable):
    __tablename__ = "models"
    project_id: Mapped[str] = MappedColumn(String(ID_LENGTH), ForeignKey("projects.id"))
    model_type: Mapped[str]
    base_model: Mapped[str]
    task: Mapped[Optional[str]]
    path: Mapped[Optional[str]]
    producer: Mapped[Optional[JSON]]
    deployment: Mapped[Optional[str]]


class PromptTemplate(BaseTable):
    __tablename__ = "prompt_templates"
    project_id: Mapped[str] = MappedColumn(String(ID_LENGTH), ForeignKey("projects.id"))
    text: Mapped[str]
    arguments: Mapped[Optional[Dict[str, Any]]]
    model_id: Mapped[Optional[str]] = MappedColumn(String(ID_LENGTH), ForeignKey("models.id"))
    model_version: Mapped[Optional[str]] = MappedColumn(ForeignKey("models.version"))
    generation_config: Mapped[Optional[JSON]]


class Document(BaseTable):
    __tablename__ = "documents"
    project_id: Mapped[str] = MappedColumn(String(ID_LENGTH), ForeignKey("projects.id"))
    path: Mapped[str]
    origin: Mapped[Optional[str]]

    # Many-to-many relationship with DataSource
    ingestions: Mapped[List[DataSource]] = relationship(
        secondary=ingestions, back_populates="documents", lazy=True,
    )


class WorkflowType(Enum):
    ingestion = "ingestion"
    application = "application"
    data_processing = "data_processing"
    training = "training"
    evaluation = "evaluation"


class Workflow(BaseTable):
    __tablename__ = "workflows"
    project_id: Mapped[str] = MappedColumn(String(ID_LENGTH), ForeignKey("projects.id"))
    workflow_type: Mapped[WorkflowType]
    function: Mapped[Optional[str]]
    configuration: Mapped[Optional[JSON]]
    graph: Mapped[Optional[JSON]]
    deployment: Mapped[Optional[str]]


class User(BaseTable):
    __tablename__ = "users"
    project_id: Mapped[str] = MappedColumn(String(ID_LENGTH), ForeignKey("projects.id"))
    full_name: Mapped[str]
    email: Mapped[str]
    policy: Mapped[str]
    features: Mapped[JSON]
    is_admin: Mapped[bool] = MappedColumn(default=False)


class ChatSession(BaseTable):
    __tablename__ = "sessions"
    workflow_id: Mapped[str] = MappedColumn(String(ID_LENGTH), ForeignKey("workflows.id"))
    user_id: Mapped[str] = MappedColumn(String(ID_LENGTH), ForeignKey("users.id"))
    history: Mapped[Optional[BLOB]]

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
        self.history_fields = ["role", "body", "extra_data", "sources", "human_feedback"]
        if history:
            for message in history:
                if not all(key in message for key in self.history_fields):
                    raise ValueError("History message missing required fields")
            self.history = history


