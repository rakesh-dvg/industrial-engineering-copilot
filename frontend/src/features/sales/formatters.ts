import type { RequirementValidationResult } from "../../api/validation";

export function formatSpecLabel(specKey: string): string {
  return specKey.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatOperator(operator: string): string {
  const mapping: Record<string, string> = {
    eq: "=",
    neq: "≠",
    gt: ">",
    gte: "≥",
    lt: "<",
    lte: "≤",
    contains: "contains",
    in: "in",
  };
  return mapping[operator] ?? operator;
}

export function formatValue(value: unknown, unit?: string | null): string {
  if (value === null || value === undefined) {
    return "Not documented";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (unit) {
    return `${value} ${unit}`;
  }
  return String(value);
}

export function formatExpected(result: RequirementValidationResult): string {
  const formatted = formatValue(result.required_value, result.required_unit);
  if (result.operator === "gte") {
    return `≥ ${formatted}`;
  }
  if (result.operator === "lte") {
    return `≤ ${formatted}`;
  }
  if (result.operator === "gt") {
    return `> ${formatted}`;
  }
  if (result.operator === "lt") {
    return `< ${formatted}`;
  }
  return formatted;
}

export function formatMoney(value: string, currency: string): string {
  return `${currency} ${Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function statusSymbol(status: string): string {
  if (status === "PASS") {
    return "✓";
  }
  if (status === "FAIL") {
    return "✕";
  }
  return "?";
}

export function statusClassName(status: string): string {
  return `status-badge status-${status.toLowerCase()}`;
}
