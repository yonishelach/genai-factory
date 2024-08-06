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
from controller.src.schemas import Document

router = APIRouter()


@router.post("/documents/")
def create_document(
    document: Document,
    session=Depends(get_db),
):
    return client.create_document(document, session=session)


@router.get("/documents/{document_name}")
def get_document(
    document_name: str,
    session=Depends(get_db),
):
    return client.get_document(document_name, session=session)


@router.delete("/documents/{document_name}")
def delete_document(
    document_name: str,
    session=Depends(get_db),
):
    return client.delete_document(document_name, session=session)


@router.patch("/documents/{document_name}")
def update_document(
    document: Document,
    document_name: str,
    session=Depends(get_db),
):
    return client.update_document(document, document_name, session=session)


@router.get("/documents/")
def list_documents(
    version: str = None,
    owner_id: str = None,
    project_id: str = None,
    labels_match: list = None,
    output_mode: str = "details",
    session=Depends(get_db),
):
    return client.list_documents(
        version=version,
        owner_id=owner_id,
        project_id=project_id,
        labels_match=labels_match,
        output_mode=output_mode,
        session=session,
    )
