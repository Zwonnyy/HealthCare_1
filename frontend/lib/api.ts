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

// ── Users ──────────────────────────────────────────
export const userApi = {
  me: () => api.get<User>("/users/me"),
  searchPatients: (q: string) =>
    api.get<PatientSearchResult[]>("/users/patients/search", { params: { q } }),
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
  list: (page = 1, size = 20) =>
    api.get<PaginatedResponse<MedicalRecord>>("/records", { params: { page, size } }),
  get: (id: number) => api.get<MedicalRecord>(`/records/${id}`),
  create: (data: {
    patient_id: number;
    diagnosis: string;
    symptoms: string;
    notes?: string;
    visited_at: string;
    prescriptions: Omit<Prescription, "id">[];
  }) => api.post<MedicalRecord>("/records", data),
  requestGuide: (recordId: number) =>
    api.post<Guide>(`/records/${recordId}/guides`),
  getGuides: (recordId: number) =>
    api.get<Guide[]>(`/records/${recordId}/guides`),
};

// ── Guides ─────────────────────────────────────────
export const guideApi = {
  get: (id: number) => api.get<Guide>(`/guides/${id}`),
};
