import { apiFetch } from "./client";
import { DEMO_REQUIREMENTS, type StructuredRequirement } from "./validation";

export type QuotationStatus = "DRAFT" | "REVIEWED" | "APPROVED" | "READY_TO_SEND" | "SENT";

export interface QuotationLine {
  id: string;
  product_id: string;
  model_number: string;
  description: string;
  quantity: number;
  unit_price: string;
  currency: string;
  discount_percent: string;
  line_subtotal: string;
  line_total: string;
}

export interface Quotation {
  id: string;
  quotation_number: string;
  status: QuotationStatus;
  customer_name: string;
  customer_email?: string | null;
  customer_reference?: string | null;
  title?: string | null;
  currency: string;
  validity_days: number;
  lead_time_days: number;
  technical_status: "PASS" | "FAIL" | "UNKNOWN";
  subtotal: string;
  discount_percent: string;
  discount_amount: string;
  total: string;
  lines: QuotationLine[];
  created_at: string;
  updated_at: string;
}

export interface CreateQuotationPayload {
  customer_name: string;
  customer_email?: string;
  customer_reference?: string;
  title?: string;
  product_id: string;
  quantity: number;
  discount_percent?: string;
  validity_days?: number;
  requirements?: StructuredRequirement[];
}

export interface QuotationListResponse {
  items: Quotation[];
  total: number;
}

export function createQuotation(payload: CreateQuotationPayload): Promise<Quotation> {
  return apiFetch<Quotation>("/api/v1/quotations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...payload,
      requirements: payload.requirements ?? DEMO_REQUIREMENTS,
    }),
  });
}

export function fetchQuotation(quotationId: string): Promise<Quotation> {
  return apiFetch<Quotation>(`/api/v1/quotations/${quotationId}`);
}

export function approveQuotation(quotationId: string): Promise<Quotation> {
  return apiFetch<Quotation>(`/api/v1/quotations/${quotationId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "APPROVED" }),
  });
}
