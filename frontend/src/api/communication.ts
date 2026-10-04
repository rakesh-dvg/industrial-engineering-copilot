import { apiFetch } from "./client";

export type CommunicationStatus = "DRAFT" | "READY_TO_SEND" | "SENT";

export interface QuotationCommunication {
  id: string;
  quotation_id: string;
  customer_name: string;
  customer_email: string;
  subject: string;
  body: string;
  status: CommunicationStatus;
  sent_at: string | null;
  demo_mode: boolean;
  created_at: string;
  updated_at: string;
}

export interface SendQuotationResponse {
  quotation_id: string;
  communication: QuotationCommunication;
  send_detail: string;
  demo_mode: boolean;
}

export function getQuotationCommunication(
  quotationId: string,
): Promise<QuotationCommunication | null> {
  return apiFetch<QuotationCommunication | null>(
    `/api/v1/quotations/${quotationId}/communication`,
  );
}

export function createQuotationCommunication(
  quotationId: string,
  payload: { customer_email?: string } = {},
): Promise<QuotationCommunication> {
  return apiFetch<QuotationCommunication>(`/api/v1/quotations/${quotationId}/communication`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateQuotationCommunication(
  quotationId: string,
  payload: {
    customer_email?: string;
    subject?: string;
    body?: string;
    status?: CommunicationStatus;
  },
): Promise<QuotationCommunication> {
  return apiFetch<QuotationCommunication>(`/api/v1/quotations/${quotationId}/communication`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function sendQuotationToCustomer(quotationId: string): Promise<SendQuotationResponse> {
  return apiFetch<SendQuotationResponse>(`/api/v1/quotations/${quotationId}/send`, {
    method: "POST",
  });
}
