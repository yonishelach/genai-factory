from controller.src.db_clients.base import Client
from typing import Union
import sqlalchemy
import uuid
from sqlalchemy.orm import sessionmaker
from controller.src.db.sql import Base
from controller.src.model import ApiResponse
from controller.src.config import logger
import controller.src.schemas as schemas
import controller.src.db.sql as sqldb
from controller.src.config import config


class SQLClient(Client):
    def __init__(self, db_url: str, verbose: bool = False):
        self.db_url = db_url
        self.engine = sqlalchemy.create_engine(
            db_url, echo=verbose, connect_args={"check_same_thread": False}
        )
        self._session_maker = sessionmaker(bind=self.engine)
        self._local_maker = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def get_db_session(self, session: sqlalchemy.orm.Session = None):
        return session or self._session_maker()

    def get_local_session(self):
        return self._local_maker()

    def create_tables(self, drop_old: bool = False, names: list = None):
        tables = None
        if names:
            tables = [Base.metadata.tables[name] for name in names]
        if drop_old:
            Base.metadata.drop_all(self.engine, tables=tables)
        Base.metadata.create_all(self.engine, tables=tables, checkfirst=True)
        return ApiResponse(success=True)

    def _create(self, session: sqlalchemy.orm.Session, db_class, obj):
        session = self.get_db_session(session)
        try:
            uid = uuid.uuid4().hex
            db_object = obj.to_orm_object(db_class, uuid=uid)
            session.add(db_object)
            session.commit()
            return ApiResponse(
                success=True, data=obj.__class__.from_orm_object(db_object)
            )
        except sqlalchemy.exc.IntegrityError:
            return ApiResponse(
                success=False, error=f"{db_class} {obj.name} already exists"
            )

    def _get(self, session: sqlalchemy.orm.Session, db_class, api_class, **kwargs):
        session = self.get_db_session(session)
        obj = session.query(db_class).filter_by(**kwargs).one_or_none()
        if obj is None:
            return ApiResponse(
                success=False, error=f"{db_class} object ({kwargs}) not found"
            )
        return ApiResponse(success=True, data=api_class.from_orm_object(obj))

    def _get_id(self, session: sqlalchemy.orm.Session, name: str, db_class):
        session = self.get_db_session(session)
        obj = session.query(db_class).filter_by(name=name).one_or_none()
        return obj.id if obj else None

    def _delete(self, session: sqlalchemy.orm.Session, db_class, **kwargs):
        session = self.get_db_session(session)
        query = session.query(db_class).filter_by(**kwargs)
        for obj in query:
            session.delete(obj)
        session.commit()
        return ApiResponse(success=True)

    def _update(self, session: sqlalchemy.orm.Session, db_class, api_object, **kwargs):
        session = self.get_db_session(session)
        obj = session.query(db_class).filter_by(**kwargs).one_or_none()
        if obj:
            api_object.merge_into_orm_object(obj)
            session.add(obj)
            session.commit()
            return ApiResponse(
                success=True, data=api_object.__class__.from_orm_object(obj)
            )
        else:
            return ApiResponse(
                success=False, error=f"{db_class} object ({kwargs}) not found"
            )

    def _list(self, session: sqlalchemy.orm.Session, db_class, api_class, output_mode, labels_match, **kwargs):
        session = self.get_db_session(session)
        query = session.query(db_class).filter_by(**kwargs)
        # TODO: Implement labels_match
        if labels_match:
            logger.debug(f"Filtering projects by labels is not supported yet")
            # query = self._filter_labels(query, sqldb.Project, labels_match)
            pass
        data = self._process_output(query.all(), api_class, output_mode)
        return ApiResponse(success=True, data=data)

    def create_project(self, project: schemas.Project, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Creating project {project.name}")
        return self._create(session, sqldb.Project, project)

    def get_project(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Getting project {name}")
        return self._get(session, sqldb.Project, schemas.Project, name=name)

    def delete_project(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Deleting project {name}")
        return self._delete(session, sqldb.Project, name=name)

    def update_project(self, project: schemas.Project, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Updating project {project.name}")
        return self._update(session, sqldb.Project, project, name=project.name)

    def list_projects(
        self,
        version: str = None,
        owner_id: str = None,
        labels_match: Union[str, list] = None,
        output_mode: schemas.OutputMode = schemas.OutputMode.Details,
        session: sqlalchemy.orm.Session = None,
    ):
        logger.debug(
            f"Getting projects: version={version}, owner_id={owner_id}, mode={output_mode}"
        )
        return self._list(
            session=session,
            db_class=sqldb.Project,
            api_class=schemas.Project,
            output_mode=output_mode,
            version=version,
            owner_id=owner_id,
            labels_match=labels_match,

        )

    def create_data_source(self, data_source: schemas.DataSource, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Creating data source {data_source.name}")
        return self._create(session, sqldb.DataSource, data_source)

    def get_data_source(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Getting data source {name}")
        return self._get(session, sqldb.DataSource, schemas.DataSource, name=name)

    def delete_data_source(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Deleting data source {name}")
        return self._delete(session, sqldb.DataSource, name=name)

    def update_data_source(self, data_source: schemas.DataSource, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Updating data source {data_source.name}")
        return self._update(session, sqldb.DataSource, data_source, name=data_source.name)

    def list_data_sources(
        self,
        version: str = None,
        owner_id: str = None,
        project_id: str = None,
        data_source_type: str = None,
        labels_match: Union[str, list] = None,
        output_mode: schemas.OutputMode = schemas.OutputMode.Details,
        session: sqlalchemy.orm.Session = None,
    ):
        logger.debug(
            f"Getting data sources: version={version}, owner_id={owner_id}, project_id={project_id} type={data_source_type} mode={output_mode}"
        )
        return self._list(
            session=session,
            db_class=sqldb.DataSource,
            api_class=schemas.DataSource,
            output_mode=output_mode,
            version=version,
            owner_id=owner_id,
            project_id=project_id,
            data_source_type=data_source_type,
            labels_match=labels_match,
        )

    def create_dataset(self, dataset: schemas.Dataset, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Creating dataset {dataset.name}")
        return self._create(session, sqldb.Dataset, dataset)

    def get_dataset(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Getting dataset {name}")
        return self._get(session, sqldb.Dataset, schemas.Dataset, name=name)

    def delete_dataset(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Deleting dataset {name}")
        return self._delete(session, sqldb.Dataset, name=name)

    def update_dataset(self, dataset: schemas.Dataset, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Updating dataset {dataset.name}")
        return self._update(session, sqldb.Dataset, dataset, name=dataset.name)

    def list_datasets(
        self,
        version: str = None,
        owner_id: str = None,
        project_id: str = None,
        task: str = None,
        labels_match: Union[str, list] = None,
        output_mode: schemas.OutputMode = schemas.OutputMode.Details,
        session: sqlalchemy.orm.Session = None,
    ):
        logger.debug(
            f"Getting datasets: version={version}, owner_id={owner_id}, project_id={project_id}, task={task} mode={output_mode}"
        )
        return self._list(
            session=session,
            db_class=sqldb.Dataset,
            api_class=schemas.Dataset,
            output_mode=output_mode,
            version=version,
            owner_id=owner_id,
            project_id=project_id,
            task=task,
            labels_match=labels_match,
        )

    def create_model(self, model: schemas.Model, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Creating model {model.name}")
        return self._create(session, sqldb.Model, model)

    def get_model(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Getting model {name}")
        return self._get(session, sqldb.Model, schemas.Model, name=name)

    def delete_model(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Deleting model {name}")
        return self._delete(session, sqldb.Model, name=name)

    def update_model(self, model: schemas.Model, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Updating model {model.name}")
        return self._update(session, sqldb.Model, model, name=model.name)

    def list_models(
        self,
        version: str = None,
        owner_id: str = None,
        project_id: str = None,
        model_type: str = None,
        task: str = None,
        labels_match: Union[str, list] = None,
        output_mode: schemas.OutputMode = schemas.OutputMode.Details,
        session: sqlalchemy.orm.Session = None,
    ):
        logger.debug(
            f"Getting models: version={version}, owner_id={owner_id}, project_id={project_id}, model_type={model_type}, task={task} mode={output_mode}"
        )
        return self._list(
            session=session,
            db_class=sqldb.Model,
            api_class=schemas.Model,
            output_mode=output_mode,
            version=version,
            owner_id=owner_id,
            project_id=project_id,
            model_type=model_type,
            task=task,
            labels_match=labels_match,
        )

    def create_prompt_template(self, prompt_template: schemas.PromptTemplate, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Creating prompt template {prompt_template.name}")
        return self._create(session, sqldb.PromptTemplate, prompt_template)

    def get_prompt_template(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Getting prompt template {name}")
        return self._get(session, sqldb.PromptTemplate, schemas.PromptTemplate, name=name)

    def delete_prompt_template(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Deleting prompt template {name}")
        return self._delete(session, sqldb.PromptTemplate, name=name)

    def update_prompt_template(self, prompt_template: schemas.PromptTemplate, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Updating prompt template {prompt_template.name}")
        return self._update(session, sqldb.PromptTemplate, prompt_template, name=prompt_template.name)

    def list_prompt_templates(
        self,
        version: str = None,
        owner_id: str = None,
        project_id: str = None,
        model_id: str = None,
        model_version: str = None,
        labels_match: Union[str, list] = None,
        output_mode: schemas.OutputMode = schemas.OutputMode.Details,
        session: sqlalchemy.orm.Session = None,
    ):
        logger.debug(
            f"Getting prompt templates: version={version}, owner_id={owner_id}, project_id={project_id}, model_id={model_id}, mode={output_mode}"
        )
        return self._list(
            session=session,
            db_class=sqldb.PromptTemplate,
            api_class=schemas.PromptTemplate,
            output_mode=output_mode,
            version=version,
            owner_id=owner_id,
            project_id=project_id,
            model_id=model_id,
            model_version=model_version,
            labels_match=labels_match,
        )

    def create_document(self, document: schemas.Document, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Creating document {document.name}")
        return self._create(session, sqldb.Document, document)

    def get_document(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Getting document {name}")
        return self._get(session, sqldb.Document, schemas.Document, name=name)

    def delete_document(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Deleting document {name}")
        return self._delete(session, sqldb.Document, name=name)

    def update_document(self, document: schemas.Document, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Updating document {document.name}")
        return self._update(session, sqldb.Document, document, name=document.name)

    def list_documents(
        self,
        version: str = None,
        owner_id: str = None,
        project_id: str = None,
        labels_match: Union[str, list] = None,
        output_mode: schemas.OutputMode = schemas.OutputMode.Details,
        session: sqlalchemy.orm.Session = None,
    ):
        logger.debug(
            f"Getting documents: version={version}, owner_id={owner_id}, project_id={project_id}, mode={output_mode}"
        )
        return self._list(
            session=session,
            db_class=sqldb.Document,
            api_class=schemas.Document,
            output_mode=output_mode,
            version=version,
            owner_id=owner_id,
            project_id=project_id,
            labels_match=labels_match,
        )

    def create_workflow(self, workflow: schemas.Workflow, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Creating workflow {workflow.name}")
        return self._create(session, sqldb.Workflow, workflow)

    def get_workflow(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Getting workflow {name}")
        return self._get(session, sqldb.Workflow, schemas.Workflow, name=name)

    def delete_workflow(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Deleting workflow {name}")
        return self._delete(session, sqldb.Workflow, name=name)

    def update_workflow(self, workflow: schemas.Workflow, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Updating workflow {workflow.name}")
        return self._update(session, sqldb.Workflow, workflow, name=workflow.name)

    def list_workflows(
        self,
        version: str = None,
        owner_id: str = None,
        project_id: str = None,
        workflow_type: str = None,
        labels_match: Union[str, list] = None,
        output_mode: schemas.OutputMode = schemas.OutputMode.Details,
        session: sqlalchemy.orm.Session = None,
    ):
        logger.debug(
            f"Getting workflows: version={version}, owner_id={owner_id}, project_id={project_id}, workflow_type={workflow_type}, mode={output_mode}"
        )
        return self._list(
            session=session,
            db_class=sqldb.Workflow,
            api_class=schemas.Workflow,
            output_mode=output_mode,
            version=version,
            owner_id=owner_id,
            project_id=project_id,
            workflow_type=workflow_type,
            labels_match=labels_match,
        )

    def create_user(self, user: schemas.User, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Creating user {user.name}")
        return self._create(session, sqldb.User, user)

    def get_user(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Getting user {name}")
        return self._get(session, sqldb.User, schemas.User, name=name)

    def delete_user(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Deleting user {name}")
        return self._delete(session, sqldb.User, name=name)

    def update_user(self, user: schemas.User, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Updating user {user.name}")
        return self._update(session, sqldb.User, user, name=user.name)

    def list_users(
        self,
        version: str = None,
        owner_id: str = None,
        project_id: str = None,
        policy: str = None,
        is_admin: bool = None,
        labels_match: Union[str, list] = None,
        output_mode: schemas.OutputMode = schemas.OutputMode.Details,
        session: sqlalchemy.orm.Session = None,
    ):
        logger.debug(
            f"Getting users: version={version}, owner_id={owner_id}, project_id={project_id}, policy={policy} mode={output_mode}"
        )
        return self._list(
            session=session,
            db_class=sqldb.User,
            api_class=schemas.User,
            output_mode=output_mode,
            version=version,
            owner_id=owner_id,
            project_id=project_id,
            is_admin=is_admin,
            policy=policy,
            labels_match=labels_match,
        )

    def create_session(self, chat_session: schemas.ChatSession, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Creating session {chat_session.name}")
        return self._create(session, sqldb.ChatSession, chat_session)

    def get_session(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Getting session {name}")
        return self._get(session, sqldb.ChatSession, schemas.ChatSession, name=name)

    def delete_session(self, name: str, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Deleting session {name}")
        return self._delete(session, sqldb.ChatSession, name=name)

    def update_session(self, chat_session: schemas.ChatSession, session: sqlalchemy.orm.Session = None):
        logger.debug(f"Updating session {chat_session.name}")
        return self._update(session, sqldb.ChatSession, session, name=chat_session.name)

    def list_sessions(
        self,
        version: str = None,
        owner_id: str = None,
        project_id: str = None,
        labels_match: Union[str, list] = None,
        output_mode: schemas.OutputMode = schemas.OutputMode.Details,
        session: sqlalchemy.orm.Session = None,
    ):
        logger.debug(
            f"Getting sessions: version={version}, owner_id={owner_id}, project_id={project_id}, mode={output_mode}"
        )
        return self._list(
            session=session,
            db_class=sqldb.ChatSession,
            api_class=schemas.ChatSession,
            output_mode=output_mode,
            version=version,
            owner_id=owner_id,
            project_id=project_id,
            labels_match=labels_match,
        )


client = SQLClient(config.sql_connection_str, verbose=config.verbose)
