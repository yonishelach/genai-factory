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

from fastapi import APIRouter, Depends

from controller.src.api.utils import get_db
from controller.src.db_clients import client
from controller.src.schemas import Model

router = APIRouter()


@router.post("/models/")
def create_model(
    model: Model,
    session=Depends(get_db),
):
    return client.create_model(model, session=session)


@router.get("/models/{model_name}")
def get_model(
    model_name: str,
    session=Depends(get_db),
):
    return client.get_model(model_name, session=session)


@router.delete("/models/{model_name}")
def delete_model(
    model_name: str,
    session=Depends(get_db),
):
    return client.delete_model(model_name, session=session)


@router.patch("/models/{model_name}")
def update_model(
    model: Model,
    model_name: str,
    session=Depends(get_db),
):
    return client.update_model(model, model_name, session=session)


@router.get("/models/")
def list_models(
    version: str = None,
    owner_id: str = None,
    project_id: str = None,
    model_type: str = None,
    task: str = None,
    labels_match: list = None,
    output_mode: str = "details",
    session=Depends(get_db),
):
    return client.list_models(
        version=version,
        owner_id=owner_id,
        project_id=project_id,
        model_type=model_type,
        task=task,
        labels_match=labels_match,
        output_mode=output_mode,
        session=session,
    )
