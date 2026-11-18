"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/", icon: "📊" },
  { label: "Receipts Vault", href: "/receipts", icon: "🧾" },
  { label: "Warranties", href: "/warranties", icon: "🛡️" },
  { label: "Subscriptions", href: "/subscriptions", icon: "🔄" },
  { label: "Household Splits", href: "/splits", icon: "👥" },
  { label: "Notifications", href: "/notifications", icon: "🔔" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  // Do not show sidebar on login or register pages
  if (pathname === "/login" || pathname === "/register") {
    return null;
  }

  const handleLogout = () => {
    api.clearToken();
    router.push("/login");
  };

  return (
    <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col min-h-screen border-r border-slate-800 shrink-0">
      <div className="p-6 border-b border-slate-800">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg">
            V
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight">Vaultly</h1>
            <p className="text-xs text-slate-400">Smart Asset Vault</p>
          </div>
        </Link>
      </div>

      <nav className="flex-1 p-4 space-y-1.5">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-rose-900/40 hover:text-rose-300 transition-colors"
        >
          <span>🚪</span>
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
