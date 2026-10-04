import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { fetchDemoEvidence } from "../../api/evidence";
import { fetchProducts } from "../../api/products";
import { approveQuotation, createQuotation, type Quotation } from "../../api/quotations";

const DEMO_CUSTOMER = {
  customer_name: "ABC Manufacturing",
  customer_reference: "RFQ-001",
  title: "Industrial Ethernet Switch Quotation",
};

function formatMoney(value: string, currency: string): string {
  return `${currency} ${Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function QuotationPreview({
  quotation,
  onApprove,
  isApproving,
}: {
  quotation: Quotation;
  onApprove: () => void;
  isApproving: boolean;
}) {
  const createdDate = new Date(quotation.created_at).toLocaleDateString();

  return (
    <article className="quotation-preview" aria-labelledby="quotation-preview-heading">
      <h3 id="quotation-preview-heading">Quotation Preview</h3>
      <p className="quotation-draft-banner">DRAFT — REQUIRES SALES REVIEW</p>

      <pre className="quotation-document">
        {`==================================================
                 QUOTATION
==================================================

Quotation: ${quotation.quotation_number}
Date: ${createdDate}
Valid for: ${quotation.validity_days} days

Customer:
${quotation.customer_name}

Reference:
${quotation.customer_reference ?? "—"}

--------------------------------------------------
Product          Qty    Unit Price       Total
--------------------------------------------------`}
        {quotation.lines.map((line) =>
          `\n${line.model_number.padEnd(16)} ${String(line.quantity).padStart(3)} ${formatMoney(line.unit_price, quotation.currency).padStart(12)} ${formatMoney(line.line_total, quotation.currency).padStart(12)}`,
        )}
        {`

--------------------------------------------------
Subtotal                         ${formatMoney(quotation.subtotal, quotation.currency).padStart(12)}
Discount                         ${formatMoney(quotation.discount_amount, quotation.currency).padStart(12)}
TOTAL                            ${formatMoney(quotation.total, quotation.currency).padStart(12)}
--------------------------------------------------

Technical Compliance: ${quotation.technical_status}
Lead Time: ${quotation.lead_time_days} days
Validity: ${quotation.validity_days} days

Technical requirements validated against
product specifications and supporting evidence.
==================================================`}
      </pre>

      {quotation.status === "DRAFT" ? (
        <button type="button" onClick={onApprove} disabled={isApproving}>
          {isApproving ? "Approving…" : "Review / Approve"}
        </button>
      ) : (
        <p>Status: {quotation.status}</p>
      )}
    </article>
  );
}

export function QuotationPage() {
  const [selectedProductId, setSelectedProductId] = useState<string>("");
  const [quantity, setQuantity] = useState(10);
  const [discountPercent, setDiscountPercent] = useState("0");
  const [validityDays, setValidityDays] = useState(30);
  const [quotation, setQuotation] = useState<Quotation | null>(null);

  const catalogQuery = useQuery({
    queryKey: ["catalog", "quotation-products"],
    queryFn: fetchProducts,
  });

  const demoProductIds = useMemo(() => {
    const models = ["NS-SW-005", "VIS-SW-003", "AC-SW-008"];
    return models
      .map((modelNumber) => catalogQuery.data?.items.find((item) => item.model_number === modelNumber)?.id)
      .filter((value): value is string => Boolean(value));
  }, [catalogQuery.data]);

  const evidenceQuery = useQuery({
    queryKey: ["evidence", "quotation"],
    queryFn: () => fetchDemoEvidence(demoProductIds),
    enabled: demoProductIds.length === 3,
  });

  const createMutation = useMutation({
    mutationFn: createQuotation,
    onSuccess: (result) => setQuotation(result),
  });

  const approveMutation = useMutation({
    mutationFn: approveQuotation,
    onSuccess: (result) => setQuotation(result),
  });

  const selectedEvidence = evidenceQuery.data?.results.find(
    (item) => item.product_id === selectedProductId,
  );

  if (catalogQuery.isLoading || evidenceQuery.isLoading) {
    return <p>Loading quotation workflow…</p>;
  }

  if (catalogQuery.isError || evidenceQuery.isError) {
    return <p role="alert">Failed to load quotation workflow.</p>;
  }

  return (
    <section aria-labelledby="quotation-heading">
      <h2 id="quotation-heading">Generate Quotation</h2>
      <p>
        Select a validated product, enter commercial terms, and generate a customer-ready
        quotation draft from catalog pricing.
      </p>

      <div className="quotation-form">
        <label htmlFor="quotation-product">Product</label>
        <select
          id="quotation-product"
          value={selectedProductId}
          onChange={(event) => setSelectedProductId(event.target.value)}
        >
          <option value="">Select product…</option>
          {evidenceQuery.data?.results.map((item) => (
            <option key={item.product_id} value={item.product_id}>
              {item.model_number} — {item.status}
            </option>
          ))}
        </select>

        {selectedEvidence ? (
          <p>
            Technical status: <strong>{selectedEvidence.status}</strong>
            {selectedEvidence.status !== "PASS" ? (
              <span> (quotation generation will be blocked)</span>
            ) : null}
          </p>
        ) : null}

        <label htmlFor="quotation-quantity">Quantity</label>
        <input
          id="quotation-quantity"
          type="number"
          min={1}
          value={quantity}
          onChange={(event) => setQuantity(Number(event.target.value))}
        />

        <label htmlFor="quotation-discount">Discount (%)</label>
        <input
          id="quotation-discount"
          type="number"
          min={0}
          max={100}
          step="0.01"
          value={discountPercent}
          onChange={(event) => setDiscountPercent(event.target.value)}
        />

        <label htmlFor="quotation-validity">Validity (days)</label>
        <input
          id="quotation-validity"
          type="number"
          min={1}
          value={validityDays}
          onChange={(event) => setValidityDays(Number(event.target.value))}
        />

        <button
          type="button"
          disabled={!selectedProductId || createMutation.isPending}
          onClick={() =>
            createMutation.mutate({
              ...DEMO_CUSTOMER,
              product_id: selectedProductId,
              quantity,
              discount_percent: discountPercent,
              validity_days: validityDays,
            })
          }
        >
          {createMutation.isPending ? "Generating…" : "Generate Quotation"}
        </button>
      </div>

      {createMutation.isError ? (
        <p role="alert">{(createMutation.error as Error).message}</p>
      ) : null}

      {quotation ? (
        <QuotationPreview
          quotation={quotation}
          onApprove={() => approveMutation.mutate(quotation.id)}
          isApproving={approveMutation.isPending}
        />
      ) : null}
    </section>
  );
}
