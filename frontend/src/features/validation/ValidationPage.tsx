import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { fetchDemoEvidence, type EvidenceItem } from "../../api/evidence";
import { fetchProducts } from "../../api/products";

const DEMO_MODELS = ["NS-SW-005", "VIS-SW-003", "AC-SW-008"];

function formatCell(value: unknown, unit?: string | null): string {
  if (value === null || value === undefined) {
    return "missing";
  }
  if (typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (unit) {
    return `${value} ${unit}`;
  }
  return String(value);
}

function formatExpected(operator: string, value: unknown, unit?: string | null): string {
  const formatted = formatCell(value, unit);
  if (operator === "gte") {
    return `>= ${formatted}`;
  }
  if (operator === "lte") {
    return `<= ${formatted}`;
  }
  if (operator === "gt") {
    return `> ${formatted}`;
  }
  if (operator === "lt") {
    return `< ${formatted}`;
  }
  return formatted;
}

function formatEvidenceSummary(items: EvidenceItem[]): string {
  if (items.length === 0) {
    return "Not found";
  }
  const first = items[0];
  const page = first.page_number ? `p.${first.page_number}` : "p.?";
  return `${first.document_title} ${page}`;
}

export function ValidationPage() {
  const [expandedKey, setExpandedKey] = useState<string | null>(null);

  const evidenceQuery = useQuery({
    queryKey: ["evidence", "demo"],
    queryFn: async () => {
      const catalog = await fetchProducts();
      const productIds = DEMO_MODELS.map((modelNumber) => {
        const product = catalog.items.find((item) => item.model_number === modelNumber);
        if (!product) {
          throw new Error(`Demo product ${modelNumber} not found in catalog.`);
        }
        return product.id;
      });
      return fetchDemoEvidence(productIds);
    },
  });

  if (evidenceQuery.isLoading) {
    return <p>Running validation with datasheet evidence…</p>;
  }

  if (evidenceQuery.isError) {
    return (
      <p role="alert">Evidence lookup failed: {(evidenceQuery.error as Error).message}</p>
    );
  }

  return (
    <section aria-labelledby="validation-heading">
      <h2 id="validation-heading">Engineering Validation + Evidence</h2>
      <p>
        Phase 4 deterministic validation with Phase 6 datasheet evidence for the ABC Manufacturing
        RFQ requirements.
      </p>

      {evidenceQuery.data?.results.map((product) => (
        <article key={product.product_id} className="validation-card">
          <h3>
            Recommended Product: {product.model_number}{" "}
            <span className={`validation-status status-${product.status.toLowerCase()}`}>
              {product.status}
            </span>
          </h3>
          <table className="validation-table">
            <thead>
              <tr>
                <th scope="col">Requirement</th>
                <th scope="col">Expected</th>
                <th scope="col">Actual</th>
                <th scope="col">Status</th>
                <th scope="col">Evidence</th>
              </tr>
            </thead>
            <tbody>
              {product.requirements.map((result) => {
                const rowKey = `${product.product_id}-${result.spec_key}`;
                return (
                  <tr key={rowKey}>
                    <td>{result.spec_key.replace(/_/g, " ")}</td>
                    <td>
                      {formatExpected(
                        result.operator,
                        result.required_value,
                        result.required_unit,
                      )}
                    </td>
                    <td>{formatCell(result.actual_value, result.actual_unit)}</td>
                    <td>{result.status}</td>
                    <td>
                      <button
                        type="button"
                        className="evidence-toggle"
                        onClick={() =>
                          setExpandedKey(expandedKey === rowKey ? null : rowKey)
                        }
                      >
                        {formatEvidenceSummary(result.evidence)}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {product.requirements.map((result) => {
            const rowKey = `${product.product_id}-${result.spec_key}`;
            if (expandedKey !== rowKey) {
              return null;
            }
            return (
              <div key={`${rowKey}-details`} className="evidence-panel">
                <h4>{result.spec_key.replace(/_/g, " ")} evidence</h4>
                <p>{result.details}</p>
                {result.evidence.length === 0 ? (
                  <p>No supporting datasheet evidence retrieved.</p>
                ) : (
                  result.evidence.map((item) => (
                    <blockquote key={item.chunk_id}>
                      <p>{item.text}</p>
                      <footer>
                        {item.document_filename}
                        {item.page_number ? ` · page ${item.page_number}` : ""}
                        {` · score ${item.similarity_score.toFixed(2)}`}
                      </footer>
                    </blockquote>
                  ))
                )}
              </div>
            );
          })}
        </article>
      ))}
    </section>
  );
}
