"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Warranty {
  id: string;
  title: string;
  duration_months: number;
  start_date: string;
  expiry_date: string;
  status: "ACTIVE" | "EXPIRING_SOON" | "EXPIRED" | "UNKNOWN";
  notes?: string;
  created_at: string;
}

export default function WarrantiesPage() {
  const [warranties, setWarranties] = useState<Warranty[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("ALL");
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // New warranty form state
  const [newTitle, setNewTitle] = useState("");
  const [newDuration, setNewDuration] = useState("12");
  const [newStartDate, setNewStartDate] = useState("");
  const [newNotes, setNewNotes] = useState("");

  const fetchWarranties = async () => {
    setLoading(true);
    setError(null);
    try {
      const statusParam = filter === "ALL" ? undefined : filter;
      const res = await api.getWarranties(statusParam);
      setWarranties(Array.isArray(res) ? res : (res?.items || []));
    } catch (err: any) {
      setError(err.message || "Failed to load warranties");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setNewStartDate(new Date().toISOString().split("T")[0]);
  }, []);

  useEffect(() => {
    fetchWarranties();
  }, [filter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.createWarranty({
        title: newTitle,
        duration_months: parseInt(newDuration, 10),
        start_date: newStartDate,
        notes: newNotes || undefined,
      });
      setShowAddModal(false);
      setNewTitle("");
      setNewNotes("");
      fetchWarranties();
    } catch (err: any) {
      alert(err.message || "Failed to add warranty");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this warranty?")) return;
    try {
      await api.deleteWarranty(id);
      fetchWarranties();
    } catch (err: any) {
      alert(err.message || "Failed to delete warranty");
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "ACTIVE":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            Active
          </span>
        );
      case "EXPIRING_SOON":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 animate-pulse">
            Expiring Soon
          </span>
        );
      case "EXPIRED":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">
            Expired
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

  const getDaysRemaining = (expiryDate: string) => {
    const expiry = new Date(expiryDate);
    const today = new Date();
    const diffTime = expiry.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return `${Math.abs(diffDays)} days ago`;
    }
    if (diffDays === 0) return "Expires today";
    return `${diffDays} days left`;
  };

  return (
    <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Warranties Vault</h1>
          <p className="text-sm text-slate-500">Track coverage periods, policy terms, and expiration alerts.</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition flex items-center gap-2"
        >
          <span>+</span>
          <span>Add Warranty</span>
        </button>
      </div>

      {/* Filter Pills */}
      <div className="flex gap-2">
        {[
          { label: "All Warranties", value: "ALL" },
          { label: "Active", value: "ACTIVE" },
          { label: "Expiring Soon (30d)", value: "EXPIRING_SOON" },
          { label: "Expired", value: "EXPIRED" },
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

      {/* Warranties Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-500">Loading warranties...</div>
      ) : warranties.length === 0 ? (
        <div className="p-12 bg-white rounded-xl border border-slate-200 text-center">
          <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h3 className="text-base font-semibold text-slate-800">No warranties found</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
            Keep manufacturer guarantees organized. Add a warranty manually or link one from your purchases.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition"
          >
            Track First Warranty
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {warranties.map((w) => (
            <div
              key={w.id}
              className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <h3 className="text-base font-semibold text-slate-900 line-clamp-1">
                    {w.title}
                  </h3>
                  {getStatusBadge(w.status)}
                </div>

                <div className="space-y-2 text-xs text-slate-600 mb-4">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Duration:</span>
                    <span className="font-medium text-slate-700">{w.duration_months} Months</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Start Date:</span>
                    <span>{new Date(w.start_date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Expires:</span>
                    <span className="font-semibold text-slate-800">
                      {new Date(w.expiry_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Remaining:</span>
                    <span className="font-medium text-indigo-600">
                      {getDaysRemaining(w.expiry_date)}
                    </span>
                  </div>
                  {w.notes && (
                    <p className="mt-2 text-slate-500 italic border-t border-slate-100 pt-2">
                      &ldquo;{w.notes}&rdquo;
                    </p>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end">
                <button
                  onClick={() => handleDelete(w.id)}
                  className="text-xs font-medium text-rose-600 hover:text-rose-800 transition"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Warranty Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-800">Track New Warranty</h2>
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
                  Product / Item Title *
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. MacBook Pro M3"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Coverage (Months) *
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={newDuration}
                    onChange={(e) => setNewDuration(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Purchase / Start Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={newStartDate}
                    onChange={(e) => setNewStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Notes / Policy ID
                </label>
                <textarea
                  rows={2}
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  placeholder="e.g. AppleCare+ Agreement #12345"
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
                  {submitting ? "Saving..." : "Save Warranty"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
