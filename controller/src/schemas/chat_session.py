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

from typing import List, Optional, Tuple

from pydantic import BaseModel

from controller.src.schemas.base import BaseWithMetadata


class QueryItem(BaseModel):
    question: str
    session_id: Optional[str] = None
    filter: Optional[List[Tuple[str, str]]] = None
    data_source: Optional[str] = None


class Message(BaseModel):
    role: str
    body: str
    extra_data: Optional[dict] = None
    sources: Optional[List[str]] = None
    human_feedback: Optional[str] = None


class ChatSession(BaseWithMetadata):
    project_id: str
    workflow_id: str
    user_id: str
    history: List[Message] = []
