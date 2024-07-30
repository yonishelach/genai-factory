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

import json

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from controller.src.api.utils import _send_to_application, get_auth_user
from controller.src.schemas import QueryItem

router = APIRouter()


@router.post("/pipeline/{name}/run")
def run_pipeline(
    request: Request, item: QueryItem, name: str, auth=Depends(get_auth_user)
):
    """This is the query command"""
    return _send_to_application(
        path=f"pipeline/{name}/run",
        method="POST",
        request=request,
        auth=auth,
    )


@router.post("/collections/{collection}/{loader}/ingest")
def ingest(
    collection, path, loader, metadata, version, from_file, auth=Depends(get_auth_user)
):
    """Ingest documents into the vector database"""
    params = {
        "path": path,
        "from_file": from_file,
        "version": version,
    }
    if metadata is not None:
        params["metadata"] = json.dumps(metadata)

    return _send_to_application(
        path=f"collections/{collection}/{loader}/ingest",
        method="POST",
        params=params,
        auth=auth,
    )
