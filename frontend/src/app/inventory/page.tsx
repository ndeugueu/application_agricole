'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Layout from '@/components/Layout';
import { api } from '@/lib/api';
import { FiPlus, FiEdit2, FiTrash2, FiPackage, FiArrowUp, FiArrowDown } from 'react-icons/fi';

interface Product {
  id: string;
  name: string;
  category: string;
  unit: string;
  unit_price: number;
  description?: string;
  current_stock?: number;
}

export default function InventoryPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [stockLevels, setStockLevels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    unit: '',
    unit_price: '',
    description: '',
  });
  const [stockFormData, setStockFormData] = useState({
    product_id: '',
    movement_type: 'IN',
    quantity: '',
    reference: '',
    notes: '',
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [productsData, stockData] = await Promise.all([
        api.getProducts(),
        api.getStockLevels(),
      ]);
      setProducts(productsData);
      setStockLevels(stockData);
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStockLevel = (productId: string) => {
    const stock = stockLevels.find((s) => String(s.product_id) === String(productId));
    return stock?.current_stock || 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        unit_price: parseFloat(formData.unit_price),
      };

      if (editingProduct) {
        await api.updateProduct(editingProduct.id, payload);
      } else {
        await api.createProduct(payload);
      }

      setShowModal(false);
      setEditingProduct(null);
      setFormData({ name: '', category: '', unit: '', unit_price: '', description: '' });
      fetchData();
    } catch (err) {
      console.error('Error saving product:', err);
    }
  };

  const handleStockSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createStockMovement({
        ...stockFormData,
        quantity: parseFloat(stockFormData.quantity),
      });

      setShowStockModal(false);
      setStockFormData({
        product_id: '',
        movement_type: 'IN',
        quantity: '',
        reference: '',
        notes: '',
      });
      fetchData();
    } catch (err) {
      console.error('Error creating stock movement:', err);
    }
  };

  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setFormData({
      name: product.name,
      category: product.category,
      unit: product.unit,
      unit_price: product.unit_price.toString(),
      description: product.description || '',
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce produit ?')) {
      try {
        await api.deleteProduct(id);
        fetchData();
      } catch (err) {
        console.error('Error deleting product:', err);
      }
    }
  };

  const openStockModal = (product: Product, type: 'IN' | 'OUT') => {
    setSelectedProduct(product);
    setStockFormData({
      product_id: product.id,
      movement_type: type,
      quantity: '',
      reference: '',
      notes: '',
    });
    setShowStockModal(true);
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
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 className="text-2xl font-bold text-gray-900">Inventaire</h2>
          <button
            onClick={() => {
              setEditingProduct(null);
              setFormData({ name: '', category: '', unit: '', unit_price: '', description: '' });
              setShowModal(true);
            }}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <FiPlus className="w-5 h-5 mr-2" />
            Nouveau produit
          </button>
        </div>

        {/* Products Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Produit
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Catégorie
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Prix unitaire
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stock actuel
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {products.map((product) => {
                  const stock = getStockLevel(product.id);
                  const isLowStock = stock < 10;

                  return (
                    <tr key={product.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10 bg-primary-100 rounded-lg flex items-center justify-center">
                            <FiPackage className="h-5 w-5 text-primary-600" />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{product.name}</div>
                            <div className="text-sm text-gray-500">{product.unit}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          {product.category}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {product.unit_price.toFixed(2)} FCFA
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            isLowStock
                              ? 'bg-red-100 text-red-800'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {stock} {product.unit}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => openStockModal(product, 'IN')}
                            className="text-green-600 hover:text-green-900"
                            title="Entrée stock"
                          >
                            <FiArrowDown className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => openStockModal(product, 'OUT')}
                            className="text-orange-600 hover:text-orange-900"
                            title="Sortie stock"
                          >
                            <FiArrowUp className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleEdit(product)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            <FiEdit2 className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDelete(product.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <FiTrash2 className="w-5 h-5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {products.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                Aucun produit enregistré. Cliquez sur "Nouveau produit" pour commencer.
              </div>
            )}
          </div>
        </div>

        {/* Product Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                {editingProduct ? 'Modifier' : 'Nouveau'} produit
              </h3>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Catégorie *
                  </label>
                  <select
                    required
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Sélectionner</option>
                    <option value="CEREALE">Céréale</option>
                    <option value="LEGUME">Légume</option>
                    <option value="FRUIT">Fruit</option>
                    <option value="BETAIL">Bétail</option>
                    <option value="INTRANT">Intrant</option>
                    <option value="AUTRE">Autre</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Unité *</label>
                  <input
                    type="text"
                    required
                    value={formData.unit}
                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                    placeholder="kg, L, unité, etc."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prix unitaire (FCFA) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.unit_price}
                    onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      setEditingProduct(null);
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    {editingProduct ? 'Modifier' : 'Créer'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Stock Movement Modal */}
        {showStockModal && selectedProduct && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                {stockFormData.movement_type === 'IN' ? 'Entrée' : 'Sortie'} de stock -{' '}
                {selectedProduct.name}
              </h3>

              <form onSubmit={handleStockSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quantité ({selectedProduct.unit}) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={stockFormData.quantity}
                    onChange={(e) =>
                      setStockFormData({ ...stockFormData, quantity: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Référence
                  </label>
                  <input
                    type="text"
                    value={stockFormData.reference}
                    onChange={(e) =>
                      setStockFormData({ ...stockFormData, reference: e.target.value })
                    }
                    placeholder="Bon de commande, facture, etc."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                  <textarea
                    value={stockFormData.notes}
                    onChange={(e) =>
                      setStockFormData({ ...stockFormData, notes: e.target.value })
                    }
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowStockModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    Confirmer
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
