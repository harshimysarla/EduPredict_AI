from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=6)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: Optional[str] = None
    full_name: str
    role: str
    is_active: bool


class DataSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: str
    status: str
    description: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    record_count: Optional[int] = None


class SystemSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    value: str


class SubjectAnalysis(BaseModel):
    subject_id: int
    subject_name: str
    subject_code: str
    attendance: Optional[float] = None
    internal_marks: Optional[float] = None
    assignment_score: Optional[float] = None
    engagement: Optional[float] = None
    total_score: Optional[float] = None
    grade: Optional[str] = None
    trend: Optional[str] = None  # up / down / stable


class AcademicSummaryOut(BaseModel):
    profile: dict
    health: dict
    subjects: List[SubjectAnalysis]
    performance_history: List[dict]
    risk: dict
    recommendations: List[str] = []
    data_source: dict


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    description: Optional[str] = None


class SectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    department_id: int
    academic_year: str
    semester: int


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    department_id: int
    credits: int
    semester: int


class StudentCreate(BaseModel):
    student_id: str
    full_name: str
    username: str
    email: Optional[str] = None
    password: str = Field(min_length=6)
    section_id: int
    admission_year: int
    current_semester: int = 1


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    section_id: Optional[int] = None
    admission_year: Optional[int] = None
    current_semester: Optional[int] = None
    is_active: Optional[bool] = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: str
    full_name: str
    email: Optional[str] = None
    section_id: int
    section_name: Optional[str] = None
    department_name: Optional[str] = None
    admission_year: int
    current_semester: int
    is_active: bool
    attendance: Optional[float] = None
    average_score: Optional[float] = None
    engagement: Optional[float] = None
    risk_probability: Optional[float] = None
    risk_level: Optional[str] = None
    last_prediction: Optional[datetime] = None


class AcademicRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject_id: int
    subject_name: Optional[str] = None
    semester: int
    internal_marks: Optional[float] = None
    assignment_score: Optional[float] = None
    exam_score: Optional[float] = None
    total_score: Optional[float] = None
    grade: Optional[str] = None


class AttendanceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject_id: int
    subject_name: Optional[str] = None
    semester: int
    month: int
    classes_held: int
    classes_attended: int
    attendance_percentage: Optional[float] = None


class EngagementRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    semester: int
    month: int
    participation_score: Optional[float] = None
    lms_logins: Optional[int] = None
    forum_posts: Optional[int] = None
    study_hours: Optional[float] = None
    engagement_score: Optional[float] = None


class PredictionRequest(BaseModel):
    attendance: float = Field(ge=0, le=100)
    previous_performance: float = Field(ge=0, le=100)
    internal_marks: float = Field(ge=0, le=100)
    assignment_score: float = Field(ge=0, le=100)
    engagement: float = Field(ge=0, le=100)
    study_hours: Optional[float] = Field(default=0, ge=0, le=24)


class PredictionOut(BaseModel):
    id: int
    student_id: str
    student_name: Optional[str] = None
    risk_probability: float
    risk_level: str
    model_name: str
    model_version: Optional[str] = None
    prediction_date: datetime
    factors: List[dict] = []
    recommendations: List[str] = []


class InterventionCreate(BaseModel):
    student_id: int
    type: str
    title: str
    description: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None


class InterventionUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None


class InterventionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    student_name: Optional[str] = None
    student_id_str: Optional[str] = None
    faculty_id: int
    faculty_name: Optional[str] = None
    type: str
    title: str
    description: Optional[str] = None
    status: str
    assigned_date: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    related_id: Optional[int] = None
    created_at: datetime


class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    model_id: str
    algorithm: str
    training_date: Optional[datetime] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    roc_auc: Optional[float] = None
    feature_list: Optional[str] = None
    training_rows: Optional[int] = None
    is_active: bool


class ModelDetail(ModelOut):
    metrics: Optional[str] = None
    feature_importance: Optional[List[dict]] = None
    confusion_matrix: Optional[dict] = None


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    filename: str
    rows: Optional[int] = None
    columns: Optional[int] = None
    status: str
    validation_errors: Optional[str] = None
    created_at: Optional[datetime] = None


class DatasetPreview(BaseModel):
    dataset_id: int
    rows: int
    columns: int
    missing_values: dict
    duplicates: int
    dtypes: dict
    validation_errors: list
    preview: list


class EarlyWarningOut(BaseModel):
    student_id: int
    student_name: str
    student_id_str: str
    previous_risk: str
    current_risk: str
    previous_probability: float
    current_probability: float
    change: float
    contributing_factors: list
    prediction_date: datetime


class ReportRequest(BaseModel):
    student_id: int


class InterventionImpactOut(BaseModel):
    student_id: int
    student_name: str
    risk_before: Optional[float] = None
    risk_after: Optional[float] = None
    performance_before: Optional[float] = None
    performance_after: Optional[float] = None
    attendance_before: Optional[float] = None
    attendance_after: Optional[float] = None
    risk_reduction: Optional[float] = None
    performance_improvement: Optional[float] = None
    attendance_improvement: Optional[float] = None
    intervention_count: int = 0
    completed_count: int = 0
