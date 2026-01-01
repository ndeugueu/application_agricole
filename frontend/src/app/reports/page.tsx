'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Layout from '@/components/Layout';
import { api } from '@/lib/api';
import { FiDownload, FiFileText, FiFile } from 'react-icons/fi';
import { format } from 'date-fns';

interface Report {
  id: string;
  name: string;
  report_type: string;
  generated_at: string;
  file_path?: string;
}

export default function ReportsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchReports();
    }
  }, [isAuthenticated]);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const data = await api.getReports();
      setReports(data);
    } catch (err) {
      console.error('Error fetching reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async (type: string) => {
    try {
      setGenerating(true);
      await api.generateReport({
        name: `Rapport ${type} - ${format(new Date(), 'dd/MM/yyyy')}`,
        report_type: type,
        parameters: {},
      });
      fetchReports();
    } catch (err) {
      console.error('Error generating report:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (reportId: string, format: 'pdf' | 'excel') => {
    try {
      const blob = await api.downloadReport(reportId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${reportId}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error downloading report:', err);
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
        <h2 className="text-2xl font-bold text-gray-900">Rapports</h2>

        {/* Generate Reports */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Générer un rapport</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <button
              onClick={() => handleGenerateReport('SALES')}
              disabled={generating}
              className="p-4 border-2 border-primary-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors disabled:opacity-50"
            >
              <FiFileText className="w-8 h-8 mx-auto mb-2 text-primary-600" />
              <span className="text-sm font-medium">Rapport Ventes</span>
            </button>
            <button
              onClick={() => handleGenerateReport('INVENTORY')}
              disabled={generating}
              className="p-4 border-2 border-primary-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors disabled:opacity-50"
            >
              <FiFileText className="w-8 h-8 mx-auto mb-2 text-primary-600" />
              <span className="text-sm font-medium">Rapport Inventaire</span>
            </button>
            <button
              onClick={() => handleGenerateReport('ACCOUNTING')}
              disabled={generating}
              className="p-4 border-2 border-primary-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors disabled:opacity-50"
            >
              <FiFileText className="w-8 h-8 mx-auto mb-2 text-primary-600" />
              <span className="text-sm font-medium">Rapport Comptable</span>
            </button>
            <button
              onClick={() => handleGenerateReport('CUSTOM')}
              disabled={generating}
              className="p-4 border-2 border-primary-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors disabled:opacity-50"
            >
              <FiFileText className="w-8 h-8 mx-auto mb-2 text-primary-600" />
              <span className="text-sm font-medium">Rapport Personnalisé</span>
            </button>
          </div>
        </div>

        {/* Reports List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Rapports générés</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Nom
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Date de génération
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reports.map((report) => (
                  <tr key={report.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <FiFile className="w-5 h-5 text-gray-400 mr-3" />
                        <span className="text-sm font-medium text-gray-900">{report.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {report.report_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {format(new Date(report.generated_at), 'dd/MM/yyyy HH:mm')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleDownload(report.id, 'pdf')}
                          className="text-red-600 hover:text-red-900"
                          title="Télécharger PDF"
                        >
                          <FiDownload className="w-5 h-5 inline mr-1" />
                          PDF
                        </button>
                        <button
                          onClick={() => handleDownload(report.id, 'excel')}
                          className="text-green-600 hover:text-green-900"
                          title="Télécharger Excel"
                        >
                          <FiDownload className="w-5 h-5 inline mr-1" />
                          Excel
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {reports.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                Aucun rapport généré. Utilisez les boutons ci-dessus pour générer vos premiers rapports.
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
