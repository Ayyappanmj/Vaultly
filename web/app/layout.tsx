import type { Metadata } from "next";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vaultly — Smart Receipt, Warranty & Subscription Vault",
  description: "Companion web dashboard for Vaultly",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased bg-slate-50 text-slate-900">
      <body className="min-h-full flex flex-col font-sans">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 flex flex-col min-w-0 bg-slate-50">{children}</main>
        </div>
      </body>
    </html>
  );
}
