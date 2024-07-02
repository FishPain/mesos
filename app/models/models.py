import uuid, os
from datetime import datetime
from celery import states

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON


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
            return None

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


class InferenceModel(Base):
    __tablename__ = "inference_model"
    inference_uuid = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_uuid = Column(String(36), ForeignKey("user_model.user_uuid"), nullable=False)
    inference_datetime = Column(DateTime, nullable=False, default=datetime.now())
    inference_status = Column(String(80), nullable=False)
    inference_output = Column(JSON, nullable=True)

    def __init__(
        self,
        inference_uuid,
        user_uuid,
        inference_status,
        inference_output=None,
    ):
        self.inference_uuid = inference_uuid
        self.user_uuid = user_uuid
        self.inference_status = inference_status
        self.inference_output = inference_output

    @staticmethod
    def save_inference_to_db(
        inference_uuid,
        user_uuid,
        inference_status,
        inference_output=None,
    ):
        inference = InferenceModel(
            inference_uuid=inference_uuid,
            user_uuid=user_uuid,
            inference_status=inference_status,
            inference_output=inference_output,
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
    def get_latest_completed_record():
        return (
            session.query(InferenceModel)
            .filter_by(inference_status=states.SUCCESS)
            .order_by(InferenceModel.inference_datetime.desc())
            .first()
        )
    
    @staticmethod
    def get_all_inference_job():
        return (
            session.query(InferenceModel)
            .order_by(InferenceModel.inference_datetime.desc())
        )

    @staticmethod
    def update_inference_status(inference_uuid, inference_status):
        record = (
            session.query(InferenceModel)
            .filter_by(inference_uuid=inference_uuid)
            .first()
        )
        record.inference_status = inference_status
        session.commit()
        return record.inference_uuid

    def update_inference_output(inference_uuid, inference_output):
        record = (
            session.query(InferenceModel)
            .filter_by(inference_uuid=inference_uuid)
            .first()
        )
        record.inference_output = inference_output
        session.commit()
        return record.inference_uuid

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
