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
from controller.src.schemas import Project

router = APIRouter()


@router.post("/projects/")
def create_project(
    project: Project,
    session=Depends(get_db),
):
    return client.create_project(project, session=session)


@router.get("/projects/{project_name}")
def get_project(
    project_name: str,
    session=Depends(get_db),
):
    return client.get_project(project_name, session=session)


@router.delete("/projects/{project_name}")
def delete_project(
    project_name: str,
    session=Depends(get_db),
):
    return client.delete_project(project_name, session=session)


@router.patch("/projects/{project_name}")
def update_project(
    project: Project,
    project_name: str,
    session=Depends(get_db),
):
    return client.update_project(project, project_name, session=session)


@router.get("/projects/")
def list_projects(
    session=Depends(get_db),
    version: str = None,
    owner_id: str = None,
    labels_match: list = None,
    output_mode: str = "details",
):
    return client.list_projects(
        version=version,
        owner_id=owner_id,
        labels_match=labels_match,
        output_mode=output_mode,
        session=session,
    )
