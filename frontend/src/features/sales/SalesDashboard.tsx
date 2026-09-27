import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { ApiError } from "../../api/client";
import {
  createQuotationCommunication,
  type QuotationCommunication,
} from "../../api/communication";
import { fetchProductsEvidence, type ProductEvidenceResult } from "../../api/evidence";
import { createQuotation, approveQuotation, type Quotation } from "../../api/quotations";
import { recommendProducts, type RecommendationResult } from "../../api/recommendations";
import { extractRfq, type RfqExtractResponse } from "../../api/rfq";
import { fetchProducts, type ProductListItem } from "../../api/products";
import {
  validateProducts,
  type ProductValidationResult,
  type StructuredRequirement,
} from "../../api/validation";
import { DEMO_RFQ, DEMO_SWITCH_MODELS } from "./demoRfq";
import {
  formatExpected,
  formatMoney,
  formatSpecLabel,
  formatValue,
  statusClassName,
  statusSymbol,
} from "./formatters";
import { CustomerCommunicationPanel } from "./CustomerCommunicationPanel";
import { FollowUpPanels } from "./FollowUpPanels";
import { SalesWorkflowStepper, type SalesWorkflowStep } from "./SalesWorkflowStepper";

const DEFAULT_CUSTOMER_EMAIL = "procurement@abcmanufacturing.example";

function toRequirements(extraction: RfqExtractResponse): StructuredRequirement[] {
  return extraction.requirements.map((req) => ({
    spec_key: req.spec_key,
    operator: req.operator,
    value: req.value,
    unit: req.unit,
    required: req.required ?? true,
    priority: req.priority === "must_have" || req.priority === "preferred" ? req.priority : null,
    source_text: req.source_text,
  }));
}

function quotationErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "QUOTATION_VALIDATION_FAILED") {
      return "Quotation cannot be generated because the selected product does not satisfy the required engineering requirements.";
    }
    if (error.code === "QUOTATION_VALIDATION_UNKNOWN") {
      return "Quotation cannot be generated because the technical validation is incomplete.";
    }
    return error.message;
  }
  return (error as Error).message;
}

type SalesDecisionState = "pending" | "accepted" | "alternative";

