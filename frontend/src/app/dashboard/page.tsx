'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Layout from '@/components/Layout';
import { api } from '@/lib/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  FiTrendingUp,
  FiDollarSign,
  FiPackage,
  FiShoppingCart,
} from 'react-icons/fi';

interface DashboardData {
  summary: {
    total_revenue: number;
    total_sales: number;
    total_products: number;
    low_stock_count: number;
  };
  sales_by_month: Array<{ month: string; amount: number }>;
  top_products: Array<{ product_name: string; quantity: number; revenue: number }>;
  inventory_status: {
    in_stock: number;
    low_stock: number;
    out_of_stock: number;
  };
}

export default function DashboardPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchDashboard();
    }
  }, [isAuthenticated]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const dashboardData = await api.getDashboard();
      setData(dashboardData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement du tableau de bord');
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      </Layout>
    );
  }

  if (!data) {
    return <Layout><div>Aucune donnée disponible</div></Layout>;
  }

  const statsCards = [
    {
      title: 'Chiffre d\'affaires',
      value: `${data.summary.total_revenue.toFixed(2)} FCFA`,
      icon: FiDollarSign,
      color: 'bg-green-500',
      change: '+12.5%',
    },
    {
      title: 'Ventes totales',
      value: data.summary.total_sales.toString(),
      icon: FiShoppingCart,
      color: 'bg-blue-500',
      change: '+8.2%',
    },
    {
      title: 'Produits',
      value: data.summary.total_products.toString(),
      icon: FiPackage,
      color: 'bg-purple-500',
      change: '+3',
    },
    {
      title: 'Stock faible',
      value: data.summary.low_stock_count.toString(),
      icon: FiTrendingUp,
      color: 'bg-orange-500',
      change: '-2',
    },
  ];

  const COLORS = ['#22c55e', '#f59e0b', '#ef4444'];

  const inventoryData = [
    { name: 'En stock', value: data.inventory_status.in_stock },
    { name: 'Stock faible', value: data.inventory_status.low_stock },
    { name: 'Rupture', value: data.inventory_status.out_of_stock },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
          {statsCards.map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  <p className="text-sm text-green-600 mt-1">{stat.change}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sales Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Ventes par mois
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.sales_by_month}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="amount"
                  stroke="#22c55e"
                  strokeWidth={2}
                  name="Montant (FCFA)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Inventory Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              État de l'inventaire
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={inventoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {inventoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Products */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Produits les plus vendus
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.top_products}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="product_name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="quantity" fill="#22c55e" name="Quantité vendue" />
              <Bar dataKey="revenue" fill="#3b82f6" name="Revenu (FCFA)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Actions rapides
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <button
              onClick={() => router.push('/sales')}
              className="p-4 border-2 border-primary-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors text-center"
            >
              <FiShoppingCart className="w-8 h-8 mx-auto mb-2 text-primary-600" />
              <span className="text-sm font-medium text-gray-900">Nouvelle vente</span>
            </button>
            <button
              onClick={() => router.push('/inventory')}
              className="p-4 border-2 border-primary-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors text-center"
            >
              <FiPackage className="w-8 h-8 mx-auto mb-2 text-primary-600" />
              <span className="text-sm font-medium text-gray-900">Gérer stock</span>
            </button>
            <button
              onClick={() => router.push('/accounting')}
              className="p-4 border-2 border-primary-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors text-center"
            >
              <FiDollarSign className="w-8 h-8 mx-auto mb-2 text-primary-600" />
              <span className="text-sm font-medium text-gray-900">Comptabilité</span>
            </button>
            <button
              onClick={() => router.push('/reports')}
              className="p-4 border-2 border-primary-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors text-center"
            >
              <FiTrendingUp className="w-8 h-8 mx-auto mb-2 text-primary-600" />
              <span className="text-sm font-medium text-gray-900">Rapports</span>
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
}
