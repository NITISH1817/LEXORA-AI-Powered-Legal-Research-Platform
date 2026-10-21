import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Scale, Lock, Mail, Eye, EyeOff, ShieldAlert, AlertCircle } from 'lucide-react';
import { getErrorMessage } from '../../api/client';
import Button from '../ui/Button';
import Input from '../ui/Input';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Please provide both your institutional email and password.');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      await login(email.trim().toLowerCase(), password);
      navigate('/');
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Authentication failed. Please verify your email and password.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#080c14] flex items-center justify-center p-4 font-sans relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <main className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl relative z-10 backdrop-blur-md">
        {/* Brand header */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-blue-500/20 mb-3">
            <Scale size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-serif font-bold text-white tracking-widest leading-none">
            LEXORA
          </h1>
          <p className="text-xs text-slate-400 mt-1.5 tracking-wide">
            AI-Powered Legal Intelligence & Research Platform
          </p>
        </div>

        {/* Supervised Pilot Advisory */}
        <div className="mb-6 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-2.5">
          <ShieldAlert size={16} className="text-amber-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold block text-amber-200">Controlled Research Pilot</span>
            Access is restricted to authorized legal researchers, advocates, and participating institutional cohorts.
          </div>
        </div>

        {error && (
          <div
            role="alert"
            className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5"
          >
            <AlertCircle size={16} className="text-rose-400 shrink-0 mt-0.5" />
            <p className="flex-1 leading-relaxed">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <Input
            label="Institutional Email"
            id="login-email"
            type="email"
            name="username"
            placeholder="advocate@firm.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="username"
            icon={<Mail size={16} />}
            disabled={isSubmitting}
          />

          <Input
            label="Password"
            id="login-password"
            type={showPassword ? 'text' : 'password'}
            name="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            icon={<Lock size={16} />}
            disabled={isSubmitting}
            rightElement={
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-slate-400 hover:text-white p-1 rounded transition-colors"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            }
          />

          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isSubmitting}
              className="w-full font-semibold shadow-lg shadow-blue-500/20"
            >
              Sign In to Legal Workspace
            </Button>
          </div>
        </form>

        <div className="mt-6 pt-5 border-t border-slate-800 text-center">
          <p className="text-xs text-slate-400">
            Have an authorized invitation code?{' '}
            <Link to="/register" className="text-blue-400 hover:underline font-semibold">
              Register Pilot Account
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
