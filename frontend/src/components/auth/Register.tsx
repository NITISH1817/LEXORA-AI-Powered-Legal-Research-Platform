import React, { useState } from 'react';
import axios from 'axios';
import { ShieldCheck } from 'lucide-react';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/register', {
        email, password, full_name: fullName
      });
      setSuccess(true);
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed.");
    }
  };

  if (success) {
    return (
      <div className="h-screen w-screen bg-[#0b0f19] flex items-center justify-center font-sans">
        <div className="bg-slate-900/80 p-8 border border-slate-800 rounded-xl text-center max-w-sm w-full text-emerald-400">
          Account created! Redirecting to login...
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-[#0b0f19] flex items-center justify-center font-sans">
      <div className="bg-slate-900/80 p-8 border border-slate-800 rounded-xl text-center max-w-sm w-full">
        <ShieldCheck className="mx-auto text-primary mb-4" size={48} />
        <h1 className="text-2xl font-serif font-bold text-white mb-2 tracking-widest">LEXORA</h1>
        <p className="text-slate-400 text-sm mb-6">Create your workspace</p>
        
        {error && <div className="bg-red-900/30 border border-red-800 text-red-400 text-xs p-2 rounded mb-4">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input 
            type="text" 
            placeholder="Full Name" 
            className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-primary"
            value={fullName} onChange={e => setFullName(e.target.value)}
            required
          />
          <input 
            type="email" 
            placeholder="Email Address" 
            className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-primary"
            value={email} onChange={e => setEmail(e.target.value)}
            required
          />
          <input 
            type="password" 
            placeholder="Password (min 8 chars)" 
            className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-primary"
            value={password} onChange={e => setPassword(e.target.value)}
            required minLength={8}
          />
          <button type="submit" className="w-full bg-primary text-black font-bold py-2 rounded transition-colors hover:bg-primary/90">
            Register
          </button>
        </form>
        <div className="mt-6 text-xs text-slate-500">
          Already have an account? <a href="/login" className="text-primary hover:underline">Sign In</a>
        </div>
      </div>
    </div>
  );
}
