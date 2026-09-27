import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import {
  createQuotationCommunication,
  sendQuotationToCustomer,
  updateQuotationCommunication,
  type QuotationCommunication,
} from "../../api/communication";
import type { Quotation } from "../../api/quotations";
import { formatMoney } from "./formatters";

export function CustomerCommunicationPanel({
  quotation,
  customerEmail,
  onCustomerEmailChange,
  communication,
  onCommunicationChange,
  onQuotationSent,
  onQuotationUpdate,
  onStepChange,
}: {
  quotation: Quotation;
  customerEmail: string;
  onCustomerEmailChange: (value: string) => void;
  communication: QuotationCommunication | null;
  onCommunicationChange: (value: QuotationCommunication | null) => void;
  onQuotationSent: (quotation: Quotation, communication: QuotationCommunication) => void;
  onQuotationUpdate?: (quotation: Quotation) => void;
  onStepChange: (step: "communication" | "sent") => void;
}) {
  const [subject, setSubject] = useState(communication?.subject ?? "");
  const [body, setBody] = useState(communication?.body ?? "");
  const [sendDetail, setSendDetail] = useState<string | null>(null);

  useEffect(() => {
    if (communication) {
      setSubject(communication.subject);
      setBody(communication.body);
    }
  }, [communication]);

  const createMutation = useMutation({
    mutationFn: () =>
      createQuotationCommunication(quotation.id, { customer_email: customerEmail }),
    onSuccess: (data) => {
      onCommunicationChange(data);
      setSubject(data.subject);
      setBody(data.body);
      onStepChange("communication");
    },
  });

  const saveMutation = useMutation({
    mutationFn: () =>
      updateQuotationCommunication(quotation.id, {
        customer_email: customerEmail,
        subject,
        body,
        status: "DRAFT",
      }),
    onSuccess: (data) => onCommunicationChange(data),
  });

  const readyMutation = useMutation({
    mutationFn: () =>
      updateQuotationCommunication(quotation.id, {
        customer_email: customerEmail,
        subject,
        body,
        status: "READY_TO_SEND",
      }),
    onSuccess: (data) => {
      onCommunicationChange(data);
      onQuotationUpdate?.({ ...quotation, status: "READY_TO_SEND" });
    },
  });

  const sendMutation = useMutation({
    mutationFn: () => sendQuotationToCustomer(quotation.id),
    onSuccess: (data) => {
      onCommunicationChange(data.communication);
      setSendDetail(data.send_detail);
      onQuotationSent(
        { ...quotation, status: "SENT", customer_email: data.communication.customer_email },
        data.communication,
      );
      onStepChange("sent");
    },
  });

  const isApproved =
    quotation.status === "APPROVED" ||
    quotation.status === "READY_TO_SEND" ||
    quotation.status === "SENT";
  const isSent = quotation.status === "SENT" || communication?.status === "SENT";

  if (!isApproved) {
    return null;
  }

  return (
    <section className="card sales-panel sales-panel-wide communication-panel">
      <h3>8. Customer Communication</h3>
      <p className="demo-customer-badge" role="status">
        DEMO CUSTOMER — No external email will be sent
      </p>
      <p className="catalog-meta">
        Quotation {quotation.quotation_number} · {quotation.customer_name} ·{" "}
        {formatMoney(quotation.total, quotation.currency)}
      </p>
      <p className="quotation-status-banner">
        Status: {quotation.status}
        {communication ? ` · Email ${communication.status}` : ""}
      </p>

      {!communication ? (
        <button
          type="button"
          className="rfq-submit"
          disabled={createMutation.isPending || customerEmail.trim().length === 0}
          onClick={() => createMutation.mutate()}
        >
          {createMutation.isPending ? "Preparing…" : "Prepare Customer Email"}
        </button>
      ) : (
        <>
          <div className="communication-form-grid">
            <label htmlFor="comm-recipient">To</label>
            <input
              id="comm-recipient"
              value={customerEmail}
              onChange={(event) => onCustomerEmailChange(event.target.value)}
              readOnly={isSent}
            />
            <label htmlFor="comm-subject">Subject</label>
            <input
              id="comm-subject"
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              readOnly={isSent}
            />
            <label htmlFor="comm-body">Email Body</label>
            <textarea
              id="comm-body"
              className="rfq-textarea"
              rows={12}
              value={body}
              onChange={(event) => setBody(event.target.value)}
              readOnly={isSent}
            />
          </div>

          <p className="catalog-meta">
            Attachment: {quotation.quotation_number}.pdf (quotation details included in email body)
          </p>

          {!isSent ? (
            <div className="sales-actions">
              <button
                type="button"
                className="btn-secondary"
                disabled={saveMutation.isPending}
                onClick={() => saveMutation.mutate()}
              >
                {saveMutation.isPending ? "Saving…" : "Save Draft"}
              </button>
              <button
                type="button"
                className="btn-secondary"
                disabled={readyMutation.isPending}
                onClick={() => readyMutation.mutate()}
              >
                {readyMutation.isPending ? "Updating…" : "Mark Ready to Send"}
              </button>
              <button
                type="button"
                className="rfq-submit"
                disabled={sendMutation.isPending}
                onClick={() => sendMutation.mutate()}
              >
                {sendMutation.isPending ? "Sending…" : "Send to Customer"}
              </button>
            </div>
          ) : (
            <div className="send-confirmation">
              <p className={communication.demo_mode ? "sales-alert" : "status-pass"}>
                {communication.demo_mode
                  ? "Demo mode: quotation recorded as sent. No external email was delivered."
                  : "Quotation sent to customer."}
              </p>
              <p>
                <strong>Sent to:</strong> {communication.customer_email}
              </p>
              <p>
                <strong>Sent at:</strong>{" "}
                {communication.sent_at
                  ? new Date(communication.sent_at).toLocaleString()
                  : "—"}
              </p>
              {sendDetail ? <p className="catalog-meta">{sendDetail}</p> : null}
            </div>
          )}

          {sendMutation.isError ? (
            <p role="alert" className="status-unavailable">
              {(sendMutation.error as Error).message}
            </p>
          ) : null}
        </>
      )}
    </section>
  );
}
