import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Análisis IMSS",
  description: "Sistema de análisis de constancias IMSS",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
