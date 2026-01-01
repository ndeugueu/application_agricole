'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Layout from '@/components/Layout';
import { api } from '@/lib/api';
import { FiDollarSign, FiTrendingUp, FiTrendingDown } from 'react-icons/fi';
import { format } from 'date-fns';

interface LedgerEntry {
  id: string;
  debit_account_id: string;
  credit_account_id: string;
  entry_date: string;
  description: string;
  debit: number;
  credit: number;
}

export default function AccountingPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({ total_debit: 0, total_credit: 0, balance: 0 });

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
      const [accountsData, entriesData] = await Promise.all([
        api.getAccounts(),
        api.getLedgerEntries({ limit: 50 }),
      ]);
      setAccounts(accountsData);
      setEntries(entriesData);

      const totalDebit = entriesData.reduce((sum: number, e: LedgerEntry) => sum + e.debit, 0);
      const totalCredit = entriesData.reduce((sum: number, e: LedgerEntry) => sum + e.credit, 0);
      setSummary({
        total_debit: totalDebit,
        total_credit: totalCredit,
        balance: totalDebit - totalCredit,
      });
    } catch (err) {
      console.error('Error fetching accounting data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getAccountCode = (accountId: string) => {
    return (
      accounts.find((account) => String(account.id) === String(accountId))?.code || accountId
    );
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
        <h2 className="text-2xl font-bold text-gray-900">Comptabilité</h2>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Débit</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.total_debit.toFixed(2)} FCFA
                </p>
              </div>
              <FiTrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Crédit</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.total_credit.toFixed(2)} FCFA
                </p>
              </div>
              <FiTrendingDown className="w-8 h-8 text-red-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Solde</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.balance.toFixed(2)} FCFA
                </p>
              </div>
              <FiDollarSign className="w-8 h-8 text-blue-500" />
            </div>
          </div>
        </div>

        {/* Ledger Entries Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Écritures récentes</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Compte dÇ¸bit
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Compte crÇ¸dit
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Description
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Débit
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Crédit
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {entries.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {format(new Date(entry.entry_date), 'dd/MM/yyyy')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {getAccountCode(entry.debit_account_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {getAccountCode(entry.credit_account_id)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">{entry.description}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600">
                      {entry.debit > 0 ? `${entry.debit.toFixed(2)} FCFA` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600">
                      {entry.credit > 0 ? `${entry.credit.toFixed(2)} FCFA` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {entries.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                Aucune écriture comptable.
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