export function SalesDashboard() {
  const queryClient = useQueryClient();
  const [rawRfq, setRawRfq] = useState("");
  const [extraction, setExtraction] = useState<RfqExtractResponse | null>(null);
  const [requirements, setRequirements] = useState<StructuredRequirement[]>([]);
  const [catalogProducts, setCatalogProducts] = useState<ProductListItem[]>([]);
  const [validationResults, setValidationResults] = useState<ProductValidationResult[]>([]);
  const [evidenceResults, setEvidenceResults] = useState<ProductEvidenceResult[]>([]);
  const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);
  const [salesDecision, setSalesDecision] = useState<SalesDecisionState>("pending");
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [showAlternativePicker, setShowAlternativePicker] = useState(false);
  const [expandedEvidence, setExpandedEvidence] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(10);
  const [discountPercent, setDiscountPercent] = useState("0");
  const [validityDays, setValidityDays] = useState(30);
  const [customerEmail, setCustomerEmail] = useState(DEFAULT_CUSTOMER_EMAIL);
  const [quotation, setQuotation] = useState<Quotation | null>(null);
  const [communication, setCommunication] = useState<QuotationCommunication | null>(null);
  const [currentStep, setCurrentStep] = useState<SalesWorkflowStep>("rfq");
  const [completedThrough, setCompletedThrough] = useState<SalesWorkflowStep | null>(null);

  const extractMutation = useMutation({
    mutationFn: extractRfq,
    onSuccess: (data) => {
      setExtraction(data);
      setRequirements(toRequirements(data));
      setQuantity(data.quantity ?? 10);
      setValidationResults([]);
      setEvidenceResults([]);
      setRecommendation(null);
      setSalesDecision("pending");
      setSelectedProductId(null);
      setShowAlternativePicker(false);
      setQuotation(null);
      setCommunication(null);
      setCurrentStep("requirements");
      setCompletedThrough("rfq");
    },
  });

  const validateMutation = useMutation({
    mutationFn: async () => {
      const catalog = await fetchProducts();
      const candidates = catalog.items
        .filter((product) => DEMO_SWITCH_MODELS.includes(product.model_number))
        .sort(
          (left, right) =>
            DEMO_SWITCH_MODELS.indexOf(left.model_number) -
            DEMO_SWITCH_MODELS.indexOf(right.model_number),
        );
      setCatalogProducts(candidates);
      const productIds = candidates.map((product) => product.id);
      const validation = await validateProducts(productIds, requirements);
      const evidence = await fetchProductsEvidence(productIds, requirements);
      const recommendationResult = await recommendProducts(productIds, requirements);
      return { validation, evidence, recommendationResult };
    },
    onSuccess: ({ validation, evidence, recommendationResult }) => {
      setValidationResults(validation.results);
      setEvidenceResults(evidence.results);
      setRecommendation(recommendationResult);
      setSalesDecision("pending");
      setSelectedProductId(null);
      setShowAlternativePicker(false);
      setQuotation(null);
      setCommunication(null);
      setCurrentStep("recommendation");
      setCompletedThrough("validation");
    },
  });

  const quotationMutation = useMutation({
    mutationFn: () =>
      createQuotation({
        customer_name: extraction?.customer_name ?? "Customer",
        customer_email: customerEmail,
        customer_reference: extraction?.customer_reference ?? undefined,
        title: extraction?.title ?? undefined,
        product_id: selectedProductId ?? "",
        quantity,
        discount_percent: discountPercent,
        validity_days: validityDays,
        requirements,
      }),
    onSuccess: (data) => {
      setQuotation(data);
      setCommunication(null);
      setCurrentStep("approval");
      setCompletedThrough("quotation");
    },
  });

  const approveMutation = useMutation({
    mutationFn: () => approveQuotation(quotation?.id ?? ""),
    onSuccess: async (data) => {
      setQuotation(data);
      setCurrentStep("communication");
      setCompletedThrough("approval");
      const draft = await createQuotationCommunication(data.id, {
        customer_email: customerEmail,
      });
      setCommunication(draft);
    },
  });

  const eligibleProducts = useMemo(() => {
    if (!recommendation) {
      return [];
    }
    const items = [];
    if (recommendation.primary_recommendation) {
      items.push(recommendation.primary_recommendation);
    }
    items.push(...recommendation.alternatives);
    return items;
  }, [recommendation]);

  const acceptRecommendation = () => {
    const primary = recommendation?.primary_recommendation;
    if (!primary) {
      return;
    }
    setSelectedProductId(primary.product_id);
    setSalesDecision("accepted");
    setShowAlternativePicker(false);
    setCurrentStep("decision");
    setCompletedThrough("recommendation");
  };

  const selectEligibleProduct = (productId: string) => {
    const primaryId = recommendation?.primary_recommendation?.product_id;
    setSelectedProductId(productId);
    setSalesDecision(productId === primaryId ? "accepted" : "alternative");
    setShowAlternativePicker(false);
    setCurrentStep("decision");
    setCompletedThrough("recommendation");
  };

  const selectedProduct = useMemo(
    () => catalogProducts.find((product) => product.id === selectedProductId) ?? null,
    [catalogProducts, selectedProductId],
  );

  const selectedValidation = validationResults.find(
    (result) => result.product_id === selectedProductId,
  );
  const selectedEvidence = evidenceResults.find(
    (result) => result.product_id === selectedProductId,
  );

  const selectedRecommendationItem = eligibleProducts.find(
    (item) => item.product_id === selectedProductId,
  );

  return (
    <section className="sales-dashboard" aria-labelledby="sales-heading">
      <header className="sales-header">
        <h2 id="sales-heading">Sales Dashboard</h2>
        <p className="sales-subtitle">
          RFQ → Validation → Recommendation → Quotation → Customer Communication → Follow-up
        </p>
      </header>

      <SalesWorkflowStepper currentStep={currentStep} completedThrough={completedThrough} />

      <FollowUpPanels />

      <div className="sales-grid">
        <section className="card sales-panel">
          <h3>1. RFQ Input</h3>
          <label className="rfq-label" htmlFor="sales-rfq-text">
            Customer RFQ
          </label>
          <textarea
            id="sales-rfq-text"
            className="rfq-textarea"
            rows={10}
            value={rawRfq}
            onChange={(event) => setRawRfq(event.target.value)}
            placeholder="Paste customer RFQ text…"
          />
          <div className="sales-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setRawRfq(DEMO_RFQ)}
            >
              Load Demo RFQ
            </button>
            <button
              type="button"
              className="rfq-submit"
              disabled={extractMutation.isPending || rawRfq.trim().length === 0}
              onClick={() => extractMutation.mutate(rawRfq)}
            >
              {extractMutation.isPending ? "Extracting…" : "Extract Requirements"}
            </button>
          </div>
          {extractMutation.isError ? (
            <p role="alert" className="status-unavailable">
              {(extractMutation.error as Error).message}
            </p>
          ) : null}
        </section>

        {extraction ? (
          <section className="card sales-panel">
            <h3>2. Requirements Review</h3>
            <div className="sales-meta-grid">
              <p>
                <strong>Customer:</strong> {extraction.customer_name ?? "—"}
              </p>
              <p>
                <strong>Reference:</strong> {extraction.customer_reference ?? "—"}
              </p>
              <p>
                <strong>Title:</strong> {extraction.title ?? "—"}
              </p>
              <p>
                <strong>Quantity:</strong> {extraction.quantity ?? "—"}
              </p>
            </div>

            {extraction.ambiguous_notes.length > 0 ? (
              <div className="sales-alert">
                <strong>Review required:</strong> The RFQ contains ambiguous requirements.
                <ul>
                  {extraction.ambiguous_notes.map((note) => (
                    <li key={note.source_text}>{note.source_text}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <table className="sales-table">
              <thead>
                <tr>
                  <th scope="col">Requirement</th>
                  <th scope="col">Operator</th>
                  <th scope="col">Expected</th>
                  <th scope="col">Required</th>
                </tr>
              </thead>
              <tbody>
                {requirements.map((req) => (
                  <tr key={`${req.spec_key}-${req.operator}`}>
                    <td>{formatSpecLabel(req.spec_key)}</td>
                    <td>{req.operator}</td>
                    <td>{formatValue(req.value, req.unit)}</td>
                    <td>{req.required === false ? "Preferred" : "Yes"}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <button
              type="button"
              className="rfq-submit"
              disabled={validateMutation.isPending || requirements.length === 0}
              onClick={() => validateMutation.mutate()}
            >
              {validateMutation.isPending ? "Validating…" : "Validate Products"}
            </button>
            {validateMutation.isError ? (
              <p role="alert" className="status-unavailable">
                Technical validation could not be completed. {(validateMutation.error as Error).message}
              </p>
            ) : null}
          </section>
        ) : null}

        {validationResults.length > 0 ? (
          <section className="card sales-panel sales-panel-wide">
            <h3>3. Technical Validation</h3>
            <div className="product-validation-grid">
              {validationResults.map((productResult) => {
                const catalogProduct = catalogProducts.find(
                  (product) => product.id === productResult.product_id,
                );
                const evidence = evidenceResults.find(
                  (item) => item.product_id === productResult.product_id,
                );
                const isExpanded = expandedEvidence === productResult.product_id;
                return (
                  <article key={productResult.product_id} className="product-card">
                    <header className="product-card-header">
                      <div>
                        <h4>{productResult.model_number}</h4>
                        <p className="catalog-meta">
                          {catalogProduct?.manufacturer.name}
                          <br />
                          {catalogProduct?.name}
                        </p>
                      </div>
                      <span className={statusClassName(productResult.status)}>
                        {productResult.status}
                      </span>
                    </header>

                    <ul className="requirement-breakdown">
                      {productResult.results.map((result) => (
                        <li key={result.spec_key}>
                          <span className={statusClassName(result.status)}>
                            {statusSymbol(result.status)}
                          </span>{" "}
                          {formatSpecLabel(result.spec_key)}
                          {result.status === "FAIL" ? (
                            <div className="catalog-meta">
                              Required: {formatExpected(result)}
                              <br />
                              Actual: {formatValue(result.actual_value, result.actual_unit)}
                            </div>
                          ) : null}
                          {result.status === "UNKNOWN" ? (
                            <div className="catalog-meta">
                              Required: {formatExpected(result)}
                              <br />
                              Actual: {formatValue(result.actual_value, result.actual_unit)}
                            </div>
                          ) : null}
                          {result.status === "PASS" ? (
                            <div className="catalog-meta">
                              {formatValue(result.actual_value, result.actual_unit)}
                            </div>
                          ) : null}
                        </li>
                      ))}
                    </ul>

                    {evidence ? (
                      <div className="evidence-section">
                        <button
                          type="button"
                          className="btn-link"
                          onClick={() =>
                            setExpandedEvidence(isExpanded ? null : productResult.product_id)
                          }
                        >
                          {isExpanded ? "Hide" : "Show"} Technical Evidence
                        </button>
                        {isExpanded ? (
                          <div className="evidence-panel">
                            {evidence.requirements.map((req) =>
                              req.evidence.length > 0 ? (
                                req.evidence.map((item) => (
                                  <blockquote key={item.chunk_id}>
                                    <p className="catalog-meta">
                                      {formatSpecLabel(req.spec_key)} · Page{" "}
                                      {item.page_number ?? "?"}
                                    </p>
                                    <p>{item.text}</p>
                                    <footer>
                                      {item.document_title} · score{" "}
                                      {item.similarity_score.toFixed(2)}
                                    </footer>
                                  </blockquote>
                                ))
                              ) : (
                                <p key={req.spec_key} className="catalog-meta">
                                  {formatSpecLabel(req.spec_key)}: no supporting evidence retrieved.
                                </p>
                              ),
                            )}
                          </div>
                        ) : null}
                      </div>
                    ) : null}

                    <div className="product-card-actions">
                      {productResult.status === "FAIL" ? (
                        <span className="catalog-meta">Not eligible</span>
                      ) : productResult.status === "UNKNOWN" ? (
                        <span className="catalog-meta">Technical validation incomplete</span>
                      ) : (
                        <span className="catalog-meta">Eligible — see system recommendation</span>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        ) : null}

        {recommendation ? (
          <section className="card sales-panel sales-panel-wide recommendation-panel">
            <h3>4. System Recommendation</h3>
            <p className="catalog-meta">{recommendation.requirements_summary}</p>

            {recommendation.primary_recommendation ? (
              <article className="recommendation-card">
                <p className="recommendation-badge">System Recommendation</p>
                <header className="recommendation-header">
                  <div>
                    <h4>{recommendation.primary_recommendation.model_number}</h4>
                    <p className="catalog-meta">
                      {recommendation.primary_recommendation.manufacturer_name}
                      <br />
                      {recommendation.primary_recommendation.product_name}
                    </p>
                  </div>
                  <span className={statusClassName("PASS")}>PASS</span>
                </header>

                <div className="recommendation-metrics">
                  <p>
                    <strong>Evidence Coverage:</strong>{" "}
                    {recommendation.primary_recommendation.evidence_coverage.supported} /{" "}
                    {recommendation.primary_recommendation.evidence_coverage.required}
                  </p>
                  {recommendation.primary_recommendation.unit_price &&
                  recommendation.primary_recommendation.currency ? (
                    <p>
                      <strong>Unit Price:</strong>{" "}
                      {formatMoney(
                        recommendation.primary_recommendation.unit_price,
                        recommendation.primary_recommendation.currency,
                      )}
                    </p>
                  ) : null}
                  {recommendation.primary_recommendation.lead_time_days !== null ? (
                    <p>
                      <strong>Lead Time:</strong>{" "}
                      {recommendation.primary_recommendation.lead_time_days} days
                    </p>
                  ) : null}
                  <p>
                    <strong>Recommendation Score:</strong>{" "}
                    {recommendation.primary_recommendation.recommendation_score}
                  </p>
                </div>

                <div className="recommendation-reasons">
                  <strong>Why this product?</strong>
                  <ul>
                    {recommendation.primary_recommendation.reasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                </div>

                {salesDecision === "pending" ? (
                  <div className="sales-actions">
                    <button type="button" className="rfq-submit" onClick={acceptRecommendation}>
                      Accept Recommendation
                    </button>
                    {eligibleProducts.length > 1 ? (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => setShowAlternativePicker((value) => !value)}
                      >
                        Choose Another Eligible Product
                      </button>
                    ) : null}
                  </div>
                ) : null}

                {showAlternativePicker ? (
                  <div className="alternative-picker">
                    {eligibleProducts.map((item) => (
                      <button
                        key={item.product_id}
                        type="button"
                        className="btn-secondary"
                        onClick={() => selectEligibleProduct(item.product_id)}
                      >
                        {item.model_number}
                        {item.product_id === recommendation.primary_recommendation?.product_id
                          ? " (Recommended)"
                          : " (Alternative)"}
                      </button>
                    ))}
                  </div>
                ) : null}
              </article>
            ) : (
              <p role="status" className="sales-alert">
                {recommendation.message ?? "No technically eligible product was found."}
              </p>
            )}

            {recommendation.alternatives.length > 0 ? (
              <div className="recommendation-alternatives">
                <h4>Alternative Products</h4>
                <table className="sales-table">
                  <thead>
                    <tr>
                      <th scope="col">Product</th>
                      <th scope="col">Status</th>
                      <th scope="col">Score</th>
                      <th scope="col">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recommendation.alternatives.map((item) => (
                      <tr key={item.product_id}>
                        <td>{item.model_number}</td>
                        <td>{item.validation_status}</td>
                        <td>{item.recommendation_score}</td>
                        <td>{item.reasons[0] ?? "Eligible alternative"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            {recommendation.excluded_products.length > 0 ? (
              <div className="recommendation-alternatives">
                <h4>Excluded Products</h4>
                <table className="sales-table">
                  <thead>
                    <tr>
                      <th scope="col">Product</th>
                      <th scope="col">Status</th>
                      <th scope="col">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recommendation.excluded_products.map((item) => (
                      <tr key={item.product_id}>
                        <td>{item.model_number}</td>
                        <td>{item.validation_status}</td>
                        <td>{item.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </section>
        ) : null}

        {recommendation ? (
          <section className="card sales-panel">
            <h3>5. Sales Decision</h3>
            <div className="decision-audit">
              <p>
                <strong>System Recommendation:</strong>{" "}
                {recommendation.primary_recommendation?.model_number ?? "None"}
              </p>
              <p>
                <strong>Sales Decision:</strong>{" "}
                {salesDecision === "pending"
                  ? "Pending"
                  : salesDecision === "accepted"
                    ? "Accepted by Sales"
                    : `Sales selected: ${selectedRecommendationItem?.model_number ?? "—"}`}
              </p>
            </div>
          </section>
        ) : null}

        {selectedProduct && selectedValidation?.status === "PASS" && salesDecision !== "pending" ? (
          <section className="card sales-panel">
            <h3>6. Selected Product</h3>
            <div className="selected-product-summary">
              <p>
                <strong>{selectedProduct.model_number}</strong>
              </p>
              <p>{selectedProduct.manufacturer.name}</p>
              <p>
                <strong>Technical Status:</strong> PASS
              </p>
              <p>
                <strong>Evidence:</strong>{" "}
                {selectedEvidence?.requirements.filter((req) => req.evidence.length > 0).length ??
                  0}{" "}
                requirements supported
              </p>
              <p>
                <strong>Unit Price:</strong>{" "}
                {selectedProduct.pricing
                  ? formatMoney(selectedProduct.pricing.unit_price, selectedProduct.pricing.currency)
                  : "Unavailable"}
              </p>
              <p>
                <strong>Lead Time:</strong> {selectedProduct.pricing?.lead_time_days ?? "—"} days
              </p>
            </div>

            <h3>7. Quotation</h3>
            <div className="quotation-form-grid">
              <label htmlFor="quote-customer">Customer</label>
              <input
                id="quote-customer"
                value={extraction?.customer_name ?? ""}
                readOnly
              />
              <label htmlFor="quote-reference">Customer Reference</label>
              <input
                id="quote-reference"
                value={extraction?.customer_reference ?? ""}
                readOnly
              />
              <label htmlFor="quote-email">Customer Email</label>
              <input
                id="quote-email"
                type="email"
                value={customerEmail}
                onChange={(event) => setCustomerEmail(event.target.value)}
              />
              <label htmlFor="quote-quantity">Quantity</label>
              <input
                id="quote-quantity"
                type="number"
                min={1}
                value={quantity}
                onChange={(event) => setQuantity(Number(event.target.value))}
              />
              <label htmlFor="quote-discount">Discount %</label>
              <input
                id="quote-discount"
                type="number"
                min={0}
                max={100}
                step="0.01"
                value={discountPercent}
                onChange={(event) => setDiscountPercent(event.target.value)}
              />
              <label htmlFor="quote-validity">Validity Days</label>
              <input
                id="quote-validity"
                type="number"
                min={1}
                value={validityDays}
                onChange={(event) => setValidityDays(Number(event.target.value))}
              />
            </div>

            <button
              type="button"
              className="rfq-submit"
              disabled={quotationMutation.isPending}
              onClick={() => quotationMutation.mutate()}
            >
              {quotationMutation.isPending ? "Generating…" : "Generate Quotation"}
            </button>
            {quotationMutation.isError ? (
              <p role="alert" className="status-unavailable">
                {quotationErrorMessage(quotationMutation.error)}
              </p>
            ) : null}
          </section>
        ) : null}

        {quotation ? (
          <section className="card sales-panel sales-panel-wide quotation-document">
            <p className="quotation-draft-banner">DRAFT — REQUIRES SALES REVIEW</p>
            <h3>QUOTATION</h3>
            <div className="sales-meta-grid">
              <p>
                <strong>Quotation:</strong> {quotation.quotation_number}
              </p>
              <p>
                <strong>Date:</strong> {new Date(quotation.created_at).toLocaleDateString()}
              </p>
              <p>
                <strong>Customer:</strong> {quotation.customer_name}
              </p>
              <p>
                <strong>Reference:</strong> {quotation.customer_reference ?? "—"}
              </p>
              <p>
                <strong>Valid for:</strong> {quotation.validity_days} days
              </p>
              <p>
                <strong>Lead time:</strong> {quotation.lead_time_days} days
              </p>
            </div>

            <table className="sales-table">
              <thead>
                <tr>
                  <th scope="col">Product</th>
                  <th scope="col">Description</th>
                  <th scope="col">Qty</th>
                  <th scope="col">Unit Price</th>
                  <th scope="col">Total</th>
                </tr>
              </thead>
              <tbody>
                {quotation.lines.map((line) => (
                  <tr key={line.id}>
                    <td>{line.model_number}</td>
                    <td>{line.description}</td>
                    <td>{line.quantity}</td>
                    <td>{formatMoney(line.unit_price, line.currency)}</td>
                    <td>{formatMoney(line.line_total, line.currency)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="quotation-totals">
              <p>
                <span>Subtotal</span>
                <strong>{formatMoney(quotation.subtotal, quotation.currency)}</strong>
              </p>
              <p>
                <span>Discount</span>
                <strong>{formatMoney(quotation.discount_amount, quotation.currency)}</strong>
              </p>
              <p>
                <span>Total</span>
                <strong>{formatMoney(quotation.total, quotation.currency)}</strong>
              </p>
            </div>

            <div className="technical-summary">
              <p>
                <strong>Technical Compliance:</strong> {quotation.technical_status}
              </p>
              <p className="catalog-meta">
                Validated against customer RFQ requirements.
                {quotation.technical_status === "PASS" ? " Technical evidence available." : ""}
              </p>
            </div>

            {quotation.status === "DRAFT" ? (
              <div className="sales-actions">
                <button type="button" className="btn-secondary">
                  Review & Approve
                </button>
                <button
                  type="button"
                  className="rfq-submit"
                  disabled={approveMutation.isPending}
                  onClick={() => approveMutation.mutate()}
                >
                  {approveMutation.isPending ? "Approving…" : "Approve Quotation"}
                </button>
              </div>
            ) : (
              <p className={statusClassName("PASS")}>{quotation.status}</p>
            )}
          </section>
        ) : null}

        {quotation ? (
          <CustomerCommunicationPanel
            quotation={quotation}
            customerEmail={customerEmail}
            onCustomerEmailChange={setCustomerEmail}
            communication={communication}
            onCommunicationChange={setCommunication}
            onQuotationUpdate={setQuotation}
            onQuotationSent={(updatedQuotation, updatedCommunication) => {
              setQuotation(updatedQuotation);
              setCommunication(updatedCommunication);
              setCompletedThrough("sent");
              setCurrentStep("followup");
              queryClient.invalidateQueries({ queryKey: ["follow-ups"] });
            }}
            onStepChange={(step) => {
              setCurrentStep(step);
              if (step === "sent") {
                setCompletedThrough("sent");
              }
            }}
          />
        ) : null}
      </div>
    </section>
  );
}
