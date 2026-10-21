import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Scale, Lock, Mail, User, Key, Eye, EyeOff, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';
import apiClient, { getErrorMessage } from '../../api/client';
import Button from '../ui/Button';
import Input from '../ui/Input';

export default function Register() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [invitationCode, setInvitationCode] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!fullName.trim() || !email.trim() || !password || !invitationCode.trim()) {
      setError('All fields including the institutional invitation code are required.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters in length.');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      await apiClient.post('/api/auth/register', {
        email: email.trim().toLowerCase(),
        password,
        full_name: fullName.trim(),
        invitation_code: invitationCode.trim(),
      });
      setSuccess(true);
    } catch (err: unknown) {
      setError(
        getErrorMessage(
          err,
          'Registration failed. Ensure you have entered a valid institutional invitation code.'
        )
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen w-full bg-[#080c14] flex items-center justify-center p-4 font-sans">
        <main className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center shadow-2xl">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-4 shadow-inner">
            <CheckCircle2 size={24} />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Account Provisioned</h2>
          <p className="text-xs sm:text-sm text-slate-400 mb-6 leading-relaxed font-sans">
            Your pilot workspace profile for <span className="text-slate-200 font-semibold">{email}</span> has been authorized.
          </p>
          <Button
            type="button"
            variant="primary"
            size="md"
            onClick={() => navigate('/login')}
            className="w-full"
          >
            Proceed to Sign In
          </Button>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#080c14] flex items-center justify-center p-4 font-sans relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <main className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl relative z-10 backdrop-blur-md">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-blue-500/20 mb-3">
            <Scale size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-serif font-bold text-white tracking-widest leading-none">
            LEXORA
          </h1>
          <p className="text-xs text-slate-400 mt-1.5">
            Supervised Institutional Pilot Registration
          </p>
        </div>

        {/* Controlled Pilot Access Notice */}
        <div className="mb-6 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-2.5">
          <ShieldAlert size={16} className="text-amber-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold block text-amber-200">Institutional Access Restricted</span>
            Registration requires an authorized invitation code provided by the institutional coordinator.
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
            label="Full Legal Name"
            id="register-name"
            type="text"
            placeholder="Advocate Anita Desai"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            autoComplete="name"
            icon={<User size={16} />}
            disabled={isSubmitting}
          />

          <Input
            label="Institutional Email"
            id="register-email"
            type="email"
            placeholder="advocate@firm.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            icon={<Mail size={16} />}
            disabled={isSubmitting}
          />

          <Input
            label="Password (min. 8 characters)"
            id="register-password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
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

          <Input
            label="Pilot Invitation Code"
            id="register-code"
            type="text"
            placeholder="e.g. LEXORA-PILOT-2026-SUPERVISED"
            value={invitationCode}
            onChange={(e) => setInvitationCode(e.target.value)}
            required
            icon={<Key size={16} />}
            helperText="Provided to authorized participating chambers and institutional research teams."
            disabled={isSubmitting}
          />

          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isSubmitting}
              className="w-full font-semibold shadow-lg shadow-blue-500/20"
            >
              Authorize & Provision Account
            </Button>
          </div>
        </form>

        <div className="mt-6 pt-5 border-t border-slate-800 text-center">
          <p className="text-xs text-slate-400">
            Already authorized?{' '}
            <Link to="/login" className="text-blue-400 hover:underline font-semibold">
              Return to Sign In
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
