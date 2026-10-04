import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../api/client";
import { SalesDashboard } from "./SalesDashboard";

const mockExtract = vi.fn();
const mockFetchProducts = vi.fn();
const mockValidateProducts = vi.fn();
const mockFetchEvidence = vi.fn();
const mockRecommendProducts = vi.fn();
const mockCreateQuotation = vi.fn();
const mockApproveQuotation = vi.fn();
const mockCreateCommunication = vi.fn();
const mockSendQuotation = vi.fn();
const mockFetchFollowUps = vi.fn();
const mockUpdateFollowUp = vi.fn();

vi.mock("../../api/rfq", () => ({
  extractRfq: (...args: unknown[]) => mockExtract(...args),
}));

vi.mock("../../api/products", () => ({
  fetchProducts: (...args: unknown[]) => mockFetchProducts(...args),
}));

vi.mock("../../api/validation", () => ({
  validateProducts: (...args: unknown[]) => mockValidateProducts(...args),
}));

vi.mock("../../api/evidence", () => ({
  fetchProductsEvidence: (...args: unknown[]) => mockFetchEvidence(...args),
}));

vi.mock("../../api/recommendations", () => ({
  recommendProducts: (...args: unknown[]) => mockRecommendProducts(...args),
}));

vi.mock("../../api/quotations", () => ({
  createQuotation: (...args: unknown[]) => mockCreateQuotation(...args),
  approveQuotation: (...args: unknown[]) => mockApproveQuotation(...args),
}));

vi.mock("../../api/communication", () => ({
  createQuotationCommunication: (...args: unknown[]) => mockCreateCommunication(...args),
  sendQuotationToCustomer: (...args: unknown[]) => mockSendQuotation(...args),
  updateQuotationCommunication: vi.fn(),
}));

vi.mock("../../api/followups", () => ({
  fetchFollowUps: (...args: unknown[]) => mockFetchFollowUps(...args),
  updateFollowUp: (...args: unknown[]) => mockUpdateFollowUp(...args),
  priorityLabel: (priority: string) => priority,
}));

const extraction = {
  customer_name: "ABC Manufacturing",
  customer_reference: "RFQ-001",
  title: "Industrial Ethernet Switch Quotation",
  quantity: 10,
  requirements: [
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
  ],
  ambiguous_notes: [],
};

const catalogProducts = {
  items: [
    {
      id: "pass-id",
      model_number: "NS-SW-005",
      name: "Industrial Ethernet Switch 5-Port",
      manufacturer: { name: "Northstar Automation" },
      pricing: {
        unit_price: "185.00",
        currency: "USD",
        lead_time_days: 14,
      },
    },
    {
      id: "fail-id",
      model_number: "VIS-SW-003",
      name: "Industrial Ethernet Switch 3-Port",
      manufacturer: { name: "Vector Industrial Systems" },
      pricing: {
        unit_price: "145.00",
        currency: "USD",
        lead_time_days: 10,
      },
    },
    {
      id: "unknown-id",
      model_number: "AC-SW-008",
      name: "Industrial Ethernet Switch 8-Port",
      manufacturer: { name: "Apex Controls" },
      pricing: {
        unit_price: "210.00",
        currency: "USD",
        lead_time_days: 21,
      },
    },
  ],
  total: 3,
};

const followUpItem = {
  id: "fu-1",
  quotation_id: "quote-1",
  customer_name: "ABC Manufacturing",
  customer_email: "procurement@abcmanufacturing.example",
  quotation_number: "Q-2026-0001",
  follow_up_date: new Date().toISOString().slice(0, 10),
  priority: "P1" as const,
  status: "OPEN" as const,
  notes: null,
  quotation: {
    id: "quote-1",
    quotation_number: "Q-2026-0001",
    status: "SENT",
    currency: "USD",
    total: "1850.00",
    sent_at: "2026-09-27T12:00:00Z",
  },
  created_at: "2026-09-27T00:00:00Z",
  updated_at: "2026-09-27T00:00:00Z",
};

const recommendationResult = {
  requirements_summary: "2 required engineering constraints",
  candidate_count: 3,
  eligible_count: 1,
  primary_recommendation: {
    product_id: "pass-id",
    model_number: "NS-SW-005",
    manufacturer_name: "Northstar Automation",
    product_name: "Industrial Ethernet Switch 5-Port",
    validation_status: "PASS",
    recommendation_score: 94,
    evidence_coverage: { supported: 2, required: 2 },
    unit_price: "185.00",
    currency: "USD",
    lead_time_days: 14,
    reasons: ["Only product satisfying all required engineering constraints."],
  },
  alternatives: [],
  excluded_products: [
    {
      product_id: "fail-id",
      model_number: "VIS-SW-003",
      validation_status: "FAIL",
      reason: "Does not satisfy one or more required engineering constraints",
    },
    {
      product_id: "unknown-id",
      model_number: "AC-SW-008",
      validation_status: "UNKNOWN",
      reason: "Technical validation is incomplete",
    },
  ],
  message: null,
};

