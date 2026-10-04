import { apiFetch } from "./client";

export type ValidationStatus = "PASS" | "FAIL" | "UNKNOWN";

export interface StructuredRequirement {
  spec_key: string;
  operator: string;
  value?: boolean | number | string | string[] | null;
  unit?: string | null;
  required?: boolean;
  priority?: "must_have" | "preferred" | null;
  source_text?: string | null;
}

export interface RequirementValidationResult {
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
}

export interface ProductValidationResult {
  product_id: string;
  model_number: string;
  status: ValidationStatus;
  results: RequirementValidationResult[];
}

export interface ValidateProductsResponse {
  results: ProductValidationResult[];
}

export const DEMO_REQUIREMENTS: StructuredRequirement[] = [
  {
    spec_key: "input_voltage",
    operator: "eq",
    value: 24,
    unit: "V",
    required: true,
    priority: "must_have",
    source_text: "24 VDC power",
  },
  {
    spec_key: "ethernet_ports",
    operator: "gte",
    value: 5,
    required: true,
    priority: "must_have",
    source_text: "minimum 5 Ethernet ports",
  },
  {
    spec_key: "din_rail_mountable",
    operator: "eq",
    value: true,
    required: true,
    priority: "must_have",
    source_text: "DIN rail mounting",
  },
  {
    spec_key: "supports_modbus_tcp",
    operator: "eq",
    value: true,
    required: true,
    priority: "must_have",
    source_text: "Modbus TCP support",
  },
  {
    spec_key: "operating_temp_min",
    operator: "lte",
    value: -20,
    unit: "°C",
    required: true,
    priority: "must_have",
    source_text: "operating temperature down to -20°C",
  },
];

export async function validateProducts(
  productIds: string[],
  requirements: StructuredRequirement[],
): Promise<ValidateProductsResponse> {
  return apiFetch<ValidateProductsResponse>("/api/v1/validation/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      product_ids: productIds,
      requirements,
    }),
  });
}

export async function validateDemoProducts(
  productIds: string[],
): Promise<ValidateProductsResponse> {
  return validateProducts(productIds, DEMO_REQUIREMENTS);
}
