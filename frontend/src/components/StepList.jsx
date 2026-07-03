import { useState, useEffect } from "react";

export default function StepList({ steps, collapsed }) {
  const [spinnerFrame, setSpinnerFrame] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setSpinnerFrame((f) => (f + 1) % 4);
    }, 250);
    return () => clearInterval(interval);
  }, []);

  if (!steps || steps.length === 0) return null;

  const spinner = ["/", "-", "\\", "|"][spinnerFrame];

  return (
    <div
      className={`flex flex-col gap-2 font-mono text-[11px] transition-all duration-500 ease-in-out origin-top ${
        collapsed
          ? "opacity-0 max-h-0 overflow-hidden pointer-events-none my-0"
          : "opacity-100 max-h-[500px] my-4"
      }`}
    >
      {steps.map((step, idx) => {
        let icon = "○";
        let iconColor = "text-[var(--muted-foreground)] opacity-40";
        let textColor = "text-[var(--muted-foreground)] opacity-60";

        if (step.status === "active") {
          icon = spinner;
          iconColor = "text-[var(--foreground)] font-bold";
          textColor = "text-[var(--foreground)] font-medium";
        } else if (step.status === "complete") {
          icon = "✓";
          iconColor = "text-[var(--foreground)] font-bold";
          textColor = "text-[var(--muted-foreground)]";
        }

        return (
          <div key={idx} className="flex items-center gap-2.5">
            <span className={`w-3 text-center select-none font-mono ${iconColor}`}>
              {icon}
            </span>
            <span className={`font-mono tracking-tight ${textColor}`}>
              {step.message}
            </span>
          </div>
        );
      })}
    </div>
  );
}
