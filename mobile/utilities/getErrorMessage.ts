type ErrorPayload = {
  message?: string;
  error?: {
    message?: string;
  };
  details?: {
    field?: string | null;
    issue?: string;
  }[];
};

function formatFieldName(field: string) {
  return field
    .split(".")
    .map((part) =>
      part
        .replace(/_/g, " ")
        .trim()
        .replace(/\b\w/g, (char) => char.toUpperCase())
    )
    .join(" ");
}

export default function getErrorMessage(data: unknown, fallback: string) {
  if (!data || typeof data !== "object") {
    return fallback;
  }

  const payload = data as ErrorPayload;
  const firstDetail = payload.details?.find((detail) => detail?.issue);

  if (firstDetail?.issue) {
    if (firstDetail.field) {
      return `${formatFieldName(firstDetail.field)}: ${firstDetail.issue}`;
    }
    return firstDetail.issue;
  }

  return payload.message || payload.error?.message || fallback;
}