function renderDashboard() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <SalesDashboard />
    </QueryClientProvider>,
  );
}

async function runThroughValidation() {
  fireEvent.change(screen.getByLabelText("Customer RFQ"), { target: { value: "RFQ" } });
  fireEvent.click(screen.getByRole("button", { name: "Extract Requirements" }));
  await screen.findByRole("button", { name: "Validate Products" });
  fireEvent.click(screen.getByRole("button", { name: "Validate Products" }));
  await screen.findByText("4. System Recommendation");
}

describe("SalesDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockExtract.mockResolvedValue(extraction);
    mockFetchProducts.mockResolvedValue(catalogProducts);
    mockRecommendProducts.mockResolvedValue(recommendationResult);
    mockValidateProducts.mockResolvedValue({
      results: [
        {
          product_id: "pass-id",
          model_number: "NS-SW-005",
          status: "PASS",
          results: [
            {
              spec_key: "input_voltage",
              operator: "eq",
              required: true,
              status: "PASS",
              required_value: 24,
              required_unit: "V",
              actual_value: 24,
              actual_unit: "V",
              details: "pass",
            },
          ],
        },
        {
          product_id: "fail-id",
          model_number: "VIS-SW-003",
          status: "FAIL",
          results: [
            {
              spec_key: "ethernet_ports",
              operator: "gte",
              required: true,
              status: "FAIL",
              required_value: 5,
              actual_value: 3,
              details: "fail",
            },
          ],
        },
        {
          product_id: "unknown-id",
          model_number: "AC-SW-008",
          status: "UNKNOWN",
          results: [
            {
              spec_key: "operating_temp_min",
              operator: "lte",
              required: true,
              status: "UNKNOWN",
              required_value: -20,
              actual_value: null,
              details: "unknown",
            },
          ],
        },
      ],
    });
    mockFetchEvidence.mockResolvedValue({
      results: [
        {
          product_id: "pass-id",
          model_number: "NS-SW-005",
          status: "PASS",
          requirements: [
            {
              spec_key: "input_voltage",
              operator: "eq",
              required: true,
              status: "PASS",
              details: "pass",
              evidence_status: "found",
              evidence: [
                {
                  text: "Input Voltage: 24 VDC nominal",
                  page_number: 1,
                  document_id: "doc-1",
                  chunk_id: "chunk-1",
                  document_title: "NS-SW-005 Datasheet",
                  document_filename: "NS-SW-005-datasheet.txt",
                  similarity_score: 0.8,
                },
              ],
            },
          ],
        },
        { product_id: "fail-id", model_number: "VIS-SW-003", status: "FAIL", requirements: [] },
        {
          product_id: "unknown-id",
          model_number: "AC-SW-008",
          status: "UNKNOWN",
          requirements: [],
        },
      ],
    });
    mockCreateQuotation.mockResolvedValue({
      id: "quote-1",
      quotation_number: "Q-2026-0001",
      status: "DRAFT",
      customer_name: "ABC Manufacturing",
      customer_reference: "RFQ-001",
      currency: "USD",
      validity_days: 30,
      lead_time_days: 14,
      technical_status: "PASS",
      subtotal: "1850.00",
      discount_percent: "0",
      discount_amount: "0.00",
      total: "1850.00",
      lines: [
        {
          id: "line-1",
          product_id: "pass-id",
          model_number: "NS-SW-005",
          description: "Industrial Ethernet Switch 5-Port",
          quantity: 10,
          unit_price: "185.00",
          currency: "USD",
          discount_percent: "0",
          line_subtotal: "1850.00",
          line_total: "1850.00",
        },
      ],
      created_at: "2026-09-27T00:00:00Z",
      updated_at: "2026-09-27T00:00:00Z",
    });
    mockApproveQuotation.mockResolvedValue({
      id: "quote-1",
      quotation_number: "Q-2026-0001",
      status: "APPROVED",
      customer_name: "ABC Manufacturing",
      customer_email: "procurement@abcmanufacturing.example",
      currency: "USD",
      validity_days: 30,
      lead_time_days: 14,
      technical_status: "PASS",
      subtotal: "1850.00",
      discount_percent: "0",
      discount_amount: "0.00",
      total: "1850.00",
      lines: [],
      created_at: "2026-09-27T00:00:00Z",
      updated_at: "2026-09-27T00:00:00Z",
    });
    mockCreateCommunication.mockResolvedValue({
      id: "comm-1",
      quotation_id: "quote-1",
      customer_name: "ABC Manufacturing",
      customer_email: "procurement@abcmanufacturing.example",
      subject: "Quotation Q-2026-0001 — Industrial Ethernet Switch Quotation",
      body: "Dear ABC Manufacturing,\n\nThank you for your enquiry.",
      status: "DRAFT",
      sent_at: null,
      demo_mode: true,
      created_at: "2026-09-27T00:00:00Z",
      updated_at: "2026-09-27T00:00:00Z",
    });
    mockSendQuotation.mockResolvedValue({
      quotation_id: "quote-1",
      demo_mode: true,
      send_detail: "Demo mode: quotation communication recorded as sent.",
      communication: {
        id: "comm-1",
        quotation_id: "quote-1",
        customer_name: "ABC Manufacturing",
        customer_email: "procurement@abcmanufacturing.example",
        subject: "Quotation Q-2026-0001 — Industrial Ethernet Switch Quotation",
        body: "Dear ABC Manufacturing,\n\nThank you for your enquiry.",
        status: "SENT",
        sent_at: "2026-09-27T12:00:00Z",
        demo_mode: true,
        created_at: "2026-09-27T00:00:00Z",
        updated_at: "2026-09-27T12:00:00Z",
      },
    });
    mockFetchFollowUps.mockImplementation((params?: { sent_only?: boolean }) => {
      if (params?.sent_only) {
        return Promise.resolve({ items: [], total: 0 });
      }
      return Promise.resolve({ items: [], total: 0 });
    });
    mockUpdateFollowUp.mockResolvedValue({
      ...followUpItem,
      status: "COMPLETED",
    });
  });

  it("renders the sales dashboard", () => {
    renderDashboard();
    expect(screen.getByRole("heading", { name: "Sales Dashboard" })).toBeInTheDocument();
  });

  it("loads demo RFQ into the textarea", () => {
    renderDashboard();
    fireEvent.click(screen.getByRole("button", { name: "Load Demo RFQ" }));
    expect((screen.getByLabelText("Customer RFQ") as HTMLTextAreaElement).value).toContain(
      "ABC Manufacturing",
    );
  });

  it("shows extracted requirements after RFQ extraction", async () => {
    renderDashboard();
    fireEvent.change(screen.getByLabelText("Customer RFQ"), {
      target: { value: "Customer RFQ text" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Extract Requirements" }));

    await waitFor(() => {
      expect(screen.getByText("2. Requirements Review")).toBeInTheDocument();
    });
    expect(screen.getByText("ABC Manufacturing")).toBeInTheDocument();
    expect(screen.getByText("Input Voltage")).toBeInTheDocument();
  });

  it("shows validation and recommendation after validating products", async () => {
    renderDashboard();
    await runThroughValidation();

    expect(screen.getByText("3. Technical Validation")).toBeInTheDocument();
    expect(screen.getByText("4. System Recommendation")).toBeInTheDocument();
    expect(screen.getByText("System Recommendation")).toBeInTheDocument();
    expect(screen.getByText("Only product satisfying all required engineering constraints.")).toBeInTheDocument();
    expect(screen.getByText("2 / 2")).toBeInTheDocument();
    expect(mockRecommendProducts).toHaveBeenCalled();
  });

  it("shows excluded FAIL and UNKNOWN products in recommendation", async () => {
    renderDashboard();
    await runThroughValidation();

    expect(screen.getByText("Excluded Products")).toBeInTheDocument();
    expect(screen.getAllByText("VIS-SW-003").length).toBeGreaterThan(0);
    expect(screen.getAllByText("AC-SW-008").length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: "Generate Quotation" })).not.toBeInTheDocument();
  });

  it("accepts recommendation and passes sales-selected product to quotation", async () => {
    renderDashboard();
    await runThroughValidation();
    fireEvent.click(screen.getByRole("button", { name: "Accept Recommendation" }));

    expect(screen.getByText("Accepted by Sales")).toBeInTheDocument();
    expect(screen.getByText("6. Selected Product")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Generate Quotation" }));

    await waitFor(() => {
      expect(mockCreateQuotation).toHaveBeenCalledWith(
        expect.objectContaining({ product_id: "pass-id", quantity: 10 }),
      );
    });
  });

  it("does not generate quotation from recommendation alone", async () => {
    renderDashboard();
    await runThroughValidation();

    expect(screen.queryByRole("button", { name: "Generate Quotation" })).not.toBeInTheDocument();
    expect(mockCreateQuotation).not.toHaveBeenCalled();
  });

  it("generates quotation totals after sales decision", async () => {
    renderDashboard();
    await runThroughValidation();
    fireEvent.click(screen.getByRole("button", { name: "Accept Recommendation" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Quotation" }));

    await waitFor(() => {
      expect(screen.getByText("Q-2026-0001")).toBeInTheDocument();
    });
    expect(screen.getByText("DRAFT — REQUIRES SALES REVIEW")).toBeInTheDocument();
    expect(screen.getAllByText(/USD 1,850.00/).length).toBeGreaterThan(0);
  });

  it("approves the quotation and shows customer communication", async () => {
    renderDashboard();
    await runThroughValidation();
    fireEvent.click(screen.getByRole("button", { name: "Accept Recommendation" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Quotation" }));
    await screen.findByRole("button", { name: "Approve Quotation" });
    fireEvent.click(screen.getByRole("button", { name: "Approve Quotation" }));

    await waitFor(() => {
      expect(screen.getByText("8. Customer Communication")).toBeInTheDocument();
    });
    expect(screen.getByLabelText("To")).toHaveValue("procurement@abcmanufacturing.example");
    expect(
      screen.getByText("DEMO CUSTOMER — No external email will be sent"),
    ).toBeInTheDocument();
    expect(screen.getByText(/Thank you for your enquiry/i)).toBeInTheDocument();
  });

  it("sends quotation after explicit sales action", async () => {
    renderDashboard();
    await runThroughValidation();
    fireEvent.click(screen.getByRole("button", { name: "Accept Recommendation" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Quotation" }));
    await screen.findByRole("button", { name: "Approve Quotation" });
    fireEvent.click(screen.getByRole("button", { name: "Approve Quotation" }));
    await screen.findByRole("button", { name: "Send to Customer" });
    fireEvent.click(screen.getByRole("button", { name: "Send to Customer" }));

    await waitFor(() => {
      expect(mockSendQuotation).toHaveBeenCalledWith("quote-1");
    });
    expect(screen.getByText(/Demo mode: quotation recorded as sent/i)).toBeInTheDocument();
  });

  it("shows RFQ extraction errors without crashing", async () => {
    mockExtract.mockRejectedValue(new Error("Groq API is not configured"));

    renderDashboard();
    fireEvent.change(screen.getByLabelText("Customer RFQ"), { target: { value: "RFQ" } });
    fireEvent.click(screen.getByRole("button", { name: "Extract Requirements" }));

    await waitFor(() => {
      expect(screen.getByText(/Groq API is not configured/i)).toBeInTheDocument();
    });
  });

  it("shows quotation validation failed errors", async () => {
    mockCreateQuotation.mockRejectedValue(
      new ApiError(
        "Product does not satisfy required engineering requirements.",
        422,
        "QUOTATION_VALIDATION_FAILED",
      ),
    );

    renderDashboard();
    await runThroughValidation();
    fireEvent.click(screen.getByRole("button", { name: "Accept Recommendation" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Quotation" }));

    await waitFor(() => {
      expect(
        screen.getByText(/does not satisfy the required engineering requirements/i),
      ).toBeInTheDocument();
    });
  });

  it("renders all workflow stepper labels on load", () => {
    renderDashboard();
    const stepper = screen.getByRole("list", { name: "Sales workflow" });
    expect(stepper).toHaveTextContent("RFQ");
    expect(stepper).toHaveTextContent("Follow-up");
    expect(stepper).toHaveTextContent("Customer Email");
  });

  it("marks Requirements current after extraction", async () => {
    renderDashboard();
    fireEvent.change(screen.getByLabelText("Customer RFQ"), {
      target: { value: "Customer RFQ text" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Extract Requirements" }));

    await screen.findByText("2. Requirements Review");
    const currentStep = document.querySelector(".sales-step-current .sales-step-label");
    expect(currentStep).toHaveTextContent("Requirements");
  });

  it("prefills procurement email in quotation form", async () => {
    renderDashboard();
    await runThroughValidation();
    fireEvent.click(screen.getByRole("button", { name: "Accept Recommendation" }));

    expect(screen.getByLabelText("Customer Email")).toHaveValue(
      "procurement@abcmanufacturing.example",
    );
  });

  it("passes procurement email when approving quotation", async () => {
    renderDashboard();
    await runThroughValidation();
    fireEvent.click(screen.getByRole("button", { name: "Accept Recommendation" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Quotation" }));
    await screen.findByRole("button", { name: "Approve Quotation" });
    fireEvent.click(screen.getByRole("button", { name: "Approve Quotation" }));

    await waitFor(() => {
      expect(mockCreateCommunication).toHaveBeenCalledWith("quote-1", {
        customer_email: "procurement@abcmanufacturing.example",
      });
    });
  });

  it("shows empty follow-up panels on initial load", () => {
    renderDashboard();
    expect(screen.getByText("Today's Follow-ups")).toBeInTheDocument();
    expect(screen.getByText("No open follow-ups are due today.")).toBeInTheDocument();
    expect(screen.getByText("No quotations have been sent yet.")).toBeInTheDocument();
  });

  it("advances stepper to Sent after sending quotation", async () => {
    renderDashboard();
    await runThroughValidation();
    fireEvent.click(screen.getByRole("button", { name: "Accept Recommendation" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Quotation" }));
    await screen.findByRole("button", { name: "Approve Quotation" });
    fireEvent.click(screen.getByRole("button", { name: "Approve Quotation" }));
    await screen.findByRole("button", { name: "Send to Customer" });
    fireEvent.click(screen.getByRole("button", { name: "Send to Customer" }));

    await waitFor(() => {
      const currentStep = document.querySelector(".sales-step-current .sales-step-label");
      expect(currentStep).toHaveTextContent("Sent");
    });
  });

  it("displays follow-ups and marks one complete", async () => {
    mockFetchFollowUps.mockImplementation((params?: { sent_only?: boolean }) => {
      if (params?.sent_only) {
        return Promise.resolve({ items: [followUpItem], total: 1 });
      }
      return Promise.resolve({ items: [followUpItem], total: 1 });
    });

    renderDashboard();
    await waitFor(() => {
      expect(screen.getAllByText("Q-2026-0001").length).toBeGreaterThan(0);
    });
    expect(screen.getByRole("button", { name: "Contact Today" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Contact Today" }));
    await waitFor(() => {
      expect(mockUpdateFollowUp).toHaveBeenCalledWith("fu-1", { status: "COMPLETED" });
    });
  });

  it("shows validation error when validate products fails", async () => {
    mockValidateProducts.mockRejectedValue(new Error("Validation service unavailable"));

    renderDashboard();
    fireEvent.change(screen.getByLabelText("Customer RFQ"), { target: { value: "RFQ" } });
    fireEvent.click(screen.getByRole("button", { name: "Extract Requirements" }));
    await screen.findByRole("button", { name: "Validate Products" });
    fireEvent.click(screen.getByRole("button", { name: "Validate Products" }));

    await waitFor(() => {
      expect(
        screen.getByText(/Technical validation could not be completed/i),
      ).toBeInTheDocument();
    });
  });

  it("shows send quotation error without crashing", async () => {
    mockSendQuotation.mockRejectedValue(new Error("QUOTATION_ALREADY_SENT"));

    renderDashboard();
    await runThroughValidation();
    fireEvent.click(screen.getByRole("button", { name: "Accept Recommendation" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Quotation" }));
    await screen.findByRole("button", { name: "Approve Quotation" });
    fireEvent.click(screen.getByRole("button", { name: "Approve Quotation" }));
    await screen.findByRole("button", { name: "Send to Customer" });
    fireEvent.click(screen.getByRole("button", { name: "Send to Customer" }));

    await waitFor(() => {
      expect(screen.getByText(/QUOTATION_ALREADY_SENT/i)).toBeInTheDocument();
    });
  });

  it("disables extract when RFQ textarea is empty", () => {
    renderDashboard();
    expect(screen.getByRole("button", { name: "Extract Requirements" })).toBeDisabled();
  });

  it("shows quotation validation unknown errors", async () => {
    mockCreateQuotation.mockRejectedValue(
      new ApiError(
        "Product has unresolved technical requirements and cannot be quoted as compliant.",
        422,
        "QUOTATION_VALIDATION_UNKNOWN",
      ),
    );

    renderDashboard();
    await runThroughValidation();
    fireEvent.click(screen.getByRole("button", { name: "Accept Recommendation" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Quotation" }));

    await waitFor(() => {
      expect(screen.getByText(/technical validation is incomplete/i)).toBeInTheDocument();
    });
  });
});
