export type SalesWorkflowStep =
  | "rfq"
  | "requirements"
  | "validation"
  | "recommendation"
  | "decision"
  | "quotation"
  | "approval"
  | "communication"
  | "sent"
  | "followup";

const STEPS: Array<{ id: SalesWorkflowStep; label: string }> = [
  { id: "rfq", label: "RFQ" },
  { id: "requirements", label: "Requirements" },
  { id: "validation", label: "Validation" },
  { id: "recommendation", label: "Recommendation" },
  { id: "decision", label: "Sales Decision" },
  { id: "quotation", label: "Quotation" },
  { id: "approval", label: "Review & Approve" },
  { id: "communication", label: "Customer Email" },
  { id: "sent", label: "Sent" },
  { id: "followup", label: "Follow-up" },
];

function stepIndex(step: SalesWorkflowStep): number {
  return STEPS.findIndex((item) => item.id === step);
}

export function SalesWorkflowStepper({
  currentStep,
  completedThrough,
}: {
  currentStep: SalesWorkflowStep;
  completedThrough: SalesWorkflowStep | null;
}) {
  const currentIndex = stepIndex(currentStep);
  const completedIndex = completedThrough ? stepIndex(completedThrough) : -1;

  return (
    <ol className="sales-stepper sales-stepper-expanded" aria-label="Sales workflow">
      {STEPS.map((step, index) => {
        const isComplete = index <= completedIndex;
        const isCurrent = index === currentIndex;
        const isLocked = index > currentIndex && !isComplete;
        return (
          <li
            key={step.id}
            className={[
              "sales-step",
              isComplete ? "sales-step-complete" : "",
              isCurrent ? "sales-step-current" : "",
              isLocked ? "sales-step-locked" : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <span className="sales-step-index">{index + 1}</span>
            <span className="sales-step-label">{step.label}</span>
          </li>
        );
      })}
    </ol>
  );
}
