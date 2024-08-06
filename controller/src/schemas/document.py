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

from typing import List, Optional

from pydantic import BaseModel

from controller.src.schemas.base import BaseWithMetadata


class Ingestion(BaseModel):
    data_source_id: str
    # data_source_version: str
    document_id: str
    # document_version: str
    extra_data: Optional[dict] = None


class Document(BaseWithMetadata):
    project_id: str
    path: str
    origin: Optional[str] = None
    ingestions: Optional[List[Ingestion]] = None
