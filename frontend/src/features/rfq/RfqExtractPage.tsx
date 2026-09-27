import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { extractRfq, type RfqExtractResponse } from "../../api/rfq";

const EXAMPLE_RFQ = `Customer: ABC Manufacturing

Please quote 10 industrial Ethernet switches.

Requirements:
- 24 VDC power
- minimum 5 Ethernet ports
- DIN rail mounting
- Modbus TCP support
- operating temperature down to -20°C`;

function formatValue(value: RfqExtractResponse["requirements"][number]["value"]): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  return String(value);
}

export function RfqExtractPage() {
  const [rawText, setRawText] = useState(EXAMPLE_RFQ);
  const mutation = useMutation({
    mutationFn: extractRfq,
  });

  return (
    <section aria-labelledby="rfq-heading">
      <h2 id="rfq-heading">RFQ Extraction</h2>
      <p>Paste customer RFQ text and extract structured engineering requirements with Groq.</p>

      <label className="rfq-label" htmlFor="rfq-text">
        RFQ text
      </label>
      <textarea
        id="rfq-text"
        className="rfq-textarea"
        rows={12}
        value={rawText}
        onChange={(event) => setRawText(event.target.value)}
      />

      <button
        type="button"
        className="rfq-submit"
        disabled={mutation.isPending || rawText.trim().length === 0}
        onClick={() => mutation.mutate(rawText)}
      >
        {mutation.isPending ? "Extracting…" : "Extract Requirements"}
      </button>

      {mutation.isError ? (
        <p role="alert" className="status-unavailable">
          {(mutation.error as Error).message}
        </p>
      ) : null}

      {mutation.data ? (
        <div className="card rfq-results">
          <h3>Structured Requirements</h3>
          {mutation.data.customer_name ? (
            <p>
              <strong>Customer:</strong> {mutation.data.customer_name}
            </p>
          ) : null}
          {mutation.data.quantity != null ? (
            <p>
              <strong>Quantity:</strong> {mutation.data.quantity}
            </p>
          ) : null}

          {mutation.data.requirements.length > 0 ? (
            <ul className="rfq-requirements">
              {mutation.data.requirements.map((req) => (
                <li key={`${req.spec_key}-${req.operator}-${req.source_text ?? ""}`}>
                  <strong>{req.spec_key}</strong> {req.operator} {formatValue(req.value)}
                  {req.unit ? ` ${req.unit}` : ""}
                  {req.source_text ? <div className="catalog-meta">Source: {req.source_text}</div> : null}
                </li>
              ))}
            </ul>
          ) : (
            <p>No structured requirements extracted.</p>
          )}

          {mutation.data.ambiguous_notes.length > 0 ? (
            <>
              <h4>Ambiguous Notes</h4>
              <ul className="rfq-requirements">
                {mutation.data.ambiguous_notes.map((note) => (
                  <li key={note.source_text}>
                    {note.source_text}
                    {note.description ? <div className="catalog-meta">{note.description}</div> : null}
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
