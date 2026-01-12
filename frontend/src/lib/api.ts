import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost';
// All API calls go through the gateway to avoid CORS issues.

const PRODUCT_TYPE_MAP: Record<string, string> = {
  CEREALE: 'recolte',
  LEGUME: 'recolte',
  FRUIT: 'recolte',
  BETAIL: 'autre',
  INTRANT: 'intrant',
  AUTRE: 'autre',
};

const SALE_STATUS_MAP: Record<string, string> = {
  pending: 'PENDING',
  confirmed: 'COMPLETED',
  rejected: 'CANCELLED',
  cancelled: 'CANCELLED',
};

const generateCode = (name: string, prefix: string) => {
  const base = name
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 6);
  const suffix = Date.now().toString().slice(-4);
  return `${prefix}${base || 'ITEM'}${suffix}`;
};

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = this.getRefreshToken();
            if (refreshToken) {
              const response = await this.client.post('/api/v1/auth/refresh', {
                refresh_token: refreshToken,
              });

              const { access_token } = response.data;
              this.setToken(access_token);

              originalRequest.headers.Authorization = `Bearer ${access_token}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            this.clearAuth();
            if (typeof window !== 'undefined') {
              window.location.href = '/login';
            }
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('access_token');
    }
    return null;
  }

  private getRefreshToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('refresh_token');
    }
    return null;
  }

  private setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  private clearAuth(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const response = await this.client.post('/api/v1/auth/login', {
      username,
      password,
    });

    const { access_token, refresh_token, user } = response.data;

    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
    }

    return response.data;
  }

  async logout() {
    try {
      const refreshToken = this.getRefreshToken();
      if (refreshToken) {
        await this.client.post('/api/v1/auth/logout', { refresh_token: refreshToken });
      } else {
        await this.client.post('/api/v1/auth/logout', { refresh_token: '' });
      }
    } finally {
      this.clearAuth();
    }
  }

  async getCurrentUser() {
    const response = await this.client.get('/api/v1/users/me');
    return response.data;
  }

  // Dashboard endpoints (via BFF Web)
  async getDashboard() {
    const response = await this.client.get('/w/dashboard');
    const data = response.data;
    const summary = data?.summary || {};
    const recentSales = data?.recent_sales || [];
    const lowStockItems = data?.low_stock_items || [];

    return {
      summary: {
        total_revenue: summary.sales_month || 0,
        total_sales: recentSales.length,
        total_products: 0,
        low_stock_count: lowStockItems.length,
      },
      sales_by_month: [],
      top_products: [],
      inventory_status: {
        in_stock: 0,
        low_stock: lowStockItems.length,
        out_of_stock: 0,
      },
    };
  }

  async getInventoryOverview() {
    const response = await this.client.get('/w/inventory/overview');
    return response.data;
  }

  async getSalesOverview(params?: { start_date?: string; end_date?: string }) {
    const response = await this.client.get('/w/sales/analytics', { params });
    return response.data;
  }

  async getAccountingOverview(params?: { start_date?: string; end_date?: string }) {
    const response = await this.client.get('/w/accounting/overview', { params });
    return response.data;
  }

  // Farm management
  async getFarms() {
    const response = await this.client.get('/api/v1/farms');
    return response.data;
  }

  async createFarm(data: any) {
    const payload = {
      ...data,
      code: data.code || generateCode(data.name || 'farm', 'FRM-'),
    };
    const response = await this.client.post('/api/v1/farms', payload);
    return response.data;
  }

  async updateFarm(id: string, data: any) {
    const response = await this.client.put(`/api/v1/farms/${id}`, data);
    return response.data;
  }

  async deleteFarm(id: string) {
    await this.client.delete(`/api/v1/farms/${id}`);
  }

  async getPlots(farmId?: string) {
    const params = farmId ? { farm_id: farmId } : {};
    const response = await this.client.get('/api/v1/plots', { params });
    return response.data;
  }

  async createPlot(data: any) {
    const payload = {
      ...data,
      code: data.code || generateCode(data.name || 'plot', 'PLT-'),
    };
    const response = await this.client.post('/api/v1/plots', payload);
    return response.data;
  }

  async updatePlot(id: string, data: any) {
    const response = await this.client.put(`/api/v1/plots/${id}`, data);
    return response.data;
  }

  async deletePlot(id: string) {
    await this.client.delete(`/api/v1/plots/${id}`);
  }

  // Inventory management
  async getProducts() {
    const response = await this.client.get('/api/v1/products');
    return response.data.map((product: any) => ({
      ...product,
      category: product.product_type,
      unit_price: product.unit_price || 0,
    }));
  }

  async createProduct(data: any) {
    const unitPriceRaw = data.unit_price;
    const unitCostRaw = data.unit_cost;
    const unitPrice = Number.isFinite(Number(unitPriceRaw))
      ? Math.round(Number(unitPriceRaw))
      : undefined;
    const unitCost = Number.isFinite(Number(unitCostRaw)) ? Math.round(Number(unitCostRaw)) : undefined;

    const payload = {
      ...data,
      code: data.code || generateCode(data.name || 'product', 'PRD-'),
      product_type: PRODUCT_TYPE_MAP[data.category] || 'autre',
      unit_price: unitPrice,
      unit_cost: unitCost,
    };
    const response = await this.client.post('/api/v1/products', payload);
    return response.data;
  }

  async updateProduct(id: string, data: any) {
    const unitPriceRaw = data.unit_price;
    const unitCostRaw = data.unit_cost;
    const unitPrice = Number.isFinite(Number(unitPriceRaw))
      ? Math.round(Number(unitPriceRaw))
      : undefined;
    const unitCost = Number.isFinite(Number(unitCostRaw)) ? Math.round(Number(unitCostRaw)) : undefined;

    const payload = {
      ...data,
      product_type: PRODUCT_TYPE_MAP[data.category] || data.product_type || 'autre',
      unit_price: unitPrice,
      unit_cost: unitCost,
    };
    const response = await this.client.put(`/api/v1/products/${id}`, payload);
    return response.data;
  }

  async deleteProduct(id: string) {
    await this.client.delete(`/api/v1/products/${id}`);
  }

  async getStockMovements(productId?: string) {
    const params = productId ? { product_id: productId } : {};
    const response = await this.client.get('/api/v1/stock-movements', { params });
    return response.data;
  }

  async createStockMovement(data: any) {
    const movementType = data.movement_type === 'OUT' ? 'sortie' : 'entree';
    const payload = {
      product_id: data.product_id,
      movement_type: movementType,
      quantity: data.quantity,
      reference_type: data.reference || 'manual',
      notes: data.notes,
    };
    const response = await this.client.post('/api/v1/stock-movements', payload);
    return response.data;
  }

  async getStockLevels() {
    const response = await this.client.get('/api/v1/stock-levels');
    return response.data.map((item: any) => ({
      ...item,
      current_stock: Number(item.current_stock),
    }));
  }

  // Sales management
  async getCustomers() {
    const response = await this.client.get('/api/v1/customers');
    return response.data;
  }

  async createCustomer(data: any) {
    const payload = {
      ...data,
      code: data.code || generateCode(data.name || 'customer', 'CST-'),
    };
    const response = await this.client.post('/api/v1/customers', payload);
    return response.data;
  }

  async updateCustomer(id: string, data: any) {
    const response = await this.client.put(`/api/v1/customers/${id}`, data);
    return response.data;
  }

  async deleteCustomer(id: string) {
    await this.client.delete(`/api/v1/customers/${id}`);
  }

  async getSales() {
    const response = await this.client.get('/api/v1/sales');
    return response.data.map((sale: any) => ({
      ...sale,
      total_ht: sale.subtotal ?? 0,
      total_tva: sale.tax_amount ?? 0,
      total_ttc: sale.total_amount ?? 0,
      status: SALE_STATUS_MAP[sale.status] || String(sale.status || '').toUpperCase(),
    }));
  }

  async createSale(data: any) {
    const payload = {
      customer_id: data.customer_id,
      sale_date: data.sale_date,
      notes: data.notes,
      delivery_address: data.delivery_address,
      idempotency_key: data.idempotency_key,
      lines: (data.lines || []).map((line: any) => ({
        product_id: line.product_id,
        product_code: line.product_code,
        product_name: line.product_name,
        quantity: Number(line.quantity),
        unit_price: Math.round(Number(line.unit_price)),
        tax_rate: line.tax_rate ?? 19.25,
      })),
    };
    const response = await this.client.post('/api/v1/sales', payload);
    return response.data;
  }

  async getSale(id: string) {
    const response = await this.client.get(`/api/v1/sales/${id}`);
    return response.data;
  }

  // Accounting
  async getAccounts() {
    const response = await this.client.get('/api/v1/accounts');
    return response.data;
  }

  async getLedgerEntries(params?: any) {
    const response = await this.client.get('/api/v1/ledger-entries', { params });
    return response.data.map((entry: any) => ({
      ...entry,
      debit: entry.amount ?? 0,
      credit: entry.amount ?? 0,
    }));
  }

  async getMonthlyReport(year: number, month: number) {
    const fiscalMonth = `${year}-${String(month).padStart(2, '0')}`;
    const response = await this.client.get(`/api/v1/reports/tva/monthly/${fiscalMonth}`);
    return response.data;
  }

  // Reporting
  async getReports() {
    const response = await this.client.get('/api/v1/reports');
    return response.data.map((report: any) => ({
      ...report,
      name: report.title,
      generated_at: report.created_at,
    }));
  }

  async generateReport(data: any) {
    const typeMap: Record<string, string> = {
      SALES: 'sales_summary',
      INVENTORY: 'inventory_status',
      ACCOUNTING: 'trial_balance',
      CUSTOM: 'custom',
    };

    const payload = {
      report_type: typeMap[data.report_type] || data.report_type,
      report_format: data.report_format || 'pdf',
      title: data.name || 'Rapport',
      filters: data.parameters || {},
    };

    const response = await this.client.post('/api/v1/reports', payload);
    return response.data;
  }

  async downloadReport(reportId: string, format: 'pdf' | 'excel') {
    const response = await this.client.get(`/api/v1/reports/${reportId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

export const api = new ApiClient();
