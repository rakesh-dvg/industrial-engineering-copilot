import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

import {
  fetchFollowUps,
  priorityLabel,
  updateFollowUp,
  type FollowUpPriority,
  type SalesFollowUp,
} from "../../api/followups";
import { formatMoney, statusClassName } from "./formatters";

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleDateString();
}

const PRIORITY_ORDER: Record<FollowUpPriority, number> = {
  P0: 0,
  P1: 1,
  P2: 2,
};

function sortFollowUps(items: SalesFollowUp[]): SalesFollowUp[] {
  return [...items].sort((left, right) => {
    const priorityDiff = PRIORITY_ORDER[left.priority] - PRIORITY_ORDER[right.priority];
    if (priorityDiff !== 0) {
      return priorityDiff;
    }
    return left.customer_name.localeCompare(right.customer_name);
  });
}

function priorityClassName(priority: FollowUpPriority): string {
  if (priority === "P0") {
    return "follow-up-priority follow-up-priority-p0";
  }
  if (priority === "P1") {
    return "follow-up-priority follow-up-priority-p1";
  }
  return "follow-up-priority follow-up-priority-p2";
}

export function FollowUpPanels() {
  const queryClient = useQueryClient();
  const today = todayIsoDate();

  const todayQuery = useQuery({
    queryKey: ["follow-ups", "today", today],
    queryFn: () => fetchFollowUps({ status: "OPEN", due_date: today }),
  });

  const sentQuery = useQuery({
    queryKey: ["follow-ups", "sent"],
    queryFn: () => fetchFollowUps({ sent_only: true }),
  });

  const updateMutation = useMutation({
    mutationFn: ({
      followUpId,
      payload,
    }: {
      followUpId: string;
      payload: Parameters<typeof updateFollowUp>[1];
    }) => updateFollowUp(followUpId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["follow-ups"] });
    },
  });

  const openFollowUps = useMemo(
    () => sortFollowUps(todayQuery.data?.items ?? []),
    [todayQuery.data?.items],
  );

  const priorityCounts = useMemo(() => {
    const counts = { P0: 0, P1: 0, P2: 0 };
    for (const item of openFollowUps) {
      counts[item.priority] += 1;
    }
    return counts;
  }, [openFollowUps]);

  const openQuotationValue = useMemo(() => {
    return openFollowUps.reduce((sum, item) => sum + Number(item.quotation.total), 0);
  }, [openFollowUps]);

  const openCurrency = openFollowUps[0]?.quotation.currency ?? "USD";

  const renderPrioritySelect = (item: SalesFollowUp) => (
    <select
      aria-label={`Priority for ${item.customer_name}`}
      value={item.priority}
      onChange={(event) =>
        updateMutation.mutate({
          followUpId: item.id,
          payload: { priority: event.target.value as FollowUpPriority },
        })
      }
    >
      <option value="P0">P0 — Immediate</option>
      <option value="P1">P1 — Important</option>
      <option value="P2">P2 — Normal</option>
    </select>
  );

  return (
    <>
      <section className="card sales-panel sales-panel-wide follow-ups-panel">
        <p className="follow-ups-eyebrow">TODAY&apos;S SALES FOLLOW-UPS</p>
        <h3>Today&apos;s Follow-ups</h3>
        <p className="follow-ups-headline">
          {openFollowUps.length} Customer{openFollowUps.length === 1 ? "" : "s"} Need Attention
          Today
        </p>
        <p className="catalog-meta follow-ups-demo-note">
          Demo/historical sales opportunities — not real CRM records. Priorities are sales labels,
          not AI predictions.
        </p>
        {openFollowUps.length ? (
          <>
            <div className="follow-ups-kpi-row">
              <span>
                Today&apos;s Follow-ups: <strong>{openFollowUps.length}</strong>
              </span>
              <span>
                P0: <strong>{priorityCounts.P0}</strong>
              </span>
              <span>
                P1: <strong>{priorityCounts.P1}</strong>
              </span>
              <span>
                P2: <strong>{priorityCounts.P2}</strong>
              </span>
              <span>
                Open Quotation Value:{" "}
                <strong>{formatMoney(String(openQuotationValue.toFixed(2)), openCurrency)}</strong>
              </span>
            </div>
            <ul className="follow-ups-opportunity-list">
              {openFollowUps.map((item) => (
                <li key={item.id} className="follow-up-opportunity">
                  <div className="follow-up-opportunity-header">
                    <span className={priorityClassName(item.priority)}>{item.priority}</span>
                    <strong>{item.customer_name}</strong>
                    <span className={statusClassName(item.status)}>{item.status}</span>
                  </div>
                  <p className="follow-up-opportunity-detail">
                    {item.quotation_number} ·{" "}
                    {formatMoney(item.quotation.total, item.quotation.currency)}
                  </p>
                  <div className="follow-up-opportunity-actions">
                    {renderPrioritySelect(item)}
                    <button
                      type="button"
                      className="btn-secondary follow-up-action"
                      onClick={() =>
                        updateMutation.mutate({
                          followUpId: item.id,
                          payload: { status: "COMPLETED" },
                        })
                      }
                    >
                      Contact Today
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className="catalog-meta">No open follow-ups are due today.</p>
        )}
      </section>

      <section className="card sales-panel sales-panel-wide">
        <h3>Sent Quotations</h3>
        {sentQuery.data?.items.length ? (
          <table className="sales-table">
            <thead>
              <tr>
                <th scope="col">Customer</th>
                <th scope="col">Quotation</th>
                <th scope="col">Amount</th>
                <th scope="col">Sent</th>
                <th scope="col">Follow-up</th>
                <th scope="col">Priority</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {sentQuery.data.items.map((item) => (
                <tr key={item.id}>
                  <td>{item.customer_name}</td>
                  <td>{item.quotation_number}</td>
                  <td>{formatMoney(item.quotation.total, item.quotation.currency)}</td>
                  <td>{formatDate(item.quotation.sent_at)}</td>
                  <td>{item.follow_up_date}</td>
                  <td>{priorityLabel(item.priority)}</td>
                  <td>{item.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="catalog-meta">No quotations have been sent yet.</p>
        )}
      </section>
    </>
  );
}
