const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiClient {
  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("vaultly_access_token");
  }

  public setToken(token: string): void {
    if (typeof window !== "undefined") {
      localStorage.setItem("vaultly_access_token", token);
    }
  }

  public clearToken(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("vaultly_access_token");
      localStorage.removeItem("vaultly_refresh_token");
      localStorage.removeItem("vaultly_user");
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      this.clearToken();
      if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }

    if (!res.ok) {
      let errorMsg = `HTTP Error ${res.status}`;
      try {
        const errorData = await res.json();
        errorMsg = errorData.detail || JSON.stringify(errorData);
      } catch {
        errorMsg = await res.text();
      }
      throw new Error(errorMsg);
    }

    return res.json();
  }

  // Auth
  async login(email: string, password: string) {
    const res = await this.request<{ access_token: string; refresh_token: string }>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }
    );
    this.setToken(res.access_token);
    if (typeof window !== "undefined") {
      localStorage.setItem("vaultly_refresh_token", res.refresh_token);
    }
    return res;
  }

  async register(email: string, password: string, full_name: string) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    });
  }

  async getMe() {
    return this.request<{ id: string; email: string; full_name: string }>("/auth/me");
  }

  // Receipts
  async getReceipts(params: { page?: number; merchant?: string; category_id?: string } = {}) {
    const q = new URLSearchParams();
    if (params.page) q.set("page", params.page.toString());
    if (params.merchant) q.set("merchant", params.merchant);
    if (params.category_id) q.set("category_id", params.category_id);
    return this.request<any>(`/receipts?${q.toString()}`);
  }

  async getReceipt(id: string) {
    return this.request<any>(`/receipts/${id}`);
  }

  async createReceipt(payload: any, idempotencyKey?: string) {
    const headers: Record<string, string> = {};
    if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
    return this.request<any>("/receipts", {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });
  }

  async deleteReceipt(id: string) {
    return this.request<{ message: string }>(`/receipts/${id}`, { method: "DELETE" });
  }

  async uploadReceiptImage(receiptId: string, file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return this.request<any>(`/receipts/${receiptId}/images`, {
      method: "POST",
      body: formData,
    });
  }

  // OCR
  async processOcr(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return this.request<any>("/ocr/process", {
      method: "POST",
      body: formData,
    });
  }

  async reviewOcr(jobId: string, review: any) {
    return this.request<{ message: string }>(`/ocr/jobs/${jobId}/review`, {
      method: "POST",
      body: JSON.stringify(review),
    });
  }

  // Warranties
  async getWarranties(status?: string) {
    const q = status ? `?status=${status}` : "";
    return this.request<any>(`/warranties${q}`);
  }

  async createWarranty(payload: any) {
    return this.request<any>("/warranties", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async deleteWarranty(id: string) {
    return this.request<{ message: string }>(`/warranties/${id}`, { method: "DELETE" });
  }

  // Subscriptions
  async getSubscriptions(status?: string) {
    const q = status ? `?status=${status}` : "";
    return this.request<any>(`/subscriptions${q}`);
  }

  async getSubscriptionAnalytics() {
    return this.request<any>("/subscriptions/analytics");
  }

  async createSubscription(payload: any) {
    return this.request<any>("/subscriptions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async cancelSubscription(id: string) {
    return this.request<any>(`/subscriptions/${id}/cancel`, { method: "POST" });
  }

  // Households & Splits
  async getHouseholds() {
    return this.request<any[]>("/households");
  }

  async createHousehold(name: string) {
    return this.request<any>("/households", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  }

  async getHouseholdBalances(householdId: string) {
    return this.request<any>(`/households/${householdId}/balances`);
  }

  async createExpenseSplit(householdId: string, payload: any) {
    return this.request<any>(`/households/${householdId}/splits`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // Notifications
  async getNotifications(unreadOnly = false) {
    return this.request<any>(`/notifications?unread_only=${unreadOnly}`);
  }

  async markNotificationRead(id: string) {
    return this.request<{ message: string }>(`/notifications/${id}/read`, { method: "POST" });
  }

  async markAllNotificationsRead() {
    return this.request<{ message: string }>("/notifications/read-all", { method: "POST" });
  }

  // Reports
  getExportCsvUrl(): string {
    const token = this.getToken();
    return `${API_BASE_URL}/reports/export/csv${token ? `?token=${token}` : ""}`;
  }

  getExportPdfUrl(): string {
    const token = this.getToken();
    return `${API_BASE_URL}/reports/export/pdf${token ? `?token=${token}` : ""}`;
  }
}

export const api = new ApiClient();
