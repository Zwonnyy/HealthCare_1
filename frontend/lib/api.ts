import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
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
