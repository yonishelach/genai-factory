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

from abc import ABC, abstractmethod

from controller.src import model
import controller.src.schemas as schemas


class Client(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def _process_output(
            items, obj_class, mode: schemas.OutputMode = schemas.OutputMode.Details
    ):
        if mode == schemas.OutputMode.Names:
            return [item.name for item in items]
        items = [obj_class.from_orm_object(item) for item in items]
        if mode == model.OutputMode.Details:
            return items
        short = mode == model.OutputMode.Short
        return [item.to_dict(short=short) for item in items]

    @abstractmethod
    def create_tables(self, drop_old: bool = False, names: list = None):
        pass

    @abstractmethod
    def create_project(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_project(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_project(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_project(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_projects(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_datasource(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_datasource(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_datasource(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_datasource(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_datasources(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_dataset(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_dataset(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_dataset(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_dataset(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_datasets(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_model(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_model(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_model(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_model(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_models(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_prompt_template(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_prompt_template(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_prompt_template(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_prompt_template(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_prompt_templates(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_document(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_document(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_document(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_document(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_documents(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_workflow(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_workflow(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_workflow(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_workflow(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_workflows(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_user(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_user(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_user(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_user(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_users(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_session(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_session(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_session(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_session(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_sessions(self, *args, **kwargs):
        pass
