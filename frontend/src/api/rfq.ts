import { apiFetch } from "./client";

export interface StructuredRequirement {
  spec_key: string;
  operator: string;
  value?: boolean | number | string | string[] | null;
  unit?: string | null;
  required?: boolean;
  priority?: string | null;
  source_text?: string | null;
}

export interface AmbiguousRequirementNote {
  source_text: string;
  description?: string | null;
}

export interface RfqExtractResponse {
  customer_name?: string | null;
  customer_reference?: string | null;
  title?: string | null;
  quantity?: number | null;
  requirements: StructuredRequirement[];
  ambiguous_notes: AmbiguousRequirementNote[];
}

export function extractRfq(rawText: string): Promise<RfqExtractResponse> {
  return apiFetch<RfqExtractResponse>("/api/v1/rfqs/extract", {
    method: "POST",
    body: JSON.stringify({ raw_text: rawText }),
  });
}
