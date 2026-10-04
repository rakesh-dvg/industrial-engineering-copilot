import { apiFetch } from "./client";

export interface ManufacturerSummary {
  id: string;
  name: string;
  description?: string | null;
  website?: string | null;
  is_active: boolean;
}

export interface ProductCategorySummary {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  is_active: boolean;
}

export interface ProductPricing {
  unit_price: string;
  currency: string;
  discount_percent: string;
  lead_time_days: number;
  price_valid_until?: string | null;
  is_active: boolean;
}

export interface ProductListItem {
  id: string;
  model_number: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  manufacturer: ManufacturerSummary;
  category: ProductCategorySummary;
  pricing?: ProductPricing | null;
}

export interface ProductListResponse {
  items: ProductListItem[];
  total: number;
}

export function fetchProducts(): Promise<ProductListResponse> {
  return apiFetch<ProductListResponse>("/api/v1/products");
}
