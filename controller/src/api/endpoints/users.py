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
from controller.src.schemas import User

router = APIRouter()


@router.post("/users/")
def create_user(
    user: User,
    session=Depends(get_db),
):
    return client.create_user(user, session=session)


@router.get("/users/{user_name}")
def get_user(
    user_name: str,
    session=Depends(get_db),
):
    return client.get_user(user_name, session=session)


@router.delete("/users/{user_name}")
def delete_user(
    user_name: str,
    session=Depends(get_db),
):
    return client.delete_user(user_name, session=session)


@router.patch("/users/{user_name}")
def update_user(
    user: User,
    user_name: str,
    session=Depends(get_db),
):
    return client.update_user(user, user_name, session=session)


@router.get("/users/")
def list_users(
    version: str = None,
    owner_id: str = None,
    project_id: str = None,
    policy: str = None,
    is_admin: bool = None,
    labels_match: list = None,
    output_mode: str = "details",
    session=Depends(get_db),
):
    return client.list_users(
        version=version,
        owner_id=owner_id,
        project_id=project_id,
        policy=policy,
        is_admin=is_admin,
        labels_match=labels_match,
        output_mode=output_mode,
        session=session,
    )
