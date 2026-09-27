import { apiFetch } from "./client";
import type { StructuredRequirement } from "./validation";

export type ValidationStatus = "PASS" | "FAIL" | "UNKNOWN";

export interface EvidenceCoverage {
  supported: number;
  required: number;
}

export interface RecommendationItem {
  product_id: string;
  model_number: string;
  manufacturer_name: string;
  product_name: string;
  validation_status: ValidationStatus;
  recommendation_score: number;
  evidence_coverage: EvidenceCoverage;
  unit_price: string | null;
  currency: string | null;
  lead_time_days: number | null;
  reasons: string[];
}

export interface ExcludedProduct {
  product_id: string;
  model_number: string;
  validation_status: ValidationStatus;
  reason: string;
}

export interface RecommendationResult {
  requirements_summary: string;
  candidate_count: number;
  eligible_count: number;
  primary_recommendation: RecommendationItem | null;
  alternatives: RecommendationItem[];
  excluded_products: ExcludedProduct[];
  message: string | null;
}

export function recommendProducts(
  productIds: string[],
  requirements: StructuredRequirement[],
): Promise<RecommendationResult> {
  return apiFetch<RecommendationResult>("/api/v1/recommendations/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_ids: productIds, requirements }),
  });
}
