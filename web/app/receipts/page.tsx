"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ReceiptsPage() {
  const [receipts, setReceipts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [ocrJob, setOcrJob] = useState<any | null>(null);

  // Form states for manual or OCR reviewed receipt
  const [merchant, setMerchant] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [notes, setNotes] = useState("");

  const loadReceipts = async () => {
    setLoading(true);
    try {
      const res = await api.getReceipts({ merchant: search || undefined });
      setReceipts(res.items || []);
    } catch {
      // Handled by api client
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setDate(new Date().toISOString().split("T")[0]);
    loadReceipts();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const job = await api.processOcr(file);
      setOcrJob(job);
      if (job.parsed_data) {
        setMerchant(job.parsed_data.merchant_name || "");
        if (job.parsed_data.total_amount) {
          setAmount(job.parsed_data.total_amount.toString());
        }
        if (job.parsed_data.purchase_date) {
          setDate(new Date(job.parsed_data.purchase_date).toISOString().split("T")[0]);
        }
      }
    } catch (err: any) {
      alert(`OCR Scan Error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleSaveReceipt = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (ocrJob) {
        // Confirm the OCR Job
        await api.reviewOcr(ocrJob.id, {
          action: "CONFIRM",
          merchant_name: merchant,
          total_amount: parseFloat(amount),
          purchase_date: new Date(date).toISOString(),
          notes,
        });
      } else {
        // Manual Create
        await api.createReceipt({
          merchant_name: merchant,
          total_amount: parseFloat(amount),
          purchase_date: new Date(date).toISOString(),
          currency: "USD",
          notes,
        });
      }

      setShowUploadModal(false);
      setOcrJob(null);
      setMerchant("");
      setAmount("");
      setNotes("");
      loadReceipts();
    } catch (err: any) {
      alert(`Error saving receipt: ${err.message}`);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to remove this receipt from your vault?")) return;
    try {
      await api.deleteReceipt(id);
      loadReceipts();
    } catch (err: any) {
      alert(`Delete error: ${err.message}`);
    }
  };

  return (
    <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Receipts Vault</h1>
          <p className="text-sm text-slate-500">Search, organize, and inspect all captured expense receipts.</p>
        </div>
        <div className="flex items-center gap-3">
          <a
            href={api.getExportCsvUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 font-medium rounded-lg text-sm border border-slate-300 shadow-xs transition-colors"
          >
            Export CSV
          </a>
          <button
            onClick={() => {
              setOcrJob(null);
              setMerchant("");
              setAmount("");
              setShowUploadModal(true);
            }}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-sm shadow-sm transition-colors flex items-center gap-2"
          >
            <span>+</span>
            <span>Upload Receipt</span>
          </button>
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex gap-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && loadReceipts()}
          placeholder="Search by merchant or receipt notes..."
          className="flex-1 max-w-md px-3.5 py-2 bg-white border border-slate-300 rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-xs"
        />
        <button
          onClick={loadReceipts}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white text-sm font-medium rounded-lg transition-colors"
        >
          Search
        </button>
      </div>

      {/* Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-200">
              <tr>
                <th className="px-5 py-3.5">Merchant</th>
                <th className="px-5 py-3.5">Purchase Date</th>
                <th className="px-5 py-3.5">Category</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Amount</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-400 text-sm">
                    Loading receipts...
                  </td>
                </tr>
              ) : receipts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-400 text-sm">
                    No receipts found. Upload your first receipt image or add one manually.
                  </td>
                </tr>
              ) : (
                receipts.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-medium text-slate-900">{r.merchant_name}</td>
                    <td className="px-5 py-3.5 text-slate-500">
                      {new Date(r.purchase_date).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5 text-slate-600">{r.category?.name || "General"}</td>
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
                    <td className="px-5 py-3.5 text-right font-semibold text-slate-900">
                      {r.currency} {Number(r.total_amount).toFixed(2)}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => handleDelete(r.id)}
                        className="text-xs text-rose-600 hover:text-rose-800 font-medium ml-3"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload & OCR Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-semibold text-slate-900">
                {ocrJob ? "Review OCR Extraction" : "Upload Receipt Image / Manual Entry"}
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                &times;
              </button>
            </div>

            {/* File Upload Drop Area */}
            {!ocrJob && (
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-indigo-500 transition-colors">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,application/pdf"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="hidden"
                  id="receipt-file-input"
                />
                <label htmlFor="receipt-file-input" className="cursor-pointer block space-y-2">
                  <div className="text-3xl">📷</div>
                  <p className="text-sm font-medium text-slate-700">
                    {uploading ? "Running OCR Analysis..." : "Click to select or drop receipt image"}
                  </p>
                  <p className="text-xs text-slate-400">Supports JPEG, PNG, WEBP, PDF (up to 15MB)</p>
                </label>
              </div>
            )}

            {/* OCR Duplicate Warning Banner */}
            {ocrJob?.parsed_data?.is_duplicate && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
                ⚠️ {ocrJob.parsed_data.duplicate_warning}
              </div>
            )}

            <form onSubmit={handleSaveReceipt} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                  Merchant Name
                </label>
                <input
                  type="text"
                  required
                  value={merchant}
                  onChange={(e) => setMerchant(e.target.value)}
                  placeholder="e.g. Target, Home Depot"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Total Amount ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="0.00"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Purchase Date
                  </label>
                  <input
                    type="date"
                    required
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Notes</label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Optional tags or notes..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm"
                >
                  {ocrJob ? "Confirm & Save" : "Save Receipt"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
