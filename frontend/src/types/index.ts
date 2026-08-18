export type Role = "admin" | "faculty" | "student"

export interface User {
  id: number
  username: string
  email: string | null
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

export interface DataSource {
  name: string
  type: string
  status: string
  display_name: string | null
  last_synced_at: string | null
  record_count: number | null
  samvidha_status?: string
}

export interface SystemSetting {
  key: string
  value: string
}

export interface AcademicSummary {
  profile: {
    student_id: string
    full_name: string | null
    department: string | null
    department_code: string | null
    section: string | null
    year: number
    semester: number
    academic_year: string | null
    admission_year: number
    username: string | null
  }
  health: {
    overall_performance: number | null
    attendance: number | null
    engagement: number | null
    internal_1: number | null
    internal_2: number | null
    internal_average: number | null
    assignment_completion: number | null
  }
  subjects: {
    subject_id: number
    subject_name: string | null
    subject_code: string | null
    attendance: number | null
    internal_marks: number | null
    assignment_score: number | null
    total_score: number | null
    grade: string | null
    trend: string
  }[]
  performance_history: { label: string; score: number; semester: number }[]
  risk: {
    risk_probability: number | null
    risk_level: string | null
    model_name: string | null
    thresholds: { risk_low: number; risk_high: number }
  }
  recommendations: string[]
  data_source: DataSource | null
}

export interface ImportValidationReport {
  rows: number
  valid_rows: number
  warnings: number
  rejected: number
  errors: string[]
  errors_total: number
  error_truncated: boolean
  missing_columns: string[]
  column_map: Record<string, string | null>
  will_create_students: boolean
  imported: boolean
  preview: Record<string, unknown>[]
  valid_records?: Record<string, unknown>[]
}

export interface ImportResult {
  imported: boolean
  imported_rows: number
  created_students: string[]
  warnings: number
  rejected: number
  errors_total: number
  source_status: string
  record_count: number | null
}

export interface ImportHistoryItem {
  id: number
  name: string
  filename: string
  rows: number | null
  status: string
  created_at: string | null
}

// ---------------------------------------------------------------------------
// Portal (Samvidha-style academic performance) types
// ---------------------------------------------------------------------------

export interface PortalProfile {
  name?: string
  rollNumber?: string
  studentId?: string
  branch?: string
  regulation?: string
  section?: string
  year?: number
  currentSemester?: number
  cgpa?: number | null
  previousSgpa?: number | null
  previousSemesterCgpa?: number | null
  dateOfAdmission?: string | null
}

export interface PortalTheoryCourse {
  serialNumber?: number
  courseCode?: string
  courseName?: string
  CIE1?: number | null
  AAT1_I?: number | null
  AAT1_II?: number | null
  CIE2?: number | null
  AAT2_I?: number | null
  AAT2_II?: number | null
  totalMarks?: number | null
  credits?: number
  grade?: string
  gradePoint?: number | null
  status?: string
  attendance?: number | null
  courseType?: string
  courseCategory?: string
}

export interface PortalLabCourse {
  serialNumber?: number
  courseCode?: string
  courseName?: string
  week1?: number | null
  week2?: number | null
  week3?: number | null
  week4?: number | null
  week5?: number | null
  week6?: number | null
  week7?: number | null
  week8?: number | null
  week9?: number | null
  week10?: number | null
  week11?: number | null
  week12?: number | null
  week13?: number | null
  week14?: number | null
  examMarks?: number | null
  totalMarks?: number | null
  credits?: number
  grade?: string
  gradePoint?: number | null
  status?: string
  attendance?: number | null
  courseType?: string
}

export interface PortalAttendanceRow {
  courseCode?: string
  courseName?: string
  courseType?: string
  courseCategory?: string
  conducted?: number | null
  attended?: number | null
  attendancePercentage?: number | null
  status?: string
  band?: string
}

export interface PortalGradeRecord {
  courseCode?: string
  courseName?: string
  grade?: string
  gradePoint?: number | null
  status?: string
  credits?: number
  attendancePercentage?: number | null
}

export interface PortalSemesterSummary {
  sgpa?: number | null
  totalCredits?: number
  earnedCredits?: number
  semesterNumber?: number
}

export interface PortalSemesterPerformance {
  semester: number
  sgpa: number | null
  totalCredits: number | null
  earnedCredits: number | null
}

export interface PortalCgpaTrendPoint {
  semester: number
  label: string
  sgpa: number | null
  cgpa: number | null
  completed: boolean
}

export interface PortalSubjectRow {
  semester?: number
  courseCode?: string
  courseName?: string
  courseType?: string
  courseCategory?: string
  credits?: number
  grade?: string
  gradePoint?: number | null
  totalMarks?: number | null
  attendance?: number | null
  status?: string
  type?: string
}

export interface PortalCourseDue {
  category: string
  requiredCourseCount: number
  registeredCourseCount: number
  yetToBeRegistered: number
}

export interface PortalStrength {
  label: string
  courseCode: string | null
  courseName: string | null
  detail: string
}

export interface PortalRisk {
  category: string
  courseCode: string | null
  courseName: string | null
  metric: string
  value: number | null
  detail: string
}

export interface PortalInsight {
  severity: "positive" | "warning" | "neutral"
  title: string
  message: string
}

export interface PortalSummary {
  profile: PortalProfile
  placeholder: boolean
  hero: {
    name?: string
    rollNumber?: string
    section?: string
    cgpa?: number | null
    currentSemester?: number
    currentSemesterLabel?: string
    performanceIndex?: number
    attendance?: number | null
    creditsEarned?: number
    programTotalCredits?: number
  }
  academicOverview: {
    cgpa?: number | null
    previousSgpa?: number | null
    previousSemesterCgpa?: number | null
    attendance?: number | null
    creditsEarned?: number
    performanceIndex?: number
  }
  cgpaTrend: PortalCgpaTrendPoint[]
  semesterPerformance: PortalSemesterPerformance[]
  attendanceAnalysis: PortalAttendanceRow[]
  subjects: PortalSubjectRow[]
  creditProgress: {
    completedCredits: number
    remainingCredits: number
    completionPercent: number
    programTotalCredits: number
  }
  pendingCourses: PortalCourseDue[]
  currentSemesterCourses: {
    courseCode?: string
    courseName?: string
    courseType?: string
    courseCategory?: string
    credits?: number
    attendance?: number | null
    status?: string
  }[]
  performance: {
    performanceIndex: number
    academicScore: number
    attendanceScore: number | null
    internalScore: number | null
    trendScore: number
    creditCompletion: number
    breakdown: Record<string, number>
    weights: Record<string, number>
  }
  strengths: PortalStrength[]
  weaknesses: PortalStrength[]
  risks: PortalRisk[]
  insights: PortalInsight[]
}

export interface PortalSemesterDetail {
  semester: number
  semesterLabel: string
  currentSemester: number | null
  profile: PortalProfile
  theoryCourses: PortalTheoryCourse[]
  labCourses: PortalLabCourse[]
  attendance: PortalAttendanceRow[]
  gradeRecords: PortalGradeRecord[]
  summary: PortalSemesterSummary
  overallCgpa: number | null
}

export interface PortalSemesterList {
  semesters: PortalSemesterPerformance[]
  currentSemester: number
}

export interface PortalProfileDetail extends PortalProfile {
  username: string
  placeholder: boolean
  performanceIndex: number
  creditProgress: {
    completedCredits: number
    remainingCredits: number
    completionPercent: number
    programTotalCredits: number
  }
}

export interface PortalImportResult {
  imported: boolean
  created_students: string[]
  students: number
}
