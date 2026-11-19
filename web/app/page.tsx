"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function DashboardOverviewPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<{ full_name: string; email: string } | null>(null);
  const [receipts, setReceipts] = useState<any[]>([]);
  const [warranties, setWarranties] = useState<any[]>([]);
  const [subAnalytics, setSubAnalytics] = useState<any | null>(null);
  const [notifications, setNotifications] = useState<any[]>([]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const me = await api.getMe();
      setUser(me);

      const [rData, wData, sData, nData] = await Promise.all([
        api.getReceipts({ page: 1 }),
        api.getWarranties(),
        api.getSubscriptionAnalytics().catch(() => null),
        api.getNotifications(true).catch(() => ({ items: [] })),
      ]);

      setReceipts(rData.items || []);
      setWarranties(wData.items || []);
      setSubAnalytics(sData);
      setNotifications(nData.items || []);
    } catch {
      router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const expiringWarranties = warranties.filter((w) => w.status === "EXPIRING_SOON");
  const totalReceiptsSpend = receipts.reduce((sum, r) => sum + Number(r.total_amount || 0), 0);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-12">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-medium text-slate-500">Loading your vault overview...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Welcome back, {user?.full_name || "Vaultly User"}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Overview of your receipts, warranties, and subscription commitments.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/receipts"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-sm shadow-sm transition-colors flex items-center gap-2"
          >
            <span>+</span>
            <span>Add Receipt</span>
          </Link>
          <a
            href={api.getExportPdfUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 font-medium rounded-lg text-sm border border-slate-300 shadow-sm transition-colors"
          >
            Export PDF Report
          </a>
        </div>
      </div>

      {/* Critical Alerts Banner */}
      {notifications.length > 0 && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-800 flex items-center gap-1.5">
              <span>⚠️</span> Vault Reminders ({notifications.length} pending)
            </span>
            <Link href="/notifications" className="text-xs font-semibold text-amber-900 hover:underline">
              View All
            </Link>
          </div>
          <p className="text-sm text-amber-900">
            {notifications[0].title}: {notifications[0].message}
          </p>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Monthly Subscriptions</p>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-slate-900">
              ${Number(subAnalytics?.total_monthly_spend || 0).toFixed(2)}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-medium">
              {subAnalytics?.total_active_count || 0} active
            </span>
          </div>
          <p className="text-xs text-slate-400">
            ${Number(subAnalytics?.total_annual_spend || 0).toFixed(2)} normalized/year
          </p>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Warranties</p>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-slate-900">
              {warranties.filter((w) => w.status === "ACTIVE").length}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">
              Protected
            </span>
          </div>
          <p className="text-xs text-slate-400">{warranties.length} total registered</p>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Expiring Soon</p>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-amber-600">{expiringWarranties.length}</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-medium">
              Next 30 days
            </span>
          </div>
          <p className="text-xs text-slate-400">Action recommended</p>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Vaulted Receipts</p>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-slate-900">${Number(totalReceiptsSpend || 0).toFixed(2)}</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium">
              {receipts.length} items
            </span>
          </div>
          <p className="text-xs text-slate-400">Tracked & organized</p>
        </div>
      </div>

      {/* Recent Receipts Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Recent Receipts</h2>
            <p className="text-xs text-slate-500">Your latest logged receipts and OCR scans.</p>
          </div>
          <Link href="/receipts" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">
            View All Vault &rarr;
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-200">
              <tr>
                <th className="px-5 py-3.5">Merchant</th>
                <th className="px-5 py-3.5">Date</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5">Category</th>
                <th className="px-5 py-3.5 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {receipts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-slate-400 text-sm">
                    No receipts vaulted yet. Click &quot;Add Receipt&quot; to begin.
                  </td>
                </tr>
              ) : (
                receipts.slice(0, 5).map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-medium text-slate-900">{r.merchant_name}</td>
                    <td className="px-5 py-3.5 text-slate-500">
                      {new Date(r.purchase_date).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          r.status === "CONFIRMED"
                            ? "bg-emerald-50 text-emerald-700"
                            : r.status === "DUPLICATE_WARNING"
                            ? "bg-amber-50 text-amber-700"
                            : "bg-blue-50 text-blue-700"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-slate-600">
                      {r.category?.name || "General"}
                    </td>
                    <td className="px-5 py-3.5 text-right font-semibold text-slate-900">
                      {r.currency} {Number(r.total_amount).toFixed(2)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
