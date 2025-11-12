'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://imss-pension-api.onrender.com';

export default function AdminPanel() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [invitations, setInvitations] = useState<any[]>([]);
  const [newEmail, setNewEmail] = useState('');
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    // Buscar token en cookies O localStorage
    const token = Cookies.get('token') || localStorage.getItem('token');
    
    if (!token) {
      router.push('/login');
      return;
    }
    
    loadData(token);
  };

  const loadData = async (token: string) => {
    setLoading(true);

    try {
      const [statsRes, invitesRes] = await Promise.all([
        fetch(`${API_URL}/admin/invitations/stats/summary`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/admin/invitations`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (invitesRes.ok) {
        const data = await invitesRes.json();
        setInvitations(data.invitations || []);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setMessage({ type: '', text: '' });

    const token = Cookies.get('token') || localStorage.getItem('token');

    try {
      const response = await fetch(`${API_URL}/admin/invitations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ email: newEmail })
      });

      if (response.ok) {
        setMessage({ type: 'success', text: `✅ Invitación enviada a ${newEmail}` });
        setNewEmail('');
        if (token) loadData(token);
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Error' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error de conexión' });
    } finally {
      setSending(false);
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    }
  };

  const copyLink = (url: string) => {
    navigator.clipboard.writeText(url);
    setMessage({ type: 'success', text: '✅ Link copiado' });
    setTimeout(() => setMessage({ type: '', text: '' }), 2000);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Panel de Administración</h1>

      {message.text && (
        <div className={`mb-6 p-4 rounded-lg ${
          message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        }`}>
          {message.text}
        </div>
      )}

      {/* Estadísticas */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-600">Total Invitaciones</h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">{stats.total_invitations}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-600">Pendientes</h3>
            <p className="text-3xl font-bold text-orange-600 mt-2">{stats.pending_invitations}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-600">Usadas</h3>
            <p className="text-3xl font-bold text-green-600 mt-2">{stats.used_invitations}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-600">Expiradas</h3>
            <p className="text-3xl font-bold text-red-600 mt-2">{stats.expired_invitations}</p>
          </div>
        </div>
      )}

      {/* Formulario */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-xl font-semibold mb-4">Enviar Nueva Invitación</h2>
        <form onSubmit={sendInvitation} className="flex gap-4">
          <input
            type="email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            placeholder="email@ejemplo.com"
            required
            className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={sending}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {sending ? 'Enviando...' : 'Enviar'}
          </button>
        </form>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">Invitaciones Recientes</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {invitations.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                    No hay invitaciones aún
                  </td>
                </tr>
              ) : (
                invitations.map((inv) => (
                  <tr key={inv.id}>
                    <td className="px-6 py-4 text-sm text-gray-900">{inv.email}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        inv.status === 'used' ? 'bg-green-100 text-green-800' :
                        inv.status === 'expired' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {inv.status === 'used' ? '✅ Usado' :
                         inv.status === 'expired' ? '⏰ Expirado' :
                         '⏳ Pendiente'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(inv.created_at).toLocaleDateString('es-MX')}
                    </td>
                    <td className="px-6 py-4 text-right text-sm">
                      {inv.status === 'pending' && (
                        <button
                          onClick={() => copyLink(inv.invitation_url)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          📋 Copiar link
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
