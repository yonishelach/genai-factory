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
from controller.src.schemas import PromptTemplate
from controller.src.api.utils import get_db
from controller.src.db_clients import client


router = APIRouter()


@router.post("/prompt-templates/")
def create_prompt_template(
    prompt_template: PromptTemplate,
    session=Depends(get_db),
):
    return client.create_prompt_template(prompt_template, session=session)


@router.get("/prompt-templates/{prompt_template_name}")
def get_prompt_template(
    prompt_template_name: str,
    session=Depends(get_db),
):
    return client.get_prompt_template(prompt_template_name, session=session)


@router.delete("/prompt-templates/{prompt_template_name}")
def delete_prompt_template(
    prompt_template_name: str,
    session=Depends(get_db),
):
    return client.delete_prompt_template(prompt_template_name, session=session)


@router.patch("/prompt-templates/{prompt_template_name}")
def update_prompt_template(
    prompt_template: PromptTemplate,
    prompt_template_name: str,
    session=Depends(get_db),
):
    return client.update_prompt_template(prompt_template, prompt_template_name, session=session)


@router.get("/prompt-templates/")
def list_prompt_templates(
    version: str = None,
    owner_id: str = None,
    project_id: str = None,
    model_id: str = None,
    model_version: str = None,
    labels_match: list = None,
    output_mode: str = "details",
    session=Depends(get_db),
):
    return client.list_prompt_templates(
        version=version,
        owner_id=owner_id,
        project_id=project_id,
        model_id=model_id,
        model_version=model_version,
        labels_match=labels_match,
        output_mode=output_mode,
        session=session,
    )
