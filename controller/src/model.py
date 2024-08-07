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

from datetime import datetime
from enum import Enum
from http.client import HTTPException
from typing import Dict, List, Optional, Tuple, Union

import yaml
from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Union[list, BaseModel, dict]] = None
    error: Optional[str] = None

    def with_raise(self, format=None) -> "ApiResponse":
        if not self.success:
            format = format or "API call failed: %s"
            raise ValueError(format % self.error)
        return self

    def with_raise_http(self, format=None) -> "ApiResponse":
        if not self.success:
            format = format or "API call failed: %s"
            raise HTTPException(status_code=400, detail=format % self.error)
        return self


class ChatRole(str, Enum):
    Human = "Human"
    AI = "AI"
    System = "System"
    User = "User"  # for co-pilot user (vs Human?)
    Agent = "Agent"  # for co-pilot agent


class Message(BaseModel):
    role: ChatRole
    body: str
    extra_data: Optional[dict] = None
    sources: Optional[List[dict]] = None
    human_feedback: Optional[dict] = None


class Conversation(BaseModel):
    messages: list[Message] = []
    saved_index: int = 0

    def __str__(self):
        return "\n".join([f"{m.role}: {m.body}" for m in self.messages])

    def add_message(self, role, content, sources=None):
        self.messages.append(Message(role=role, content=content, sources=sources))

    def to_list(self):
        return self.dict()["messages"]
        # return self.model_dump(mode="json")["messages"]

    def to_dict(self):
        return self.dict()["messages"]
        # return self.model_dump(mode="json")["messages"]

    @classmethod
    def from_list(cls, data: list):
        return cls.parse_obj({"messages": data or []})
        # return cls.model_validate({"messages": data or []})


class QueryItem(BaseModel):
    question: str
    session_id: Optional[str] = None
    filter: Optional[List[Tuple[str, str]]] = None
    collection: Optional[str] = None


class DataSourceType(str, Enum):
    RELATIONAL = "relational"
    VECTOR = "vector"
    GRAPH = "graph"
    KEY_VALUE = "key-value"
    COLUMN_FAMILY = "column-family"
    STORAGE = "storage"
    OTHER = "other"


class ModelType(str, Enum):
    model = "model"
    adapter = "adapter"


class Ingestion(BaseModel):
    data_source_id: str
    data_source_version: str
    extra_data: Optional[dict] = None


class WorkflowType(str, Enum):
    RELATIONAL = "relational"
    VECTOR = "vector"
    GRAPH = "graph"
    KEY_VALUE = "key-value"
    COLUMN_FAMILY = "column-family"
    STORAGE = "storage"
    OTHER = "other"


class OutputMode(str, Enum):
    Names = "names"
    Short = "short"
    Dict = "dict"
    Details = "details"


metadata_fields = [
    "uid",
    "name",
    "description",
    "labels",
    "owner_id",
    "created",
    "updated",
    "version",
]


