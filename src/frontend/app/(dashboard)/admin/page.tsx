'use client';
import Cookies from 'js-cookie';

import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { User, Invitation } from '@/types';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Users, 
  CreditCard, 
  Mail, 
  TrendingUp, 
  Plus,
  Loader2,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://imss-pension-api.onrender.com';

interface DashboardStats {
  total_users: number;
  active_users: number;
  total_credits_distributed: number;
  pending_invitations: number;
}

interface User {
  id: number;
  email: string;
  credits: number;
  credits_expire_at: string | null;
  company_size: string | null;
  created_at: string;
  is_active: boolean;
}

interface Invitation {
  id: number;
  email: string;
  token: string;
  initial_credits: number;
  credits_valid_days: number;
  used: boolean;
  created_at: string;
}

interface AddCreditsForm {
  userId: number;
  userEmail: string;
  credits: number;
  days: number;
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [inviteForm, setInviteForm] = useState({
    email: '',
    initial_credits: 10,
    credits_valid_days: 30
  });

  const [creditsDialog, setCreditsDialog] = useState(false);
  const [addCreditsForm, setAddCreditsForm] = useState<AddCreditsForm>({
    userId: 0,
    userEmail: '',
    credits: 10,
    days: 30
  });

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/admin/dashboard/stats`, {
        headers: {
          'Authorization': `Bearer ${Cookies.get('token') || localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_URL}/admin/users`, {
        headers: {
          'Authorization': `Bearer ${Cookies.get('token') || localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (err) {
      console.error('Error fetching users:', err);
    }
  };

