"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  entity_type?: string;
  entity_id?: string;
  is_read: boolean;
  created_at: string;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getNotifications(unreadOnly);
      setNotifications(data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load notifications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [unreadOnly]);

  const handleMarkRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err: any) {
      alert(err.message || "Failed to mark as read");
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err: any) {
      alert(err.message || "Failed to mark all as read");
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case "WARRANTY_EXPIRING":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">
            Warranty Alert
          </span>
        );
      case "SUBSCRIPTION_RENEWAL":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800">
            Renewal Alert
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-800">
            System
          </span>
        );
    }
  };

  return (
    <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Notification Center</h1>
          <p className="text-sm text-slate-500">
            Proactive alerts for expiring warranties and renewal charges.
          </p>
        </div>
        <button
          onClick={handleMarkAllRead}
          className="px-3 py-1.5 text-xs font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg shadow-sm transition"
        >
          Mark All as Read
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setUnreadOnly(false)}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
            !unreadOnly
              ? "bg-indigo-600 text-white shadow-sm"
              : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-100"
          }`}
        >
          All Notifications
        </button>
        <button
          onClick={() => setUnreadOnly(true)}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
            unreadOnly
              ? "bg-indigo-600 text-white shadow-sm"
              : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-100"
          }`}
        >
          Unread Only
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700">
          {error}
        </div>
      )}

      {/* List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">Loading notifications...</div>
        ) : notifications.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-800">All caught up!</h3>
            <p className="text-sm text-slate-500 mt-1">
              You have no {unreadOnly ? "unread " : ""}notifications at this time.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {notifications.map((n) => (
              <div
                key={n.id}
                className={`p-5 flex items-start justify-between gap-4 transition ${
                  n.is_read ? "bg-white" : "bg-indigo-50/30"
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {getTypeBadge(n.notification_type)}
                    <h4
                      className={`text-sm ${
                        n.is_read ? "font-medium text-slate-800" : "font-bold text-slate-900"
                      }`}
                    >
                      {n.title}
                    </h4>
                    {!n.is_read && (
                      <span className="w-2 h-2 rounded-full bg-indigo-600"></span>
                    )}
                  </div>
                  <p className="text-sm text-slate-600">{n.message}</p>
                  <span className="text-xs text-slate-400 block pt-1">
                    {new Date(n.created_at).toLocaleString()}
                  </span>
                </div>

                {!n.is_read && (
                  <button
                    onClick={() => handleMarkRead(n.id)}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 shrink-0 px-2 py-1 rounded hover:bg-indigo-50 transition"
                  >
                    Mark Read
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
