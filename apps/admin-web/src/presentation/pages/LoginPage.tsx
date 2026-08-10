import React, { useState } from 'react';
import { Lock, Mail, AlertCircle } from 'lucide-react';
import { useLogin } from '../hooks/useAuth';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const login = useLogin();

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    login.mutate({ email, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 font-sans px-4">
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 w-full max-w-sm"
      >
        <div className="w-12 h-12 rounded-xl bg-red-600 flex items-center justify-center font-black text-xl text-white mb-4 shadow-lg shadow-red-500/30">
          R
        </div>
        <h1 className="text-lg font-bold text-gray-900 mb-1">Painel do Gestor</h1>
        <p className="text-xs text-gray-500 mb-6">Entre com seu e-mail e senha cadastrados.</p>

        {login.isError && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 text-xs font-semibold rounded-xl px-3 py-2 mb-4">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{login.error.message}</span>
          </div>
        )}

        <label className="text-xs font-semibold text-gray-700 block mb-1">E-mail</label>
        <div className="relative mb-4">
          <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="voce@restaurante.com"
            className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500"
          />
        </div>

        <label className="text-xs font-semibold text-gray-700 block mb-1">Senha</label>
        <div className="relative mb-6">
          <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500"
          />
        </div>

        <button
          type="submit"
          disabled={login.isPending}
          className="w-full bg-red-600 disabled:bg-red-300 text-white font-bold text-sm px-5 py-2.5 rounded-xl shadow-md"
        >
          {login.isPending ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  );
};
