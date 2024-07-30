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

from typing import Optional
from sqlalchemy import (JSON, ForeignKey, Index, LargeBinary,
                        String, UniqueConstraint)
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column, declared_attr

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

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]  # in mysql collation="utf8_bin"
        value: Mapped[str]
        parent: Mapped[int] = mapped_column(ForeignKey(f"{table}.name"))

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
#     Column(
#         "document_id",
#         String(length=ID_LENGTH),
#         ForeignKey("documents.id"),
#         primary_key=True,
#     ),
#     Column(
#         "document_version",
#         String,
#         ForeignKey("documents.version"),
#         primary_key=True,
#     ),
#     Column("extra_data", JSON),
# )


class BaseTable(Base):
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

    id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    name: Mapped[str]
    version: Mapped[str] = mapped_column(default="")
    description: Mapped[Optional[str]]
    owner_id: Mapped[Optional[str]] = mapped_column(String(ID_LENGTH), ForeignKey("users.id"))
    date_created: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    date_updated: Mapped[Optional[datetime.datetime]] = mapped_column(
        default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
    )

    def __init__(self, id, name, version=None, description=None, owner_id=None, labels=None):
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
        print(self.labels)
        update_labels(self, {"_GENAI_FACTORY": True})


class DataSource(BaseTable):
    __tablename__ = "data_sources"
    project_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("projects.id"))
    secret_keys: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    data_source_type: Mapped[str]
    database_kwargs: Mapped[Optional[JSON]] = mapped_column(type_=JSON)

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
    __tablename__ = "datasets"
    project_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("projects.id"))
    credential_id: Mapped[str] = mapped_column(String(ID_LENGTH))
    sources: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    task: Mapped[Optional[str]]
    path: Mapped[Optional[str]]
    producer: Mapped[Optional[JSON]] = mapped_column(type_=JSON)


class Model(BaseTable):
    __tablename__ = "models"
    project_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("projects.id"))
    model_type: Mapped[str]
    base_model: Mapped[str]
    task: Mapped[Optional[str]]
    path: Mapped[Optional[str]]
    producer: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    deployment: Mapped[Optional[str]]


class PromptTemplate(BaseTable):
    __tablename__ = "prompt_templates"
    project_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("projects.id"))
    text: Mapped[str]
    arguments: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    model_id: Mapped[Optional[str]] = mapped_column(String(ID_LENGTH), ForeignKey("models.id"))
    model_version: Mapped[Optional[str]] = mapped_column(ForeignKey("models.version"))
    generation_config: Mapped[Optional[JSON]] = mapped_column(type_=JSON)


class Document(BaseTable):
    __tablename__ = "documents"
    project_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("projects.id"))
    path: Mapped[str]
    origin: Mapped[Optional[str]]

    # Many-to-many relationship with DataSource
    ingestions: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    # ingestions: Mapped[List["DataSource"]] = relationship(
    #     secondary=ingestions, back_populates="documents", lazy=True, foreign_keys=[ingestions.c.document_id, ingestions.c.document_version]
    # )


class Workflow(BaseTable):
    __tablename__ = "workflows"
    project_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("projects.id"))
    workflow_type: Mapped[str]
    function: Mapped[Optional[str]]
    configuration: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    graph: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    deployment: Mapped[Optional[str]]


class User(BaseTable):
    __tablename__ = "users"
    project_id: Mapped[Optional[str]] = mapped_column(String(ID_LENGTH), ForeignKey("projects.id"))
    full_name: Mapped[str]
    email: Mapped[str]
    policy: Mapped[Optional[str]]
    features: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    is_admin: Mapped[bool] = mapped_column(default=False)

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
        project_id=None,
        labels=None,
    ):
        super().__init__(id, name, version, description, owner_id, labels=labels)
        self.email = email
        self.full_name = full_name
        self.is_admin = is_admin
        self.project_id = project_id
        self.policy = policy
        self.features = features


class ChatSession(BaseTable):
    __tablename__ = "sessions"
    workflow_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("workflows.id"))
    user_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("users.id"))
    history: Mapped[Optional[bytes]] = mapped_column(LargeBinary)  # BLOB in MySQL

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


