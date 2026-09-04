import type { ReactNode } from "react";

export function StatusBanner({
  tone,
  children,
}: {
  tone: "error" | "info";
  children: ReactNode;
}) {
  return <div className={`banner banner-${tone}`}>{children}</div>;
}
