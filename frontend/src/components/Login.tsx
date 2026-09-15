import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, Mail, Loader2, Layout } from 'lucide-react';
import axios from 'axios';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/login', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            login(res.data.access_token);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-background to-background z-0"></div>
            
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md bg-surface/80 backdrop-blur-md border border-border rounded-xl shadow-2xl p-8 z-10 relative overflow-hidden"
            >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-600 via-primary to-cyan-400"></div>
                
                <div className="flex flex-col items-center mb-8">
                    <div className="w-12 h-12 bg-primary/20 border border-primary/50 rounded-lg flex items-center justify-center mb-4">
                        <Layout className="text-primary w-6 h-6" />
                    </div>
                    <h1 className="text-2xl font-semibold text-white tracking-wide">LEGAL INTEL WORKSPACE</h1>
                    <p className="text-textMuted text-sm mt-2 flex items-center gap-2">
                        <Shield size={14} className="text-emerald-500" />
                        Secure Authorized Access Only
                    </p>
                </div>

                {error && (
                    <motion.div 
                        initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                        className="bg-rose-500/10 border border-rose-500/50 text-rose-400 text-sm p-3 rounded-md mb-6"
                    >
                        {error}
                    </motion.div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-xs font-medium text-textMuted uppercase tracking-wider mb-2">Email Address</label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-textMuted" size={16} />
                            <input 
                                type="email" 
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full bg-slate-900 border border-border text-white rounded-md py-2.5 pl-10 pr-4 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                                placeholder="lawyer@firm.com"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-textMuted uppercase tracking-wider mb-2">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-textMuted" size={16} />
                            <input 
                                type="password" 
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-slate-900 border border-border text-white rounded-md py-2.5 pl-10 pr-4 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    <button 
                        type="submit" 
                        disabled={isLoading}
                        className="w-full bg-primary hover:bg-blue-600 text-white font-medium py-2.5 rounded-md transition-colors flex justify-center items-center gap-2 disabled:opacity-50 mt-4"
                    >
                        {isLoading ? <Loader2 size={18} className="animate-spin" /> : "Authenticate"}
                    </button>
                </form>
            </motion.div>
        </div>
    );
};

export default Login;
