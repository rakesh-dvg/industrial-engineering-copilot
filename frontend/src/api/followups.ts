import { apiFetch } from "./client";

export type FollowUpPriority = "P0" | "P1" | "P2";
export type FollowUpStatus = "OPEN" | "COMPLETED";

export interface FollowUpQuotationSummary {
  id: string;
  quotation_number: string;
  status: string;
  currency: string;
  total: string;
  sent_at: string | null;
}

export interface SalesFollowUp {
  id: string;
  quotation_id: string;
  customer_name: string;
  customer_email: string;
  quotation_number: string;
  follow_up_date: string;
  priority: FollowUpPriority;
  status: FollowUpStatus;
  notes: string | null;
  quotation: FollowUpQuotationSummary;
  created_at: string;
  updated_at: string;
}

export interface SalesFollowUpListResponse {
  items: SalesFollowUp[];
  total: number;
}

export function fetchFollowUps(params?: {
  status?: FollowUpStatus;
  due_date?: string;
  sent_only?: boolean;
}): Promise<SalesFollowUpListResponse> {
  const search = new URLSearchParams();
  if (params?.status) {
    search.set("status", params.status);
  }
  if (params?.due_date) {
    search.set("due_date", params.due_date);
  }
  if (params?.sent_only) {
    search.set("sent_only", "true");
  }
  const query = search.toString();
  return apiFetch<SalesFollowUpListResponse>(
    `/api/v1/sales/follow-ups${query ? `?${query}` : ""}`,
  );
}

export function updateFollowUp(
  followUpId: string,
  payload: {
    follow_up_date?: string;
    priority?: FollowUpPriority;
    status?: FollowUpStatus;
    notes?: string;
  },
): Promise<SalesFollowUp> {
  return apiFetch<SalesFollowUp>(`/api/v1/sales/follow-ups/${followUpId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function priorityLabel(priority: FollowUpPriority): string {
  if (priority === "P0") {
    return "P0 — Immediate";
  }
  if (priority === "P1") {
    return "P1 — Important";
  }
  return "P2 — Normal";
}
