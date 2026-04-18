/**
 * Extract FastAPI-style `detail` from an Axios error without coupling callers to axios types.
 */
export function getApiErrorDetail(err: unknown, fallback: string): string {
  if (typeof err !== "object" || err === null || !("response" in err)) {
    return fallback
  }

  const data = (err as {
    response?: {
      data?: {
        detail?: unknown
        errors?: Array<{ msg?: unknown }>
      }
    }
  }).response?.data

  if (typeof data?.detail === "string" && data.detail.trim()) {
    return data.detail
  }

  const firstValidationMessage = data?.errors?.find((item) => typeof item?.msg === "string")?.msg
  if (typeof firstValidationMessage === "string" && firstValidationMessage.trim()) {
    return firstValidationMessage
  }

  return fallback
}
