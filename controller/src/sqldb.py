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

import sqlalchemy
from sqlalchemy import (Boolean, JSON, Column, DateTime, ForeignKey, Index, Integer,
                        String, UniqueConstraint, Table)
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import declarative_base, relationship

# Create a base class for declarative class definitions
Base = declarative_base()
TEXT_LENGTH = 255
ID_LENGTH = 64


def make_label(table):
    class Label(Base):
        __tablename__ = f"{table}_labels"
        __table_args__ = (
            UniqueConstraint("name", "parent", name=f"_{table}_labels_uc"),
            Index(f"idx_{table}_labels_name_value", "name", "value"),
        )

        id = Column(Integer, primary_key=True)
        name = Column(String(255, None))  # in mysql collation="utf8_bin"
        value = Column(String(255, collation=None))
        parent = Column(Integer, ForeignKey(f"{table}.name"))

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


# Association table between users and projects for many-to-many relationship
user_project = Table(
    "user_project",
    Base.metadata,
    Column("user_uid", ForeignKey("users.uid")),
    Column("project_uid", ForeignKey("projects.uid")),
    Column("project_version", ForeignKey("projects.version")),
)

# Association table between documents and data sources (ingestions) for many-to-many relationship
ingestions = Table(
    "ingestions",
    Base.metadata,
    Column("document_uid", String(ID_LENGTH), ForeignKey("documents.uid")),
    Column("document_version", String(TEXT_LENGTH), ForeignKey("documents.version")),
    Column("data_source_uid", String(ID_LENGTH), ForeignKey("data_sources.uid")),
    Column("data_source_version", String(TEXT_LENGTH), ForeignKey("data_sources.version")),
    Column("extra_data", JSON),
)


