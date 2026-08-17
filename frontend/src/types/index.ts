export type Role = "admin" | "faculty" | "student"

export interface User {
  id: number
  email: string
  full_name: string
  role: Role
  is_active: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  role: Role
  full_name: string
}

export interface StudentSummary {
  id: number
  student_id: string
  full_name: string
  email: string
  section_id: number
  section_name: string | null
  department_name: string | null
  admission_year: number
  current_semester: number
  is_active: boolean
  attendance: number | null
  average_score: number | null
  engagement: number | null
  risk_probability: number | null
  risk_level: string | null
  last_prediction: string | null
}

export interface DashboardAnalytics {
  kpis: {
    total_students: number
    high_risk: number
    moderate_risk: number
    low_risk: number
    unpredicted: number
    average_performance: number
    average_attendance: number
    average_engagement: number
    below_attendance_threshold: number
  }
  risk_distribution: { name: string; value: number; level: string }[]
  performance_trend: { semester: number; average: number }[]
  attendance_performance_scatter: {
    student: string
    student_id: string
    attendance: number
    score: number
  }[]
  subject_performance: { subject: string; average: number; records: number }[]
  students_requiring_attention: {
    id: number
    student_id: string
    name: string
    attendance: number | null
    average_score: number | null
    engagement: number | null
    risk_probability: number | null
    risk_level: string
  }[]
  correlations: {
    attendance_performance: number
    engagement_performance: number
  }
  engagement_distribution: { name: string; value: number }[]
  score_distribution: { range: string; count: number }[]
}

export interface PredictionResult {
  id: number
  student_id: string
  student_name: string
  risk_probability: number
  risk_level: string
  model: string
  prediction_date: string
  factors: { feature: string; impact: string }[]
  recommendations: string[]
}

export interface PredictionWithWarning {
  prediction: PredictionResult
  warning: {
    student_id: number
    student_name: string
    student_id_str: string
    previous_risk: string
    current_risk: string
    previous_probability: number
    current_probability: number
    change: number
    contributing_factors: { feature: string; impact: string }[]
    prediction_date: string
  } | null
}

export interface Intervention {
  id: number
  student_id: number
  student_name: string | null
  student_id_str: string | null
  faculty_id: number
  faculty_name: string | null
  type: string
  title: string
  description: string | null
  status: string
  assigned_date: string | null
  follow_up_date: string | null
  completed_date: string | null
  notes: string | null
}

export interface ModelVersionItem {
  id: number
  model_id: string
  algorithm: string
  training_date: string | null
  accuracy: number | null
  precision: number | null
  recall: number | null
  f1_score: number | null
  roc_auc: number | null
  feature_list: string | null
  training_rows: number | null
  is_active: boolean
}

export interface ModelDetailItem extends ModelVersionItem {
  metrics: string | null
  feature_importance: { feature: string; importance: number }[] | null
  confusion_matrix: { matrix: number[][] } | null
}

export interface DatasetItem {
  id: number
  name: string
  filename: string
  rows: number | null
  columns: number | null
  status: string
  validation_errors: string | null
  created_at: string | null
}

export interface DatasetPreview {
  dataset_id: number
  rows: number
  columns: number
  missing_values: Record<string, number>
  duplicates: number
  dtypes: Record<string, string>
  validation_errors: string[]
  preview: Record<string, unknown>[]
}

export interface NotificationItem {
  id: number
  title: string
  message: string
  type: string
  is_read: boolean
  related_id: number | null
  created_at: string
}

export interface InterventionImpact {
  student_id: number
  student_name: string
  risk_before: number | null
  risk_after: number | null
  performance_before: number | null
  performance_after: number | null
  attendance_before: number | null
  attendance_after: number | null
  risk_reduction: number | null
  performance_improvement: number | null
  attendance_improvement: number | null
  intervention_count: number
  completed_count: number
  message?: string
}

export interface AcademicRecord {
  id: number
  subject_id: number
  subject_name: string | null
  semester: number
  internal_marks: number | null
  assignment_score: number | null
  exam_score: number | null
  total_score: number | null
  grade: string | null
}

export interface AttendanceRecord {
  id: number
  subject_id: number
  subject_name: string | null
  semester: number
  month: number
  classes_held: number
  classes_attended: number
  attendance_percentage: number | null
}

export interface EngagementRecord {
  id: number
  semester: number
  month: number
  participation_score: number | null
  lms_logins: number | null
  forum_posts: number | null
  study_hours: number | null
  engagement_score: number | null
}

export interface Department {
  id: number
  name: string
  code: string
  description: string | null
}

export interface Section {
  id: number
  name: string
  department_id: number
  academic_year: string
  semester: number
}

export interface Subject {
  id: number
  name: string
  code: string
  department_id: number
  credits: number
  semester: number
}
