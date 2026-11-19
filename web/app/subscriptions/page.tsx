"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Subscription {
  id: string;
  name: string;
  amount: number | string;
  currency: string;
  billing_frequency: "weekly" | "monthly" | "quarterly" | "half_yearly" | "yearly" | "custom";
  status: "active" | "paused" | "cancelled" | "trial";
  next_billing_date: string;
  monthly_equivalent?: number | string;
  annual_equivalent?: number | string;
  notes?: string;
}

interface Analytics {
  total_monthly_spend: number | string;
  total_annual_spend: number | string;
  active_subscriptions_count: number;
}

export default function SubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("ALL");
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // New subscription form
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [frequency, setFrequency] = useState<string>("monthly");
  const [nextBillingDate, setNextBillingDate] = useState("");
  const [notes, setNotes] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [subRes, anaRes] = await Promise.all([
        api.getSubscriptions(filter === "ALL" ? undefined : filter),
        api.getSubscriptionAnalytics(),
      ]);
      setSubscriptions(Array.isArray(subRes) ? subRes : (subRes?.items || []));
      setAnalytics(anaRes);
    } catch (err: any) {
      setError(err.message || "Failed to load subscriptions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setNextBillingDate(new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0]);
  }, []);

  useEffect(() => {
    fetchData();
  }, [filter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.createSubscription({
        name,
        amount: parseFloat(amount),
        currency,
        billing_frequency: frequency,
        next_billing_date: nextBillingDate,
        notes: notes || undefined,
      });
      setShowAddModal(false);
      setName("");
      setAmount("");
      setNotes("");
      fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to add subscription");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async (id: string, currentStatus: string) => {
    if (currentStatus === "cancelled") return;
    if (!confirm("Are you sure you want to mark this subscription as cancelled?")) return;
    try {
      await api.cancelSubscription(id);
      fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to cancel subscription");
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            Active
          </span>
        );
      case "trial":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
            Free Trial
          </span>
        );
      case "paused":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
            Paused
          </span>
        );
      case "cancelled":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">
            Cancelled
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Subscriptions Manager</h1>
          <p className="text-sm text-slate-500">Track recurring commitments, renewals, and annualized spend.</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition flex items-center gap-2"
        >
          <span>+</span>
          <span>Add Subscription</span>
        </button>
      </div>

      {/* Analytics Summary */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-semibold text-slate-500 uppercase">Monthly Burn Rate</span>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              ${Number(analytics.total_monthly_spend || 0).toFixed(2)}
              <span className="text-xs text-slate-500 font-normal ml-1">/ mo</span>
            </div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-semibold text-slate-500 uppercase">Annualized Projected Spend</span>
            <div className="text-2xl font-bold text-slate-900 mt-2">
              ${Number(analytics.total_annual_spend || 0).toFixed(2)}
              <span className="text-xs text-slate-500 font-normal ml-1">/ yr</span>
            </div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-semibold text-slate-500 uppercase">Active Subscriptions</span>
            <div className="text-2xl font-bold text-indigo-600 mt-2">
              {analytics.active_subscriptions_count || 0}
            </div>
          </div>
        </div>
      )}

      {/* Filter Pills */}
      <div className="flex gap-2">
        {[
          { label: "All", value: "ALL" },
          { label: "Active", value: "active" },
          { label: "Trials", value: "trial" },
          { label: "Paused", value: "paused" },
          { label: "Cancelled", value: "cancelled" },
        ].map((tab) => (
          <button
            key={tab.value}
            onClick={() => setFilter(tab.value)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
              filter === tab.value
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-100"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700">
          {error}
        </div>
      )}

      {/* Subscriptions Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">Loading subscriptions...</div>
        ) : subscriptions.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-slate-500 text-sm">No subscriptions tracked yet.</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="mt-3 px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition"
            >
              Add Your First Subscription
            </button>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-200 text-slate-500 font-semibold text-xs uppercase tracking-wider">
                <th className="py-3 px-6">Service Name</th>
                <th className="py-3 px-6">Billing Cycle</th>
                <th className="py-3 px-6">Cost</th>
                <th className="py-3 px-6">Monthly Equiv.</th>
                <th className="py-3 px-6">Next Renewal</th>
                <th className="py-3 px-6">Status</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {subscriptions.map((sub) => (
                <tr key={sub.id} className="hover:bg-slate-50/60 transition">
                  <td className="py-4 px-6 font-semibold text-slate-900">
                    {sub.name}
                    {sub.notes && (
                      <span className="block text-xs font-normal text-slate-400">
                        {sub.notes}
                      </span>
                    )}
                  </td>
                  <td className="py-4 px-6 capitalize text-slate-600">
                    {sub.billing_frequency.replace("_", " ")}
                  </td>
                  <td className="py-4 px-6 font-semibold text-slate-900">
                    ${Number(sub.amount).toFixed(2)}{" "}
                    <span className="text-xs text-slate-400">{sub.currency}</span>
                  </td>
                  <td className="py-4 px-6 text-slate-600">
                    ${Number(sub.monthly_equivalent || sub.amount).toFixed(2)}/mo
                  </td>
                  <td className="py-4 px-6 text-slate-700">
                    {new Date(sub.next_billing_date).toLocaleDateString()}
                  </td>
                  <td className="py-4 px-6">{getStatusBadge(sub.status)}</td>
                  <td className="py-4 px-6 text-right space-x-3">
                    {sub.status !== "cancelled" && (
                      <button
                        onClick={() => handleCancel(sub.id, sub.status)}
                        className="text-xs font-medium text-rose-600 hover:text-rose-800 transition"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-800">Add Subscription</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Service Name *
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Netflix, Spotify, GitHub Pro"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Billing Amount *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="15.99"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Currency
                  </label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                    <option value="INR">INR (₹)</option>
                    <option value="CAD">CAD ($)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Frequency *
                  </label>
                  <select
                    value={frequency}
                    onChange={(e) => setFrequency(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="half_yearly">Semi-Annual</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Next Renewal *
                  </label>
                  <input
                    type="date"
                    required
                    value={nextBillingDate}
                    onChange={(e) => setNextBillingDate(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Notes
                </label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Shared with roommate; billed to Visa *4242"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition disabled:opacity-50"
                >
                  {submitting ? "Saving..." : "Save Subscription"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
