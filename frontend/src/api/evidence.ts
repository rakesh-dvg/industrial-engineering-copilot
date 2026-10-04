import { apiFetch } from "./client";
import {
  DEMO_REQUIREMENTS,
  type StructuredRequirement,
  type ValidationStatus,
} from "./validation";

export type EvidenceStatus = "found" | "not_found" | "insufficient";

export interface EvidenceItem {
  text: string;
  page_number?: number | null;
  document_id: string;
  chunk_id: string;
  document_title: string;
  document_filename: string;
  similarity_score: number;
}

export interface RequirementEvidenceResult {
  spec_key: string;
  operator: string;
  required: boolean;
  priority?: "must_have" | "preferred" | null;
  status: ValidationStatus;
  required_value?: boolean | number | string | string[] | null;
  required_unit?: string | null;
  actual_value?: boolean | number | string | string[] | null;
  actual_unit?: string | null;
  details: string;
  source_text?: string | null;
  evidence_status: EvidenceStatus;
  evidence: EvidenceItem[];
}

export interface ProductEvidenceResult {
  product_id: string;
  model_number: string;
  status: ValidationStatus;
  requirements: RequirementEvidenceResult[];
}

export interface ProductsEvidenceResponse {
  results: ProductEvidenceResult[];
}

export async function fetchProductsEvidence(
  productIds: string[],
  requirements: StructuredRequirement[],
): Promise<ProductsEvidenceResponse> {
  return apiFetch<ProductsEvidenceResponse>("/api/v1/evidence/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      product_ids: productIds,
      requirements,
    }),
  });
}

export async function fetchDemoEvidence(productIds: string[]): Promise<ProductsEvidenceResponse> {
  return fetchProductsEvidence(productIds, DEMO_REQUIREMENTS);
}
