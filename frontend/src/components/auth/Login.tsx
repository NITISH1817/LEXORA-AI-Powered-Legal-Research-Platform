import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      // Auth context redirects to workspace
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid email or password.");
    }
  };

  return (
    <div className="h-screen w-screen bg-[#0b0f19] flex items-center justify-center font-sans">
      <div className="bg-slate-900/80 p-8 border border-slate-800 rounded-xl text-center max-w-sm w-full">
        <ShieldCheck className="mx-auto text-primary mb-4" size={48} />
        <h1 className="text-2xl font-serif font-bold text-white mb-2 tracking-widest">LEXORA</h1>
        <p className="text-slate-400 text-sm mb-6">Unified Legal Research Platform</p>
        
        {error && <div className="bg-red-900/30 border border-red-800 text-red-400 text-xs p-2 rounded mb-4">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input 
            type="email" 
            placeholder="Email Address" 
            className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-primary"
            value={email} onChange={e => setEmail(e.target.value)}
            required
          />
          <input 
            type="password" 
            placeholder="Password" 
            className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-primary"
            value={password} onChange={e => setPassword(e.target.value)}
            required
          />
          <button type="submit" className="w-full bg-primary text-black font-bold py-2 rounded transition-colors hover:bg-primary/90">
            Sign In
          </button>
        </form>
        <div className="mt-6 text-xs text-slate-500">
          Don't have an account? <a href="/register" className="text-primary hover:underline">Register</a>
        </div>
      </div>
    </div>
  );
}