class User(Base):
    __tablename__ = "users"

    # Columns:
    uid = Column(String(ID_LENGTH), primary_key=True, nullable=False)
    name = Column(String(TEXT_LENGTH), primary_key=False, nullable=False)
    description = Column(String(TEXT_LENGTH), nullable=True, default="")
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    spec = Column(MutableDict.as_mutable(JSON), nullable=True)
    Label = make_label(__tablename__)
    labels = relationship(Label, cascade="all, delete-orphan")
    email = Column(String(TEXT_LENGTH), nullable=False, unique=True)
    full_name = Column(String(TEXT_LENGTH), nullable=False)

    # Relationships:

    # many-to-many relationship with the 'Project' table
    projects = relationship("Project", secondary=user_project, back_populates="users")
    # one-to-many relationship with the 'ChatSession' table
    chat_sessions = relationship("ChatSession", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    # Columns:
    uid = Column(String(ID_LENGTH), primary_key=True, nullable=False)
    version = Column(String(TEXT_LENGTH), primary_key=True, nullable=False, default="")
    name = Column(String(TEXT_LENGTH), primary_key=True, nullable=False)
    description = Column(String(TEXT_LENGTH), nullable=True, default="")
    owner_id = Column(String(ID_LENGTH), ForeignKey("users.name"), nullable=False)
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    spec = Column(MutableDict.as_mutable(JSON), nullable=True)
    Label = make_label(__tablename__)
    labels = relationship(Label, cascade="all, delete-orphan")

    # Relationships:

    # one-to-many relationship with the 'Model' table
    models = relationship("Model", back_populates="project")
    # one-to-many relationship with the 'PromptTemplate' table
    prompt_templates = relationship("PromptTemplate", back_populates="project")
    # one-to-many relationship with the 'Dateset' table
    datasets = relationship("Dataset", back_populates="project")
    # one-to-many relationship with the 'DataSource' table
    data_sources = relationship("DataSource", back_populates="project")
    # one-to-many relationship with the 'Document' table
    documents = relationship("Document", back_populates="project")
    # one-to-many relationship with the 'Workflow' table
    workflows = relationship("Workflow", back_populates="project")
    # many-to-many relationship with the 'User' table
    users = relationship("User", secondary=user_project, back_populates="projects")

    def __init__(self, uid, version, name, description, owner_id, created, updated, spec, labels):
        self.uid = uid
        self.version = version
        self.name = name
        self.description = description
        self.owner_id = owner_id
        self.created = created
        self.updated = updated
        self.spec = spec
        self.labels = labels

        update_labels(self, {"_GENAI_FACTORY": "true"})


class DataSource(Base):
    __tablename__ = "data_sources"

    # Columns:
    uid = Column(String(ID_LENGTH), primary_key=True, nullable=False)
    version = Column(String(TEXT_LENGTH), primary_key=True, nullable=False, default="")
    name = Column(String(TEXT_LENGTH), nullable=False)
    description = Column(String(TEXT_LENGTH), nullable=True, default="")
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    spec = Column(MutableDict.as_mutable(JSON), nullable=True)
    Label = make_label(__tablename__)
    labels = relationship(Label, cascade="all, delete-orphan")
    owner_id = Column(String(ID_LENGTH), sqlalchemy.ForeignKey("users.uid"), nullable=False)
    data_source_type = Column(String(TEXT_LENGTH), nullable=True)
    project_id = Column(String(ID_LENGTH), ForeignKey("projects.uid"), nullable=False)

    # Relationships:

    # many-to-one relationship with the 'Project' table
    project = relationship("Project", back_populates="data_sources")
    # many-to-many relationship with the 'Document' table
    documents = relationship("Document", secondary=ingestions, back_populates="ingestions")
    # TODO: add a many-to-one relationship with the 'Credentials' table in the next version


class Dataset(Base):
    __tablename__ = "datasets"

    uid = Column(String(ID_LENGTH), primary_key=True, nullable=False)
    version = Column(String(TEXT_LENGTH), primary_key=True, nullable=False, default="")
    name = Column(String(TEXT_LENGTH), nullable=False)
    description = Column(String(TEXT_LENGTH), nullable=True, default="")
    owner_id = Column(String(ID_LENGTH), ForeignKey("users.name"), nullable=False)
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    spec = Column(MutableDict.as_mutable(JSON), nullable=True)
    Label = make_label(__tablename__)
    labels = relationship(Label, cascade="all, delete-orphan")
    task = Column(String(TEXT_LENGTH), nullable=True)
    path = Column(String(TEXT_LENGTH), nullable=True)
    producer = Column(JSON, nullable=True)
    project_id = Column(String(ID_LENGTH), ForeignKey("projects.uid"), nullable=False)

    # Relationships:

    # many-to-one relationship with the 'Project' table
    project = relationship("Project", back_populates="datasets")
    # TODO: add a many-to-one relationship with the 'Credentials' table


class Model(Base):
    __tablename__ = "models"

    uid = Column(String(ID_LENGTH), primary_key=True, nullable=False)
    version = Column(String(TEXT_LENGTH), primary_key=True, nullable=False, default="")
    name = Column(String(TEXT_LENGTH), nullable=False)
    description = Column(String(TEXT_LENGTH), nullable=True, default="")
    owner_id = Column(String(ID_LENGTH), ForeignKey("users.name"), nullable=False)
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    spec = Column(MutableDict.as_mutable(JSON), nullable=True)
    Label = make_label(__tablename__)
    labels = relationship(Label, cascade="all, delete-orphan")
    project_id = Column(String(ID_LENGTH), ForeignKey("projects.uid"), nullable=False)
    model_type = Column(String(TEXT_LENGTH), nullable=True)
    base_model = Column(String(TEXT_LENGTH), nullable=True)
    task = Column(String(TEXT_LENGTH), nullable=True)

    # Relationships:

    # many-to-one relationship with the 'Project' table
    project = relationship("Project", back_populates="models")
    # one-to-one relationship with the 'PromptTemplate' table
    prompt_template = relationship("PromptTemplate", back_populates="model", uselist=False)


class PromptTemplate(Base):
    __tablename__ = "prompts"

    # Columns:
    uid = Column(String(ID_LENGTH), primary_key=True, nullable=False)
    name = Column(String(TEXT_LENGTH), primary_key=True, nullable=False)
    version = Column(String(TEXT_LENGTH), primary_key=True, nullable=False)
    description = Column(String(TEXT_LENGTH), nullable=True)
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    spec = Column(MutableDict.as_mutable(JSON), nullable=True)
    Label = make_label(__tablename__)
    labels = relationship(Label, cascade="all, delete-orphan")
    text = Column(String(TEXT_LENGTH), nullable=True)
    project_id = Column(String(ID_LENGTH), ForeignKey("projects.uid"), nullable=False)
    model_id = Column(String(ID_LENGTH), ForeignKey("models.uid"), nullable=False)

    # Relationships:

    # many-to-one relationship with the 'Project' table
    project = relationship("Project", back_populates="prompt_templates")
    # one-to-one relationship with the 'Model' table
    model = relationship("Model", back_populates="prompt_template")


class Document(Base):
    __tablename__ = "documents"

    uid = Column(String(ID_LENGTH), primary_key=True, nullable=False)
    version = Column(String(TEXT_LENGTH), primary_key=True, nullable=False, default="")
    name = Column(String(TEXT_LENGTH), nullable=False)
    description = Column(String(TEXT_LENGTH), nullable=True, default="")
    # data_source_name = Column(
    #     String(TEXT_LENGTH), sqlalchemy.ForeignKey("data_sources.name"), nullable=False
    # )
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    spec = Column(MutableDict.as_mutable(JSON), nullable=True)
    Label = make_label(__tablename__)
    labels = relationship(Label, cascade="all, delete-orphan")
    path = Column(String(TEXT_LENGTH), nullable=True)
    project_id = Column(String(ID_LENGTH), ForeignKey("projects.uid"), nullable=False)
    # relationships:

    # many-to-one relationship with the 'Project' table
    project = relationship("Project", back_populates="documents")
    # many-to-many relationship with the 'ingestions' table
    ingestions = relationship("DataSource", secondary=ingestions, back_populates="document")


class Workflow(Base):
    __tablename__ = "workflows"

    uid = Column(String(ID_LENGTH), primary_key=True, nullable=False)
    version = Column(String(TEXT_LENGTH), primary_key=True, nullable=False, default="")
    name = Column(String(TEXT_LENGTH), nullable=False)
    description = Column(String(TEXT_LENGTH), nullable=True, default="")
    owner_id = Column(String(ID_LENGTH), ForeignKey("users.name"), nullable=False)
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    spec = Column(MutableDict.as_mutable(JSON), nullable=True)
    Label = make_label(__tablename__)
    labels = relationship(Label, cascade="all, delete-orphan")
    workflow_type = Column(String(TEXT_LENGTH), nullable=True)
    workflow_function = Column(String(TEXT_LENGTH), nullable=True)
    project_id = Column(String(ID_LENGTH), ForeignKey("projects.uid"), nullable=False)

    # Relationships:

    # many-to-one relationship with the 'Project' table
    project = relationship("Project", back_populates="workflows")
    # one-to-many relationship with the 'ChatSession' table
    chat_sessions = relationship("ChatSession", back_populates="workflow")


class Session(Base):
    __tablename__ = "chat_sessions"

    uid = Column(String(ID_LENGTH), primary_key=True, nullable=False)
    version = Column(String(TEXT_LENGTH), primary_key=True, nullable=False, default="")
    name = Column(String(TEXT_LENGTH), primary_key=True, nullable=False)
    description = Column(String(TEXT_LENGTH), nullable=True, default="")
    username = Column(String(TEXT_LENGTH), sqlalchemy.ForeignKey("users.name"), nullable=False)
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    spec = Column(MutableDict.as_mutable(JSON), nullable=True)
    Label = make_label(__tablename__)
    labels = relationship(Label, cascade="all, delete-orphan")
    workflow_id = Column(String(ID_LENGTH), ForeignKey("workflows.uid"), nullable=False)
    user_id = Column(String(ID_LENGTH), ForeignKey("users.uid"), nullable=False)

    # Relationships:

    # many-to-one relationship with the 'Workflow' table
    workflow = relationship("Workflow", back_populates="chat_sessions")
    # many-to-one relationship with the 'User' table
    user = relationship("User", back_populates="chat_sessions")

#
# prompt_model = Table(
#     "prompt_model",
#     Base.metadata,
#     Column("prompt_uid", String(ID_LENGTH), ForeignKey("prompts.uid")),
#     Column("prompt_version", String(TEXT_LENGTH), ForeignKey("prompts.version")),
#     Column("model_uid", String(ID_LENGTH), ForeignKey("models.uid")),
#     Column("model_version", String(TEXT_LENGTH), ForeignKey("models.version")),
#     Column("generation_config", JSON),
# )


