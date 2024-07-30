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
from controller.src.schemas import DataSource
from controller.src.api.utils import get_db
from controller.src.db_clients import client


router = APIRouter()


@router.post("/data-sources/")
def create_data_source(
    data_source: DataSource,
    session=Depends(get_db),
):
    return client.create_dataset(data_source, session=session)


@router.get("/data-sources/{data_source_name}")
def get_data_source(
    data_source_name: str,
    session=Depends(get_db),
):
    return client.get_data_source(data_source_name, session=session)


@router.delete("/data-sources/{data_source_name}")
def delete_data_source(
    data_source_name: str,
    session=Depends(get_db),
):
    return client.delete_data_source(data_source_name, session=session)


@router.patch("/data-sources/{data_source_name}")
def update_data_source(
    data_source: DataSource,
    data_source_name: str,
    session=Depends(get_db),
):
    return client.update_data_source(data_source, data_source_name, session=session)


@router.get("/data-sources/")
def list_data_sources(
    session=Depends(get_db),
    version: str = None,
    owner_id: str = None,
    project_id: str = None,
    data_source_type: str = None,
    labels_match: list = None,
    output_mode: str = "details",
):
    return client.list_data_sources(
        version=version,
        owner_id=owner_id,
        project_id=project_id,
        data_source_type=data_source_type,
        labels_match=labels_match,
        output_mode=output_mode,
        session=session,
    )
