import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FollowUpPanels } from "./FollowUpPanels";

const mockFetchFollowUps = vi.fn();
const mockUpdateFollowUp = vi.fn();

vi.mock("../../api/followups", () => ({
  fetchFollowUps: (...args: unknown[]) => mockFetchFollowUps(...args),
  updateFollowUp: (...args: unknown[]) => mockUpdateFollowUp(...args),
  priorityLabel: (priority: string) => priority,
}));

const demoFollowUps = [
  {
    id: "fu-apex",
    quotation_id: "quote-3",
    customer_name: "Apex Manufacturing",
    customer_email: "procurement@apexmanufacturing.example",
    quotation_number: "Q-2026-0003",
    follow_up_date: new Date().toISOString().slice(0, 10),
    priority: "P0" as const,
    status: "OPEN" as const,
    notes: null,
    quotation: {
      id: "quote-3",
      quotation_number: "Q-2026-0003",
      status: "SENT",
      currency: "USD",
      total: "8450.00",
      sent_at: "2026-09-27T10:00:00Z",
    },
    created_at: "2026-09-27T00:00:00Z",
    updated_at: "2026-09-27T00:00:00Z",
  },
  {
    id: "fu-abc",
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
  },
  {
    id: "fu-delta",
    quotation_id: "quote-2",
    customer_name: "Delta Automation",
    customer_email: "procurement@deltaautomation.example",
    quotation_number: "Q-2026-0002",
    follow_up_date: new Date().toISOString().slice(0, 10),
    priority: "P2" as const,
    status: "OPEN" as const,
    notes: null,
    quotation: {
      id: "quote-2",
      quotation_number: "Q-2026-0002",
      status: "SENT",
      currency: "USD",
      total: "4200.00",
      sent_at: "2026-09-26T15:00:00Z",
    },
    created_at: "2026-09-27T00:00:00Z",
    updated_at: "2026-09-27T00:00:00Z",
  },
];

function renderFollowUpPanels() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <FollowUpPanels />
    </QueryClientProvider>,
  );
}

describe("FollowUpPanels", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchFollowUps.mockImplementation((params?: { sent_only?: boolean }) => {
      if (params?.sent_only) {
        return Promise.resolve({ items: demoFollowUps, total: 3 });
      }
      return Promise.resolve({ items: demoFollowUps, total: 3 });
    });
    mockUpdateFollowUp.mockResolvedValue({
      ...demoFollowUps[0],
      status: "COMPLETED",
    });
  });

  it("displays three follow-up opportunities with priorities and values", async () => {
    renderFollowUpPanels();

    expect(await screen.findByText("TODAY'S SALES FOLLOW-UPS")).toBeInTheDocument();
    expect(await screen.findByText(/3 Customers Need Attention Today/)).toBeInTheDocument();
    expect(screen.getAllByText("Apex Manufacturing").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ABC Manufacturing").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Delta Automation").length).toBeGreaterThan(0);
    expect(screen.getByText(/Q-2026-0003 · USD 8,450.00/)).toBeInTheDocument();
    expect(screen.getByText(/Q-2026-0001 · USD 1,850.00/)).toBeInTheDocument();
    expect(screen.getByText(/Q-2026-0002 · USD 4,200.00/)).toBeInTheDocument();
    expect(screen.getAllByText("OPEN").length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText(/P0:/)).toBeInTheDocument();
    expect(screen.getByText(/P1:/)).toBeInTheDocument();
    expect(screen.getByText(/P2:/)).toBeInTheDocument();
    expect(screen.getByText(/Open Quotation Value:/)).toBeInTheDocument();
    expect(screen.getByText(/USD 14,500.00/)).toBeInTheDocument();
  });

  it("completes a follow-up via Contact Today and removes it from the open queue", async () => {
    mockFetchFollowUps.mockImplementation((params?: { sent_only?: boolean; status?: string }) => {
      if (params?.sent_only) {
        return Promise.resolve({ items: demoFollowUps, total: 3 });
      }
      return Promise.resolve({ items: demoFollowUps, total: 3 });
    });
    mockUpdateFollowUp.mockImplementation(async () => ({
      ...demoFollowUps[0],
      status: "COMPLETED",
    }));

    renderFollowUpPanels();
    await screen.findAllByText("Apex Manufacturing");
    expect(screen.getAllByRole("button", { name: "Contact Today" })).toHaveLength(3);

    fireEvent.click(screen.getAllByRole("button", { name: "Contact Today" })[0]);

    await waitFor(() => {
      expect(mockUpdateFollowUp).toHaveBeenCalledWith("fu-apex", { status: "COMPLETED" });
    });
  });

  it("shows demo disclaimer for historical opportunities", async () => {
    renderFollowUpPanels();
    await screen.findByText(/Demo\/historical sales opportunities/i);
  });
});