class Base(BaseModel):
    _extra_fields = []
    _top_level_fields = []

    class Config:
        orm_mode = True

    def to_dict(
        self, drop_none=True, short=False, drop_metadata=False, to_datestr=False
    ):
        struct = self.dict()
        # struct = self.model_dump(mode="json")  # pydantic v2
        new_struct = {}
        for k, v in struct.items():
            if (
                (drop_none and v is None)
                or (short and k in self._extra_fields)
                or (drop_metadata and k in metadata_fields)
            ):
                continue
            if to_datestr and isinstance(v, datetime):
                v = v.isoformat()
            elif short and isinstance(v, datetime):
                v = v.strftime("%Y-%m-%d %H:%M")
            if hasattr(v, "to_dict"):
                v = v.to_dict()
            new_struct[k] = v
        return new_struct

    @classmethod
    def from_dict(cls, data: dict):
        if isinstance(data, cls):
            return data
        return cls.parse_obj(data)
        # return cls.model_validate(data)  # pydantic v2

    @classmethod
    def from_orm_object(cls, obj):
        object_dict = {}
        for field in obj.__table__.columns:
            object_dict[field.name] = getattr(obj, field.name)
        spec = object_dict.pop("spec", {})
        object_dict.update(spec)
        if obj.labels:
            object_dict["labels"] = {label.name: label.value for label in obj.labels}
        return cls.from_dict(object_dict)

    def merge_into_orm_object(self, orm_object):
        struct = self.to_dict(drop_none=True)
        spec = orm_object.spec or {}
        labels = struct.pop("labels", None)
        for k, v in struct.items():
            if k in (metadata_fields + self._top_level_fields) and k not in [
                "created",
                "updated",
            ]:
                setattr(orm_object, k, v)
            if k not in [metadata_fields + self._top_level_fields]:
                spec[k] = v
        orm_object.spec = spec

        if labels:
            old = {label.name: label for label in orm_object.labels}
            orm_object.labels.clear()
            for name, value in labels.items():
                if name in old:
                    if value is not None:  # None means delete
                        old[name].value = value
                        orm_object.labels.append(old[name])
                else:
                    orm_object.labels.append(
                        orm_object.Label(name=name, value=value, parent=orm_object.name)
                    )

        return orm_object

    def to_orm_object(self, obj_class):
        # Getting all fields from the object into a dictionary
        struct = self.to_dict(drop_none=False, short=False)

        # Getting only the fields that are in metadata_fields and _top_level_fields without timestamps
        obj_dict = {
            k: v
            for k, v in struct.items()
            if k in (metadata_fields + self._top_level_fields)
            and k not in ["created", "updated"]
        }
        # Getting all fields that are not in metadata_fields and _top_level_fields into spec
        obj_dict["spec"] = {
            k: v
            for k, v in struct.items()
            if k not in metadata_fields + self._top_level_fields
        }
        # Popping labels from the dictionary
        labels = obj_dict.pop("labels", None)
        obj = obj_class(**obj_dict)
        # Putting the labels back into the object
        if labels:
            obj.labels.clear()
            for name, value in labels.items():
                obj.labels.append(obj.Label(name=name, value=value, parent=obj.name))
        return obj

    def to_yaml(self, drop_none=True):
        return yaml.dump(self.to_dict(drop_none=drop_none))

    def __repr__(self):
        args = ", ".join(
            [f"{k}={v!r}" for k, v in self.to_dict(short=True, to_datestr=True).items()]
        )
        return f"{self.__class__.__name__}({args})"

    def __str__(self):
        return str(self.to_dict(to_datestr=True))


class BaseWithMetadata(Base):
    name: str
    description: Optional[str] = None
    labels: Optional[Dict[str, Union[str, None]]] = None
    created: Optional[Union[str, datetime]] = None
    updated: Optional[Union[str, datetime]] = None


class BaseWithVerMetadata(BaseWithMetadata):
    version: Optional[str] = ""


class User(BaseWithMetadata):
    _extra_fields = ["policy", "features"]
    _top_level_fields = ["email", "full_name"]

    email: str
    full_name: Optional[str] = None
    features: Optional[dict[str, str]] = None
    policy: Optional[dict[str, str]] = None
    is_admin: Optional[bool] = False


class Project(BaseWithVerMetadata):
    pass


class DataSource(BaseWithVerMetadata):
    # _extra_fields = ["project_id"]
    _top_level_fields = ["data_source_type"]

    project_id: str
    data_source_type: DataSourceType
    database_kwargs: Optional[dict[str, str]] = None


class Dataset(BaseWithVerMetadata):
    # _extra_fields = ["project_id"]
    _top_level_fields = ["task"]

    project_id: str
    task: str
    sources: Optional[List[str]] = None
    path: str
    producer: Optional[str] = None


class Model(BaseWithVerMetadata):
    # _extra_fields = ["project_id", "path", "producer", "deployment"]
    _extra_fields = ["path", "producer", "deployment"]
    _top_level_fields = ["model_type", "base_model", "task"]

    project_id: str
    model_type: ModelType
    base_model: str
    task: Optional[str] = None
    path: Optional[str] = None
    producer: Optional[str] = None
    deployment: Optional[str] = None


class PromptTemplate(BaseWithVerMetadata):
    # _extra_fields = ["project_id", "arguments"]
    _extra_fields = ["arguments"]
    _top_level_fields = ["text"]

    project_id: str
    text: str
    arguments: Optional[List[str]] = None


class Document(BaseWithVerMetadata):
    # _extra_fields = ["project_id", "origin"]
    _extra_fields = ["origin"]
    _top_level_fields = ["path"]
    project_id: str
    path: str
    origin: Optional[str] = None
    ingestions: Optional[List[Ingestion]] = None


class Workflow(BaseWithVerMetadata):
    # _extra_fields = ["project_id"]
    _top_level_fields = ["workflow_type", "workflow_function"]

    project_id: str
    workflow_type: WorkflowType
    workflow_function: Optional[str] = None
    configuration: Optional[str] = None
    graph: Optional[dict] = None
    deployment: Optional[str] = None


class ChatSession(BaseWithMetadata):
    _extra_fields = ["history"]

    workflow_id: str
    history: Optional[List[Message]] = []

    def to_conversation(self):
        return Conversation.from_list(self.history)