  const fetchInvitations = async () => {
    try {
      const response = await fetch(`${API_URL}/admin/invitations`, {
        headers: {
          'Authorization': `Bearer ${Cookies.get('token') || localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setInvitations(data.invitations || data);
      }
    } catch (err) {
      console.error('Error fetching invitations:', err);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchUsers();
    fetchInvitations();
  }, []);

  const handleCreateInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_URL}/admin/invitations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${Cookies.get('token') || localStorage.getItem('token')}`
        },
        body: JSON.stringify(inviteForm)
      });

      if (response.ok) {
        setSuccess(`Invitación enviada a ${inviteForm.email} con ${inviteForm.initial_credits} créditos válidos por ${inviteForm.credits_valid_days} días`);
        setInviteForm({ email: '', initial_credits: 10, credits_valid_days: 30 });
        fetchInvitations();
        fetchStats();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Error al crear invitación');
      }
    } catch (err) {
      setError('Error de conexión al crear invitación');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCredits = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_URL}/admin/users/credits`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${Cookies.get('token') || localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          user_id: addCreditsForm.userId,
          credits: addCreditsForm.credits,
          valid_days: addCreditsForm.days
        })
      });

      if (response.ok) {
        setSuccess(`Se agregaron ${addCreditsForm.credits} créditos a ${addCreditsForm.userEmail}`);
        setCreditsDialog(false);
        fetchUsers();
        fetchStats();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Error al agregar créditos');
      }
    } catch (err) {
      setError('Error de conexión al agregar créditos');
    } finally {
      setLoading(false);
    }
  };

  const openAddCreditsDialog = (user: User) => {
    setAddCreditsForm({
      userId: user.id,
      userEmail: user.email,
      credits: 10,
      days: 30
    });
    setCreditsDialog(true);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Panel de Administración</h1>
        <p className="text-muted-foreground">
          Gestiona usuarios, créditos e invitaciones de Pensionasoft
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mb-6 border-green-500 text-green-700">
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 lg:w-[600px]">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="users">Usuarios</TabsTrigger>
          <TabsTrigger value="invitations">Invitaciones</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Usuarios</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_users || 0}</div>
                <p className="text-xs text-muted-foreground">Usuarios registrados</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Usuarios Activos</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.active_users || 0}</div>
                <p className="text-xs text-muted-foreground">Con créditos disponibles</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Créditos Distribuidos</CardTitle>
                <CreditCard className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_credits_distributed || 0}</div>
                <p className="text-xs text-muted-foreground">Créditos totales otorgados</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Invitaciones Pendientes</CardTitle>
                <Mail className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.pending_invitations || 0}</div>
                <p className="text-xs text-muted-foreground">Sin usar</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="users" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Gestión de Usuarios</CardTitle>
              <CardDescription>Lista de todos los usuarios registrados y sus créditos</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Créditos</TableHead>
                      <TableHead>Tamaño Empresa</TableHead>
                      <TableHead>Expiración</TableHead>
                      <TableHead>Registro</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground">
                          No hay usuarios registrados
                        </TableCell>
                      </TableRow>
                    ) : (
                      users.map((user) => (
                        <TableRow key={user.id}>
                          <TableCell className="font-medium">{user.email}</TableCell>
                          <TableCell>
                            <span className={`font-semibold ${user.credits > 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {user.credits}
                            </span>
                          </TableCell>
                          <TableCell>{user.company_size || 'No especificado'}</TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {user.credits_expire_at
                              ? formatDistanceToNow(new Date(user.credits_expire_at), {
                                  addSuffix: true,
                                  locale: es
                                })
                              : 'Sin expiración'}
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {formatDistanceToNow(new Date(user.created_at), {
                              addSuffix: true,
                              locale: es
                            })}
                          </TableCell>
                          <TableCell className="text-right">
                            <Button className="h-9 px-3" variant="outline" onClick={() => openAddCreditsDialog(user)}>
                              <Plus className="h-4 w-4 mr-1" />
                              Agregar Créditos
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="invitations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Crear Nueva Invitación</CardTitle>
              <CardDescription>Envía una invitación con créditos personalizados</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateInvitation} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="usuario@empresa.com"
                      value={inviteForm.email}
                      onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="initial_credits">
                      Créditos Iniciales
                      <span className="text-xs text-muted-foreground ml-2">(1-1000)</span>
                    </Label>
                    <Input
                      id="initial_credits"
                      type="number"
                      min="1"
                      max="1000"
                      value={inviteForm.initial_credits}
                      onChange={(e) => setInviteForm({ 
                        ...inviteForm, 
                        initial_credits: parseInt(e.target.value) 
                      })}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="credits_valid_days">
                      Días de Validez
                      <span className="text-xs text-muted-foreground ml-2">(1-365)</span>
                    </Label>
                    <Input
                      id="credits_valid_days"
                      type="number"
                      min="1"
                      max="365"
                      value={inviteForm.credits_valid_days}
                      onChange={(e) => setInviteForm({ 
                        ...inviteForm, 
                        credits_valid_days: parseInt(e.target.value) 
                      })}
                      required
                    />
                  </div>
                </div>

                <Button type="submit" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <Mail className="mr-2 h-4 w-4" />
                      Enviar Invitación
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Invitaciones Enviadas</CardTitle>
              <CardDescription>Historial de todas las invitaciones</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Créditos</TableHead>
                      <TableHead>Días Validez</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead>Fecha</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invitations.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground">
                          No hay invitaciones enviadas
                        </TableCell>
                      </TableRow>
                    ) : (
                      invitations.map((invitation) => {
                        const invitationUrl = `${window.location.origin}/register?token=${invitation.token}`;
                        
                        const copyLink = () => {
                          navigator.clipboard.writeText(invitationUrl);
                          setSuccess('Link copiado al portapapeles');
                          setTimeout(() => setSuccess(null), 2000);
                        };

                        const resendEmail = async () => {
                          setLoading(true);
                          try {
                            const response = await fetch(`${API_URL}/admin/invitations/${invitation.id}/resend?expiration_days=7`, {
                              method: 'POST',
                              headers: {
                                'Authorization': `Bearer ${Cookies.get('token') || localStorage.getItem('token')}`
                              }
                            });
                            
                            if (response.ok) {
                              setSuccess(`Email reenviado a ${invitation.email}`);
                            } else {
                              setError('Error al reenviar email');
                            }
                          } catch (err) {
                            setError('Error de conexión');
                          } finally {
                            setLoading(false);
                          }
                        };

                        return (
                          <TableRow key={invitation.id}>
                            <TableCell className="font-medium">{invitation.email}</TableCell>
                            <TableCell>{invitation.initial_credits}</TableCell>
                            <TableCell>{invitation.credits_valid_days} días</TableCell>
                            <TableCell>
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                invitation.status === "used"
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {invitation.status === "used" ? "Usada" : "Pendiente"}
                              </span>
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {formatDistanceToNow(new Date(invitation.created_at), {
                                addSuffix: true,
                                locale: es
                              })}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex items-center justify-end gap-2">
                                {invitation.status === "pending" && (
                                  <>
                                    <Button
                                      className="h-9 px-3"
                                      variant="outline"
                                      onClick={copyLink}
                                      title="Copiar link de invitación"
                                    >
                                      📋
                                    </Button>
                                    <Button
                                      className="h-9 px-3"
                                      variant="outline"
                                      onClick={resendEmail}
                                      disabled={loading}
                                      title="Reenviar email"
                                    >
                                      📧
                                    </Button>
                                  </>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={creditsDialog} onOpenChange={setCreditsDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Agregar Créditos</DialogTitle>
            <DialogDescription>
              Agregar créditos al usuario: {addCreditsForm.userEmail}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="dialog-credits">
                Cantidad de Créditos
                <span className="text-xs text-muted-foreground ml-2">(1-1000)</span>
              </Label>
              <Input
                id="dialog-credits"
                type="number"
                min="1"
                max="1000"
                value={addCreditsForm.credits}
                onChange={(e) => setAddCreditsForm({
                  ...addCreditsForm,
                  credits: parseInt(e.target.value)
                })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="dialog-days">
                Días de Validez
                <span className="text-xs text-muted-foreground ml-2">(1-365)</span>
              </Label>
              <Input
                id="dialog-days"
                type="number"
                min="1"
                max="365"
                value={addCreditsForm.days}
                onChange={(e) => setAddCreditsForm({
                  ...addCreditsForm,
                  days: parseInt(e.target.value)
                })}
              />
            </div>

            <div className="rounded-lg bg-muted p-4">
              <p className="text-sm">
                <strong>Resumen:</strong> Se agregarán{' '}
                <span className="font-bold text-green-600">{addCreditsForm.credits} créditos</span>{' '}
                válidos por <span className="font-bold">{addCreditsForm.days} días</span>
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCreditsDialog(false)} disabled={loading}>
              Cancelar
            </Button>
            <Button onClick={handleAddCredits} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Procesando...
                </>
              ) : (
                'Agregar Créditos'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
