'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Layout from '@/components/Layout';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { FiArrowLeft, FiPlus, FiTrash2 } from 'react-icons/fi';

interface Customer {
  id: string;
  name: string;
  phone_number?: string;
  email?: string;
  address?: string;
}

interface Product {
  id: string;
  code?: string;
  name: string;
  unit: string;
  unit_price: number;
}

interface SaleLineForm {
  id: string;
  product_id: string;
  product_code: string;
  product_name: string;
  quantity: string;
  unit_price: string;
}

const today = () => new Date().toISOString().slice(0, 10);

export default function NewSalePage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [showCustomerModal, setShowCustomerModal] = useState(false);

  const [formData, setFormData] = useState({
    customer_id: '',
    sale_date: today(),
    notes: '',
    delivery_address: '',
  });

  const [lines, setLines] = useState<SaleLineForm[]>([
    {
      id: crypto.randomUUID(),
      product_id: '',
      product_code: '',
      product_name: '',
      quantity: '1',
      unit_price: '',
    },
  ]);

  const [customerForm, setCustomerForm] = useState({
    name: '',
    phone_number: '',
    email: '',
    address: '',
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      void loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [customersData, productsData] = await Promise.all([
        api.getCustomers(),
        api.getProducts(),
      ]);
      setCustomers(customersData);
      setProducts(productsData);
    } catch (err) {
      console.error('Error loading sale data:', err);
      setError('Impossible de charger les clients ou produits.');
    } finally {
      setLoading(false);
    }
  };

  const total = useMemo(() => {
    return lines.reduce((sum, line) => {
      const qty = Number(line.quantity || 0);
      const price = Number(line.unit_price || 0);
      return sum + qty * price;
    }, 0);
  }, [lines]);

  const handleLineChange = (id: string, patch: Partial<SaleLineForm>) => {
    setLines((prev) =>
      prev.map((line) => (line.id === id ? { ...line, ...patch } : line))
    );
  };

  const handleProductSelect = (id: string, productId: string) => {
    const product = products.find((item) => item.id === productId);
    if (!product) {
      handleLineChange(id, {
        product_id: '',
        product_code: '',
        product_name: '',
        unit_price: '',
      });
      return;
    }

    handleLineChange(id, {
      product_id: product.id,
      product_code: product.code || '',
      product_name: product.name,
      unit_price: String(product.unit_price ?? ''),
    });
  };

  const addLine = () => {
    setLines((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        product_id: '',
        product_code: '',
        product_name: '',
        quantity: '1',
        unit_price: '',
      },
    ]);
  };

  const removeLine = (id: string) => {
    setLines((prev) => (prev.length > 1 ? prev.filter((line) => line.id !== id) : prev));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const validLines = lines.filter((line) => line.product_id && Number(line.quantity) > 0);
    if (!formData.customer_id) {
      setError('Veuillez selectionner un client.');
      return;
    }
    if (validLines.length === 0) {
      setError('Ajoutez au moins une ligne de vente valide.');
      return;
    }

    setSubmitting(true);
    try {
      await api.createSale({
        ...formData,
        lines: validLines,
      });
      router.push('/sales');
    } catch (err) {
      console.error('Error creating sale:', err);
      setError('Echec lors de la creation de la vente.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCustomerCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!customerForm.name.trim()) {
      setError('Le nom du client est obligatoire.');
      return;
    }

    try {
      const customer = await api.createCustomer({
        name: customerForm.name.trim(),
        phone_number: customerForm.phone_number || undefined,
        email: customerForm.email || undefined,
        address: customerForm.address || undefined,
      });
      setCustomers((prev) => [customer, ...prev]);
      setFormData((prev) => ({ ...prev, customer_id: customer.id }));
      setCustomerForm({ name: '', phone_number: '', email: '', address: '' });
      setShowCustomerModal(false);
    } catch (err) {
      console.error('Error creating customer:', err);
      setError('Echec lors de la creation du client.');
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

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.push('/sales')}
            className="flex items-center text-sm text-gray-600 hover:text-gray-900"
          >
            <FiArrowLeft className="mr-2" />
            Retour aux ventes
          </button>
        </div>

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 className="text-2xl font-bold text-gray-900">Nouvelle vente</h2>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Client *</label>
                <div className="flex gap-2">
                  <select
                    required
                    value={formData.customer_id}
                    onChange={(event) =>
                      setFormData((prev) => ({ ...prev, customer_id: event.target.value }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Selectionner un client</option>
                    {customers.map((customer) => (
                      <option key={customer.id} value={customer.id}>
                        {customer.name}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => setShowCustomerModal(true)}
                    className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    title="Nouveau client"
                  >
                    <FiPlus />
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date *</label>
                <input
                  type="date"
                  required
                  value={formData.sale_date}
                  onChange={(event) =>
                    setFormData((prev) => ({ ...prev, sale_date: event.target.value }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Adresse de livraison</label>
                <input
                  type="text"
                  value={formData.delivery_address}
                  onChange={(event) =>
                    setFormData((prev) => ({ ...prev, delivery_address: event.target.value }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <input
                  type="text"
                  value={formData.notes}
                  onChange={(event) => setFormData((prev) => ({ ...prev, notes: event.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Lignes de vente</h3>
              <button
                type="button"
                onClick={addLine}
                className="flex items-center text-sm text-primary-600 hover:text-primary-700"
              >
                <FiPlus className="mr-1" />
                Ajouter une ligne
              </button>
            </div>

            {lines.map((line) => (
              <div key={line.id} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                <div className="md:col-span-5">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Produit *</label>
                  <select
                    required
                    value={line.product_id}
                    onChange={(event) => handleProductSelect(line.id, event.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Selectionner un produit</option>
                    {products.map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.name} ({product.unit})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Quantite *</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    required
                    value={line.quantity}
                    onChange={(event) => handleLineChange(line.id, { quantity: event.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div className="md:col-span-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prix unitaire (FCFA) *</label>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    required
                    value={line.unit_price}
                    onChange={(event) => handleLineChange(line.id, { unit_price: event.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div className="md:col-span-2 flex justify-end">
                  <button
                    type="button"
                    onClick={() => removeLine(line.id)}
                    className="text-red-600 hover:text-red-800"
                    title="Supprimer la ligne"
                  >
                    <FiTrash2 />
                  </button>
                </div>
              </div>
            ))}

            <div className="flex justify-end text-sm text-gray-600">
              Total HT estime: <span className="ml-2 font-semibold text-gray-900">{total.toFixed(2)} FCFA</span>
            </div>
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => router.push('/sales')}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-60"
            >
              {submitting ? 'Enregistrement...' : 'Creer la vente'}
            </button>
          </div>
        </form>

        {showCustomerModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Nouveau client</h3>
              <form onSubmit={handleCustomerCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                  <input
                    type="text"
                    required
                    value={customerForm.name}
                    onChange={(event) =>
                      setCustomerForm((prev) => ({ ...prev, name: event.target.value }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Telephone</label>
                  <input
                    type="text"
                    value={customerForm.phone_number}
                    onChange={(event) =>
                      setCustomerForm((prev) => ({ ...prev, phone_number: event.target.value }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={customerForm.email}
                    onChange={(event) => setCustomerForm((prev) => ({ ...prev, email: event.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Adresse</label>
                  <input
                    type="text"
                    value={customerForm.address}
                    onChange={(event) =>
                      setCustomerForm((prev) => ({ ...prev, address: event.target.value }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowCustomerModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    Creer
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
