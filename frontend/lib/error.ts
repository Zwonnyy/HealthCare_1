type ApiError = {
  response?: {
    data?: {
      detail?: string | { msg: string }[];
    };
  };
};

export function getErrorMessage(err: unknown, fallback = "오류가 발생했어요."): string {
  const detail = (err as ApiError)?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(", ");
  return fallback;
}