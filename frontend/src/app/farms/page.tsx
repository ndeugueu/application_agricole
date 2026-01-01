'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Layout from '@/components/Layout';
import { api } from '@/lib/api';
import { FiPlus, FiEdit2, FiTrash2, FiMap } from 'react-icons/fi';

interface Farm {
  id: string;
  name: string;
  location: string;
  total_area: number;
  description?: string;
  created_at: string;
}

export default function FarmsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [farms, setFarms] = useState<Farm[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingFarm, setEditingFarm] = useState<Farm | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    total_area: '',
    description: '',
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchFarms();
    }
  }, [isAuthenticated]);

  const fetchFarms = async () => {
    try {
      setLoading(true);
      const data = await api.getFarms();
      setFarms(data);
    } catch (err) {
      console.error('Error fetching farms:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        total_area: parseFloat(formData.total_area),
      };

      if (editingFarm) {
        await api.updateFarm(editingFarm.id, payload);
      } else {
        await api.createFarm(payload);
      }

      setShowModal(false);
      setEditingFarm(null);
      setFormData({ name: '', location: '', total_area: '', description: '' });
      fetchFarms();
    } catch (err) {
      console.error('Error saving farm:', err);
    }
  };

  const handleEdit = (farm: Farm) => {
    setEditingFarm(farm);
    setFormData({
      name: farm.name,
      location: farm.location,
      total_area: farm.total_area.toString(),
      description: farm.description || '',
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette exploitation ?')) {
      try {
        await api.deleteFarm(id);
        fetchFarms();
      } catch (err) {
        console.error('Error deleting farm:', err);
      }
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
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 className="text-2xl font-bold text-gray-900">Mes Exploitations</h2>
          <button
            onClick={() => {
              setEditingFarm(null);
              setFormData({ name: '', location: '', total_area: '', description: '' });
              setShowModal(true);
            }}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <FiPlus className="w-5 h-5 mr-2" />
            Nouvelle exploitation
          </button>
        </div>

        {/* Farms Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {farms.map((farm) => (
            <div
              key={farm.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center">
                  <div className="p-2 bg-primary-100 rounded-lg mr-3">
                    <FiMap className="w-6 h-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{farm.name}</h3>
                    <p className="text-sm text-gray-500">{farm.location}</p>
                  </div>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Surface totale:</span>
                  <span className="font-medium">{farm.total_area} ha</span>
                </div>
                {farm.description && (
                  <p className="text-sm text-gray-600 line-clamp-2">{farm.description}</p>
                )}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(farm)}
                  className="flex-1 flex items-center justify-center px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <FiEdit2 className="w-4 h-4 mr-2" />
                  Modifier
                </button>
                <button
                  onClick={() => handleDelete(farm.id)}
                  className="flex items-center justify-center px-3 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                >
                  <FiTrash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}

          {farms.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500">
              Aucune exploitation enregistrée. Cliquez sur "Nouvelle exploitation" pour commencer.
            </div>
          )}
        </div>

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                {editingFarm ? 'Modifier' : 'Nouvelle'} exploitation
              </h3>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Localisation *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Surface totale (ha) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.total_area}
                    onChange={(e) => setFormData({ ...formData, total_area: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      setEditingFarm(null);
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    {editingFarm ? 'Modifier' : 'Créer'}
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
