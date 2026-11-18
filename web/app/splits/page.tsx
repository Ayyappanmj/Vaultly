"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Member {
  id: string;
  user_id: string;
  role: string;
  full_name?: string;
  email?: string;
}

interface Household {
  id: string;
  name: string;
  created_by: string;
  members: Member[];
}

interface MemberBalance {
  user_id: string;
  full_name: string;
  total_paid: number;
  total_owed: number;
  net_balance: number;
}

export default function SplitsPage() {
  const [households, setHouseholds] = useState<Household[]>([]);
  const [selectedHouseholdId, setSelectedHouseholdId] = useState<string>("");
  const [balances, setBalances] = useState<MemberBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showCreateHouseholdModal, setShowCreateHouseholdModal] = useState(false);
  const [newHouseholdName, setNewHouseholdName] = useState("");
  const [showAddExpenseModal, setShowAddExpenseModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Expense form
  const [expenseDesc, setExpenseDesc] = useState("");
  const [expenseAmount, setExpenseAmount] = useState("");
  const [currency, setCurrency] = useState("USD");

  const fetchHouseholds = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHouseholds();
      setHouseholds(data);
      if (data.length > 0 && !selectedHouseholdId) {
        setSelectedHouseholdId(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load households");
    } finally {
      setLoading(false);
    }
  };

  const fetchBalances = async (householdId: string) => {
    if (!householdId) return;
    try {
      const report = await api.getHouseholdBalances(householdId);
      setBalances(report.member_balances || []);
    } catch (err: any) {
      console.error("Failed to load balances", err);
    }
  };

  useEffect(() => {
    fetchHouseholds();
  }, []);

  useEffect(() => {
    if (selectedHouseholdId) {
      fetchBalances(selectedHouseholdId);
    }
  }, [selectedHouseholdId]);

  const handleCreateHousehold = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const created = await api.createHousehold(newHouseholdName);
      setNewHouseholdName("");
      setShowCreateHouseholdModal(false);
      await fetchHouseholds();
      setSelectedHouseholdId(created.id);
    } catch (err: any) {
      alert(err.message || "Failed to create household");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedHouseholdId) return;
    setSubmitting(true);
    try {
      await api.createExpenseSplit(selectedHouseholdId, {
        description: expenseDesc,
        total_amount: parseFloat(expenseAmount),
        currency,
        split_type: "EQUAL",
      });
      setExpenseDesc("");
      setExpenseAmount("");
      setShowAddExpenseModal(false);
      fetchBalances(selectedHouseholdId);
    } catch (err: any) {
      alert(err.message || "Failed to record shared expense");
    } finally {
      setSubmitting(false);
    }
  };

  const activeHousehold = households.find((h) => h.id === selectedHouseholdId);

  return (
    <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Household Expense Splits</h1>
          <p className="text-sm text-slate-500">
            Fair, deterministic penny-rounding debt settlements with roommates & family.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {households.length > 0 && (
            <button
              onClick={() => setShowAddExpenseModal(true)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition flex items-center gap-2"
            >
              <span>+</span>
              <span>Split Expense</span>
            </button>
          )}
          <button
            onClick={() => setShowCreateHouseholdModal(true)}
            className="px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-sm font-medium shadow-sm transition"
          >
            + New Household
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700">
          {error}
        </div>
      )}

      {/* Household selector & Penny rounding note */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-indigo-50/70 border border-indigo-100 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-indigo-900 uppercase">Active Household:</span>
          {households.length > 0 ? (
            <select
              value={selectedHouseholdId}
              onChange={(e) => setSelectedHouseholdId(e.target.value)}
              className="bg-white border border-indigo-200 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {households.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name} ({h.members?.length || 0} members)
                </option>
              ))}
            </select>
          ) : (
            <span className="text-sm text-slate-500">None created yet</span>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-indigo-700">
          <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Deterministic penny-rounding: sum(shares) === total amount guarantee</span>
        </div>
      </div>

      {/* If no household */}
      {!loading && households.length === 0 && (
        <div className="p-12 bg-white rounded-xl border border-slate-200 text-center">
          <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 className="text-base font-semibold text-slate-800">No household group yet</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
            Create a household to split grocery receipts, utilities, and subscriptions fairly with zero penny mismatches.
          </p>
          <button
            onClick={() => setShowCreateHouseholdModal(true)}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition"
          >
            Create Household Group
          </button>
        </div>
      )}

      {/* Balance Cards & Members */}
      {activeHousehold && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Household Info */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Household Roster
            </h3>
            <div className="divide-y divide-slate-100">
              {activeHousehold.members?.map((m) => (
                <div key={m.id} className="py-2.5 flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold text-slate-800">
                      {m.full_name || m.email || "Member"}
                    </div>
                    <div className="text-xs text-slate-400 capitalize">{m.role}</div>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                    Active
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Settlement Balances */}
          <div className="md:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                Balance & Debt Matrix
              </h3>
              <button
                onClick={() => fetchBalances(selectedHouseholdId)}
                className="text-xs text-indigo-600 hover:underline font-medium"
              >
                Refresh Balances
              </button>
            </div>

            {balances.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm">
                No shared expenses recorded yet. All accounts are settled!
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {balances.map((b) => (
                  <div key={b.user_id} className="py-4 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-sm text-slate-900">{b.full_name}</div>
                      <div className="text-xs text-slate-500">
                        Paid: ${Number(b.total_paid).toFixed(2)} | Share: $
                        {Number(b.total_owed).toFixed(2)}
                      </div>
                    </div>
                    <div className="text-right">
                      <span
                        className={`text-sm font-bold ${
                          b.net_balance > 0
                            ? "text-emerald-600"
                            : b.net_balance < 0
                            ? "text-rose-600"
                            : "text-slate-500"
                        }`}
                      >
                        {b.net_balance > 0
                          ? `+ $${Number(b.net_balance).toFixed(2)}`
                          : b.net_balance < 0
                          ? `- $${Math.abs(Number(b.net_balance)).toFixed(2)}`
                          : "$0.00"}
                      </span>
                      <span className="block text-xs text-slate-400">
                        {b.net_balance > 0
                          ? "Gets back"
                          : b.net_balance < 0
                          ? "Owes group"
                          : "Settled up"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Household Modal */}
      {showCreateHouseholdModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-800">New Household Group</h2>
              <button
                onClick={() => setShowCreateHouseholdModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateHousehold} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Household / Group Name *
                </label>
                <input
                  type="text"
                  required
                  value={newHouseholdName}
                  onChange={(e) => setNewHouseholdName(e.target.value)}
                  placeholder="e.g. Elm Street Apartment, Family Hub"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateHouseholdModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition disabled:opacity-50"
                >
                  {submitting ? "Creating..." : "Create Household"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Shared Expense Modal */}
      {showAddExpenseModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-800">Split Shared Expense</h2>
              <button
                onClick={() => setShowAddExpenseModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateExpense} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Expense Description *
                </label>
                <input
                  type="text"
                  required
                  value={expenseDesc}
                  onChange={(e) => setExpenseDesc(e.target.value)}
                  placeholder="e.g. Weekly Groceries at Trader Joe's"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Total Amount *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={expenseAmount}
                    onChange={(e) => setExpenseAmount(e.target.value)}
                    placeholder="124.50"
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
                  </select>
                </div>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600">
                <span className="font-semibold block mb-0.5">Equal Split Rule:</span>
                The cost is divided equally among all {activeHousehold?.members?.length || 1} household members. Any remainder penny is deterministically allocated to ensure the exact cent total.
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddExpenseModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition disabled:opacity-50"
                >
                  {submitting ? "Splitting..." : "Split Expense"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
