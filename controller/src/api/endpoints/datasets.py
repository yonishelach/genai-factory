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
from controller.src.schemas import Dataset

router = APIRouter()


@router.post("/datasets/")
def create_data_source(
    dataset: Dataset,
    session=Depends(get_db),
):
    return client.create_dataset(dataset, session=session)


@router.get("/datasets/{dataset_name}")
def get_data_source(
    dataset_name: str,
    session=Depends(get_db),
):
    return client.get_data_source(dataset_name, session=session)


@router.delete("/datasets/{dataset_name}")
def delete_data_source(
    dataset_name: str,
    session=Depends(get_db),
):
    return client.delete_data_source(dataset_name, session=session)


@router.patch("/datasets/{dataset_name}")
def update_data_source(
    dataset: Dataset,
    dataset_name: str,
    session=Depends(get_db),
):
    return client.update_data_source(dataset, dataset_name, session=session)


@router.get("/datasets/")
def list_datasets(
    session=Depends(get_db),
    version: str = None,
    owner_id: str = None,
    project_id: str = None,
    task: str = None,
    labels_match: list = None,
    output_mode: str = "details",
):
    return client.list_datasets(
        version=version,
        owner_id=owner_id,
        project_id=project_id,
        task=task,
        labels_match=labels_match,
        output_mode=output_mode,
        session=session,
    )
