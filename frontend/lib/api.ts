import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

type RetriableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean };

const api = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1`,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err: AxiosError) => {
    const original = err.config as RetriableRequestConfig | undefined;
    const isAuthEndpoint = original?.url?.startsWith("/auth/");

    if (err.response?.status === 401 && original && !original._retry && !isAuthEndpoint) {
      original._retry = true;
      try {
        const { data } = await api.get<{ access_token: string }>("/auth/token/refresh");
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", data.access_token);
        }
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          window.location.href = "/login";
        }
      }
    } else if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;

// ── Types ──────────────────────────────────────────
export type UserRole = "DOCTOR" | "PATIENT";
export type GuideStatus = "PENDING" | "GENERATING" | "COMPLETED" | "FAILED";

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  profile_image_url: string | null;
}

export interface Prescription {
  id: number;
  medication_name: string;
  dosage: string;
  frequency: string;
  duration_days: number;
  instructions: string | null;
}

export interface MedicalRecord {
  id: number;
  patient_id: number;
  doctor_id: number;
  diagnosis: string;
  symptoms: string;
  notes: string | null;
  visited_at: string;
  created_at: string;
  prescriptions: Prescription[];
}

export interface Guide {
  id: number;
  record_id: number;
  medication_guide: string | null;
  lifestyle_guide: string | null;
  status: GuideStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

// ── Auth ───────────────────────────────────────────
export const authApi = {
  signup: (data: {
    email: string;
    password: string;
    name: string;
    gender: string;
    birth_date: string;
    phone_number: string;
    role: UserRole;
  }) => api.post("/auth/signup", data),

  login: (email: string, password: string) =>
    api.post<{ access_token: string }>("/auth/login", { email, password }),
  logout: () => api.post("/auth/logout"),
  refresh: () => api.get<{ access_token: string }>("/auth/token/refresh"),
};

export interface PatientSearchResult {
  id: number;
  name: string;
  email: string;
}

export interface DoctorSearchResult {
  id: number;
  name: string;
  email: string;
}

export interface UserInfo {
  id: number;
  name: string;
  email: string;
  phone_number: string;
  profile_image_url: string | null;
  birthday: string;
  gender: "MALE" | "FEMALE";
  role: UserRole;
  created_at: string;
}

// ── Users ──────────────────────────────────────────
export const userApi = {
  me: () => api.get<UserInfo>("/users/me"),
  updateMe: (data: {
    name?: string;
    email?: string;
    phone_number?: string;
    birthday?: string;
    gender?: "MALE" | "FEMALE";
    current_password?: string;
    new_password?: string;
  }) => api.patch<UserInfo>("/users/me", data),
  uploadProfileImage: (file: File) => {
    const formData = new FormData();
    formData.append("image", file);
    return api.post<UserInfo>("/users/me/profile-image", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  searchPatients: (q: string) =>
    api.get<PatientSearchResult[]>("/users/patients/search", { params: { q } }),
  searchDoctors: (q: string) =>
    api.get<DoctorSearchResult[]>("/users/doctors/search", { params: { q } }),
};

// ── Pagination ─────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ── Records ────────────────────────────────────────
export const recordApi = {
  list: (page = 1, size = 20, q?: string) =>
    api.get<PaginatedResponse<MedicalRecord>>("/records", { params: { page, size, ...(q ? { q } : {}) } }),
  get: (id: number) => api.get<MedicalRecord>(`/records/${id}`),
  create: (data: {
    patient_id: number;
    diagnosis: string;
    symptoms: string;
    notes?: string;
    visited_at: string;
    prescriptions: Omit<Prescription, "id">[];
  }) => api.post<MedicalRecord>("/records", data),
  update: (id: number, data: { diagnosis?: string; symptoms?: string; notes?: string }) =>
    api.patch<MedicalRecord>(`/records/${id}`, data),
  requestGuide: (recordId: number) =>
    api.post<Guide>(`/records/${recordId}/guides`),
  getGuides: (recordId: number) =>
    api.get<Guide[]>(`/records/${recordId}/guides`),
};

// ── Guides ─────────────────────────────────────────
export const guideApi = {
  get: (id: number) => api.get<Guide>(`/guides/${id}`),
};

// ── Message Types ──────────────────────────────────
export interface Message {
  id: number;
  sender_id: number;
  receiver_id: number;
  record_id: number | null;
  content: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

// ── Health Log Types ───────────────────────────────
export type Mood = "GREAT" | "GOOD" | "NORMAL" | "BAD" | "TERRIBLE";
export type AnalysisStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface HealthLog {
  id: number;
  patient_id: number;
  record_id: number | null;
  log_date: string;
  pain_score: number;
  mood: Mood;
  symptoms_text: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HealthLogAnalysis {
  id: number;
  patient_id: number;
  record_id: number | null;
  analysis_text: string | null;
  status: AnalysisStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

// ── Notification Types ─────────────────────────────
export type NotificationType =
  | "MESSAGE_RECEIVED"
  | "RECORD_CREATED"
  | "GUIDE_COMPLETED"
  | "ANALYSIS_COMPLETED"
  | "APPOINTMENT_REQUESTED"
  | "APPOINTMENT_CONFIRMED"
  | "MEDICATION_REMINDER";

export interface Notification {
  id: number;
  user_id: number;
  notification_type: NotificationType;
  title: string;
  body: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

// ── Stats Types ────────────────────────────────────
export interface PatientStats {
  total_records: number;
  unread_messages: number;
  health_log_stats: {
    total: number;
    avg_pain_score_7d: number | null;
    avg_pain_score_30d: number | null;
    pain_trend_14d: { date: string; avg_pain_score: number }[];
  };
  mood_distribution_30d: {
    GREAT: number;
    GOOD: number;
    NORMAL: number;
    BAD: number;
    TERRIBLE: number;
  };
}

export interface DoctorStats {
  total_patients: number;
  total_records: number;
  records_last_30d: number;
  unread_messages: number;
  pending_guides: number;
}

// ── Messages API ───────────────────────────────────
export const messageApi = {
  send: (data: { receiver_id: number; record_id?: number; content: string }) =>
    api.post<Message>("/messages", data),
  inbox: (page = 1, size = 20) =>
    api.get<PaginatedResponse<Message>>("/messages/inbox", { params: { page, size } }),
  sent: (page = 1, size = 20) =>
    api.get<PaginatedResponse<Message>>("/messages/sent", { params: { page, size } }),
  unreadCount: () => api.get<{ unread_count: number }>("/messages/unread-count"),
  get: (id: number) => api.get<Message>(`/messages/${id}`),
};

// ── Health Logs API ────────────────────────────────
export const healthLogApi = {
  list: (page = 1, size = 20) =>
    api.get<PaginatedResponse<HealthLog>>("/health-logs", { params: { page, size } }),
  create: (data: {
    record_id?: number;
    log_date: string;
    pain_score: number;
    mood: Mood;
    symptoms_text: string;
    notes?: string;
  }) => api.post<HealthLog>("/health-logs", data),
  delete: (id: number) => api.delete(`/health-logs/${id}`),
  requestAnalysis: (record_id?: number) =>
    api.post<HealthLogAnalysis>("/health-logs/analyze", { record_id }),
  getAnalysis: (analysis_id: number) =>
    api.get<HealthLogAnalysis>(`/health-logs/analyses/${analysis_id}`),
};

// ── Notifications API ──────────────────────────────
export const notificationApi = {
  list: (page = 1, size = 20) =>
    api.get<PaginatedResponse<Notification>>("/notifications", { params: { page, size } }),
  unreadCount: () => api.get<{ count: number }>("/notifications/unread-count"),
  markRead: (id: number) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch("/notifications/read-all"),
};

// ── Stats API ──────────────────────────────────────
export const statsApi = {
  patient: () => api.get<PatientStats>("/stats/patient"),
  doctor: () => api.get<DoctorStats>("/stats/doctor"),
};

// ── Appointment Types ───────────────────────────────
export type AppointmentStatus = "PENDING" | "CONFIRMED" | "CANCELLED" | "COMPLETED";

export interface Appointment {
  id: number;
  patient_id: number;
  doctor_id: number;
  requested_at: string;
  status: AppointmentStatus;
  patient_notes: string | null;
  doctor_notes: string | null;
  created_at: string;
  updated_at: string;
}

export const appointmentApi = {
  create: (data: { doctor_id: number; requested_at: string; patient_notes?: string }) =>
    api.post<Appointment>("/appointments", data),
  list: (page = 1, size = 10) =>
    api.get<PaginatedResponse<Appointment>>("/appointments", { params: { page, size } }),
  updateStatus: (id: number, data: { status: AppointmentStatus; doctor_notes?: string }) =>
    api.patch<Appointment>(`/appointments/${id}`, data),
  cancel: (id: number) => api.delete(`/appointments/${id}`),
};

// ── Medication Check Types ──────────────────────────
export interface TodayMedication {
  prescription: Prescription;
  checked: boolean;
}

export const medicationCheckApi = {
  today: () => api.get<TodayMedication[]>("/medication-checks/today"),
  toggle: (prescriptionId: number) =>
    api.post<{ checked: boolean }>(`/medication-checks/${prescriptionId}/toggle`),
};

// ── Health Trend ────────────────────────────────────
export interface TrendPoint {
  date: string;
  pain_score: number;
  mood: string;
}

export const healthTrendApi = {
  get: (days = 30) => api.get<TrendPoint[]>("/health-logs/trend", { params: { days } }),
};

// ── Health Goal Types ───────────────────────────────
export type GoalType = "WEIGHT" | "BLOOD_PRESSURE" | "EXERCISE_DAYS" | "PAIN_SCORE" | "CUSTOM";

export interface HealthGoal {
  id: number;
  patient_id: number;
  goal_type: GoalType;
  title: string;
  target_value: number;
  current_value: number | null;
  unit: string;
  deadline: string | null;
  achieved: boolean;
  created_at: string;
  updated_at: string;
}

export interface HealthGoalHistoryPoint {
  id: number;
  recorded_value: number;
  recorded_at: string;
}

export const healthGoalApi = {
  list: () => api.get<HealthGoal[]>("/health-goals/goals"),
  create: (data: { goal_type: GoalType; title: string; target_value: number; unit: string; deadline?: string }) =>
    api.post<HealthGoal>("/health-goals/goals", data),
  update: (id: number, data: { current_value?: number; achieved?: boolean }) =>
    api.patch<HealthGoal>(`/health-goals/goals/${id}`, data),
  delete: (id: number) => api.delete(`/health-goals/goals/${id}`),
  history: (goalId: number) => api.get<HealthGoalHistoryPoint[]>(`/health-goals/goals/${goalId}/history`),
};

// ── Health Report Types ─────────────────────────────
export type ReportStatus = "PENDING" | "COMPLETED" | "FAILED";

export interface HealthReport {
  id: number;
  patient_id: number;
  year: number;
  month: number;
  report_text: string | null;
  status: ReportStatus;
  error_message: string | null;
  created_at: string;
}

export const healthReportApi = {
  generate: (year: number, month: number) =>
    api.post<HealthReport>(`/health-reports/generate?year=${year}&month=${month}`),
  list: () => api.get<HealthReport[]>("/health-reports"),
};

// ── Drug Interaction Types ──────────────────────────
export interface DrugInteraction {
  id: number;
  record_id: number;
  status: "PENDING" | "COMPLETED" | "FAILED";
  result_text: string | null;
  has_warning: boolean;
  error_message: string | null;
  created_at: string;
}

export const drugInteractionApi = {
  check: (recordId: number) => api.post<DrugInteraction>(`/records/${recordId}/interactions`),
  getLatest: (recordId: number) => api.get<DrugInteraction | null>(`/records/${recordId}/interactions`),
};

// ── Vitals Types ────────────────────────────────────
export interface VitalRecord {
  id: number;
  patient_id: number;
  systolic: number | null;
  diastolic: number | null;
  blood_sugar: number | null;
  weight: number | null;
  heart_rate: number | null;
  notes: string | null;
  alert_message: string | null;
  recorded_at: string;
}

export const vitalApi = {
  record: (data: {
    systolic?: number;
    diastolic?: number;
    blood_sugar?: number;
    weight?: number;
    heart_rate?: number;
    notes?: string;
  }) => api.post<VitalRecord>("/vitals", data),
  list: (limit = 20) => api.get<VitalRecord[]>("/vitals", { params: { limit } }),
};

// ── Symptom Check Types ─────────────────────────────
export type UrgencyLevel = "LOW" | "MEDIUM" | "HIGH";

export interface SymptomCheck {
  id: number;
  symptom_text: string;
  ai_assessment: string | null;
  urgency: UrgencyLevel | null;
  suggest_appointment: boolean;
  created_at: string;
}

export const symptomCheckApi = {
  check: (symptom_text: string) => api.post<SymptomCheck>("/symptom-check", { symptom_text }),
  list: () => api.get<SymptomCheck[]>("/symptom-check"),
};

// ── Medication Reminder Types ───────────────────────
export interface MedicationReminder {
  id: number;
  patient_id: number;
  name: string;
  reminder_time: string;
  enabled: boolean;
  created_at: string;
}

export const reminderApi = {
  list: () => api.get<MedicationReminder[]>("/reminders"),
  create: (data: { name: string; reminder_time: string }) => api.post<MedicationReminder>("/reminders", data),
  update: (id: number, data: { enabled?: boolean; reminder_time?: string; name?: string }) =>
    api.patch<MedicationReminder>(`/reminders/${id}`, data),
  delete: (id: number) => api.delete(`/reminders/${id}`),
};

// ── AI Health Insight Types ────────────────────────
export interface RiskSignal {
  label: string;
  detail: string;
  severity: number;
}

export interface HealthRisk {
  risk_level: "낮음" | "주의" | "높음";
  score: number;
  summary: string;
  signals: RiskSignal[];
  recommendations: string[];
}

export interface MedicationAdherenceItem {
  prescription_id: number;
  medication_name: string;
  expected_days: number;
  checked_days: number;
  adherence_rate: number;
}

export interface MedicationAdherence {
  period_days: number;
  overall_rate: number;
  summary: string;
  items: MedicationAdherenceItem[];
}

export interface PreVisitQuestionnaire {
  id: number;
  appointment_id: number;
  patient_id: number;
  symptoms: string;
  onset: string | null;
  severity: number | null;
  medications: string | null;
  history: string | null;
  questions: string | null;
  ai_summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface PatientTimelineItem {
  id: number;
  type: "record" | "health_log" | "vital" | "symptom_check" | "pre_visit";
  title: string;
  summary: string;
  occurred_at: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface PatientTimeline {
  patient_id: number;
  patient_name: string;
  period_days: number;
  items: PatientTimelineItem[];
}

export const healthInsightApi = {
  risk: (days = 30) => api.get<HealthRisk>("/health-insights/risk", { params: { days } }),
  medicationAdherence: (days = 30) =>
    api.get<MedicationAdherence>("/health-insights/medication-adherence", { params: { days } }),
  createPreVisit: (
    appointmentId: number,
    data: {
      symptoms: string;
      onset?: string;
      severity?: number;
      medications?: string;
      history?: string;
      questions?: string;
    }
  ) => api.post<PreVisitQuestionnaire>(`/health-insights/appointments/${appointmentId}/pre-visit`, data),
  preVisits: (appointmentId?: number) =>
    api.get<PreVisitQuestionnaire[]>("/health-insights/pre-visits", {
      params: appointmentId ? { appointment_id: appointmentId } : undefined,
    }),
  patientTimeline: (patientId: number, days = 90) =>
    api.get<PatientTimeline>(`/health-insights/patients/${patientId}/timeline`, { params: { days } }),
};
