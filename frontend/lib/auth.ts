import { User } from "./api";

function storage() {
  return typeof window !== "undefined" ? localStorage : null;
}

export function saveToken(token: string) {
  storage()?.setItem("access_token", token);
}

export function getToken() {
  return storage()?.getItem("access_token") ?? null;
}

export function logout() {
  storage()?.removeItem("access_token");
  storage()?.removeItem("user");
}

export function saveUser(user: User) {
  storage()?.setItem("user", JSON.stringify(user));
}

export function getUser(): User | null {
  const raw = storage()?.getItem("user");
  return raw ? JSON.parse(raw) : null;
}