import uuid, os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, DateTime, ForeignKey


engine = create_engine(os.getenv("DATABASE_URI"))

Base = declarative_base()

session = sessionmaker(bind=engine)()

class UserModel(Base):
    __tablename__ = "user_model"
    user_uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(80), nullable=False)
    email = Column(String(80), unique=True, nullable=False)
    password = Column(String(80), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __repr__(self):
        return f"<UserModel {self.user_uuid}>"

    @staticmethod
    def create_dummy_user():
        # create a dummy user
        dummy_username = "dummyUser"
        dummy_email = "dummyUser@dummy.com"
        dummy_pwd = "dummyHexPwd"

        # if user exists, raise an exception
        if UserModel.get_user_uuid_by_email(dummy_email):
            raise Exception("User already exists")

        model = UserModel(
            username=dummy_username, email=dummy_email, password=dummy_pwd
        )
        session.add(model)
        session.commit()
        return model.user_uuid

    @staticmethod
    def get_user_uuid_by_email(email):
        user = session.query(UserModel).filter_by(email=email).first()
        if user:
            return user.user_uuid
        else:
            return None

    @staticmethod
    def get_user_record_by_uuid(user_uuid):
        return session.query(UserModel).filter_by(user_uuid=user_uuid).first()


class MLModel(Base):
    __tablename__ = "ml_model"
    model_uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_uuid = Column(String(36), ForeignKey("user_model.user_uuid"), nullable=False)
    upload_datetime = Column(DateTime, nullable=False, default=datetime.now())
    model_name = Column(String(80), nullable=True)
    model_type = Column(String(80), nullable=True)
    s3_url = Column(String(200), unique=True, nullable=False)

    def __init__(self, user_uuid, model_name, model_type, s3_url):
        self.user_uuid = user_uuid
        self.model_name = model_name
        self.model_type = model_type
        self.s3_url = s3_url

    def __repr__(self):
        return f"<MLModel {self.model_uuid}>"

    @staticmethod
    def save_model_to_db(model_name, model_type, s3_url):
        dummy_user_uuid = UserModel.get_user_uuid_by_email("dummyUser@dummy.com")
        if dummy_user_uuid is None:
            raise Exception("User does not exist")

        model = MLModel(
            user_uuid=dummy_user_uuid,
            model_name=model_name,
            model_type=model_type,
            s3_url=s3_url,
        )
        session.add(model)
        session.commit()
        return model.model_uuid

    @staticmethod
    def get_record_by_uuid(model_uuid):
        return session.query(MLModel).filter_by(model_uuid=model_uuid).first()


class ModelRegistryModel(Base):
    __tablename__ = "model_registry_model"
    model_registry_uuid = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    model_uuid = Column(String(36), ForeignKey("ml_model.model_uuid"), nullable=False)
    model_version = Column(String(80), nullable=False)
    model_status = Column(String(80), nullable=False)
    model_endpoint = Column(String(200), nullable=False)

    def __repr__(self):
        return f"<ModelRegistry {self.model_registry_uuid}>"

    def __init__(self, model_uuid, model_version, model_status, model_endpoint):
        self.model_uuid = model_uuid
        self.model_version = model_version
        self.model_status = model_status
        self.model_endpoint = model_endpoint

    @staticmethod
    def register_model(model_uuid, model_version, model_status, model_endpoint):
        model = ModelRegistryModel(
            model_uuid=model_uuid,
            model_version=model_version,
            model_status=model_status,
            model_endpoint=model_endpoint,
        )
        session.add(model)
        session.commit()
        return model.model_registry_uuid

    @staticmethod
    def get_record_by_uuid(model_registry_uuid):
        return (
            session.query(ModelRegistryModel)
            .filter_by(model_registry_uuid=model_registry_uuid)
            .first()
        )

    @staticmethod
    def update_record_by_uuid(model_registry_uuid, **kwargs):
        record = (
            session.query(ModelRegistryModel)
            .filter_by(model_registry_uuid=model_registry_uuid)
            .first()
        )
        for key, value in kwargs.items():
            setattr(record, key, value)
        session.commit()
        return record.model_registry_uuid

    @staticmethod
    def delete_record_by_uuid(model_registry_uuid):
        record = (
            session.query(ModelRegistryModel)
            .filter_by(model_registry_uuid=model_registry_uuid)
            .first()
        )
        session.delete(record)
        session.commit()
        return record.model_registry_uuid


class InferenceModel(Base):
    __tablename__ = "inference_model"
    inference_uuid = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_uuid = Column(String(36), ForeignKey("user_model.user_uuid"), nullable=False)
    model_registry_uuid = Column(
        String(36),
        ForeignKey("model_registry_model.model_registry_uuid"),
        nullable=False,
    )
    inference_datetime = Column(DateTime, nullable=False, default=datetime.now())
    inference_status = Column(String(80), nullable=False)

    def __init__(
        self,
        user_uuid,
        model_registry_uuid,
        inference_status,
    ):
        self.user_uuid = user_uuid
        self.model_registry_uuid = model_registry_uuid
        self.inference_status = inference_status

    @staticmethod
    def save_inference_to_db(
        user_uuid,
        model_registry_uuid,
        inference_status,
    ):
        inference = InferenceModel(
            user_uuid=user_uuid,
            model_registry_uuid=model_registry_uuid,
            inference_status=inference_status,
        )
        session.add(inference)
        session.commit()
        return inference.inference_uuid

    @staticmethod
    def get_record_by_uuid(inference_uuid):
        return (
            session.query(InferenceModel)
            .filter_by(inference_uuid=inference_uuid)
            .first()
        )
    
    @staticmethod
    def get_record_by_model_registry_uuid(model_registry_uuid):
        return (
            session.query(InferenceModel)
            .filter_by(model_registry_uuid=model_registry_uuid)
            .first()
        )
    
    @staticmethod
    def delete_record_by_uuid(inference_uuid):
        record = (
            session.query(InferenceModel)
            .filter_by(inference_uuid=inference_uuid)
            .first()
        )
        session.delete(record)
        session.commit()
        return record.inference_uuid

    def __repr__(self):
        return f"<InferenceModel {self.inference_uuid}>"


class JobsModel(Base):
    __tablename__ = "jobs_model"
    job_uuid = Column(String(36), primary_key=True)
    user_uuid = Column(String(36), ForeignKey("user_model.user_uuid"), nullable=False)
    job_type = Column(String(80), nullable=False)
    job_datetime = Column(DateTime, nullable=False, default=datetime.now())
    job_status = Column(String(80), nullable=False)
    reference_uuid = Column(String(36), nullable=True)

    def __init__(self, job_uuid, user_uuid, job_type, job_status, reference_uuid):
        self.job_uuid = job_uuid
        self.user_uuid = user_uuid
        self.job_type = job_type
        self.job_status = job_status
        self.reference_uuid = reference_uuid

    @staticmethod
    def save_job_to_db(job_uuid, user_uuid, job_type, job_status, reference_uuid):
        job = JobsModel(
            job_uuid=job_uuid,
            user_uuid=user_uuid,
            job_type=job_type,
            job_status=job_status,
            reference_uuid=reference_uuid,
        )
        session.add(job)
        session.commit()
        return job.job_uuid

    @staticmethod
    def get_record_by_uuid(job_uuid):
        return session.query(JobsModel).filter_by(job_uuid=job_uuid).first()

    @staticmethod
    def update_task_status(job_uuid, job_status):
        record = session.query(JobsModel).filter_by(job_uuid=job_uuid).first()
        record.job_status = job_status
        session.commit()
        return record.job_uuid

    @staticmethod
    def update_task_reference(job_uuid, reference_uuid):
        record = session.query(JobsModel).filter_by(job_uuid=job_uuid).first()
        record.reference_uuid = reference_uuid
        session.commit()
        return record.job_uuid

    def __repr__(self):
        return f"<JobsModel {self.job_uuid}>"


# drop all tables and recreate them
Base.metadata.create_all(engine)
