import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SLA Dashboard — Injani Systems",
  description: "Injani Systems — Approval Workflow Performance Monitor",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0 }}>{children}</body>
    </html>
  );
}
