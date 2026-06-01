import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Eye, 
  EyeOff, 
  LoaderCircle, 
  Shield, 
  KeyRound, 
  Cpu, 
  Terminal, 
  Sparkles,
  Activity,
  Lock,
  Network,
  Binary,
  User
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import useAuthStore from '@/store/authStore';
import api from '@/services/api';

const loginSchema = z.object({
  email: z.string().email({ message: 'Invalid email address.' }),
  password: z.string().min(8, { message: 'Password must be at least 8 characters.' }),
  role: z.enum(['admin', 'user']),
});

// Subtle cyber synthesizer sound engine
const playCyberBeep = (freq, dur) => {
  if (typeof window === 'undefined') return;
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.03, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + dur);
    osc.start();
    osc.stop(audioCtx.currentTime + dur);
  } catch (e) {}
};

const LoginPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState(null);
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  // Decorative live logs
  const [authPanelLogs, setAuthPanelLogs] = useState([
    { id: 1, text: '[*] Kyber-1024 operational tunnel active...', color: 'text-pn-neon-blue' },
    { id: 2, text: '[*] API Gateway proxy balance standard - EPS: 140', color: 'text-emerald-400' },
    { id: 3, text: '[*] Endpoint honeypots monitoring ports: 22, 445', color: 'text-pn-neon-blue' }
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      const logs = [
        { text: '[+] Rotating Zero-Trust ephemeral handshake key', color: 'text-emerald-400' },
        { text: '[+] eBPF hypervisor monitors reporting SECURE', color: 'text-pn-neon-blue' },
        { text: '[!] Classical signature verification flagged legacy key', color: 'text-amber-400' },
        { text: '[+] Decoy honeypot intercepted safe ping on port 22', color: 'text-emerald-400' }
      ];
      const selected = logs[Math.floor(Math.random() * logs.length)];
      setAuthPanelLogs(prev => [
        { id: Date.now(), text: selected.text, color: selected.color },
        ...prev.slice(0, 3)
      ]);
    }, 4500);
    return () => clearInterval(interval);
  }, []);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
    mode: 'onChange',
    defaultValues: {
      role: 'user'
    }
  });

  const selectedRole = watch('role');

  const onSubmit = async (data) => {
    setApiError(null);
    playCyberBeep(520, 0.1);
    try {
      const params = new URLSearchParams();
      params.append('username', data.email);
      params.append('password', data.password);

      const response = await api.post('/auth/token', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      login(response);
      playCyberBeep(880, 0.2);
      if (response.user?.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      if (err.code === '2FA_REQUIRED' || err.message === '2FA required') {
        sessionStorage.setItem('mfa_username', data.email);
        sessionStorage.setItem('mfa_password', data.password);
        playCyberBeep(700, 0.15);
        navigate('/mfa-challenge');
        return;
      }
      playCyberBeep(180, 0.35);
      setApiError(err.message || 'Authentication credentials refused. Verify keys.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#05050A] text-[#E0E0E0] p-4 relative overflow-hidden font-sans">
      
      {/* Background Graphic elements */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(0,240,255,0.03),transparent_50%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_80%,rgba(138,43,226,0.03),transparent_50%)] pointer-events-none" />
      <div className="absolute inset-0 z-0 h-full w-full bg-[linear-gradient(to_right,rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:24px_24px] opacity-40 pointer-events-none"></div>

      <div className="relative z-10 w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        
        {/* Left Side: Advanced Cybersecurity HUD (lg:col-span-6) */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="lg:col-span-6 rounded-2xl bg-[#090911]/85 border border-[#33334D]/80 backdrop-blur-xl p-8 flex flex-col justify-between hidden lg:flex min-h-[500px]"
        >
          <div>
            <div className="flex items-center gap-2 mb-8">
              <div className="p-2 bg-primary/10 border border-primary/20 rounded-xl text-primary animate-pulse">
                <Shield size={24} />
              </div>
              <span className="text-sm font-black font-heading text-white tracking-widest uppercase">PhantomNet XDR</span>
            </div>

            <h2 className="text-3xl font-extrabold font-heading text-white mb-4 leading-tight tracking-tight">
              Defend Your Grid at <span className="bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text">Machine Speed</span>
            </h2>
            <p className="text-xs text-pn-text-muted leading-relaxed mb-6 font-mono">
              Hyperscale event ingestion normalizes security signals, audits keys against Shor post-quantum readiness, and dispatches automated containment blocks globally.
            </p>
          </div>

          {/* Interactive rolling console */}
          <div className="space-y-3 font-mono text-[10px] bg-[#020204]/90 p-4 border border-white/5 rounded-xl">
            <span className="text-[9px] font-bold text-pn-text-muted uppercase tracking-widest block mb-2 border-b border-white/5 pb-1 flex items-center gap-1.5">
              <Activity size={10} className="text-pn-neon-blue animate-pulse" />
              Ingestion Stream Diagnostics
            </span>
            <div className="space-y-1.5 text-left">
              {authPanelLogs.map((log) => (
                <div key={log.id} className={`${log.color} truncate`}>
                  {log.text}
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Right Side: Immersive Login Form (lg:col-span-6) */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="lg:col-span-6 rounded-2xl bg-[#0d0d1e]/40 border border-[#33334D] backdrop-blur-xl p-8 flex flex-col justify-between min-h-[500px]"
        >
          <div className="space-y-6">
            <div className="text-center lg:text-left">
              <h1 className="text-2xl font-black font-heading text-white tracking-tight uppercase">SOC Commander Portal</h1>
              <p className="text-xs text-pn-text-muted mt-1">Authenticate credential keys to access global operations grid.</p>
            </div>

            <AnimatePresence>
              {apiError && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="p-3 text-[10px] font-mono text-center text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl"
                  role="alert"
                >
                  {apiError}
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 text-left font-mono">
              <div className="space-y-1">
                <Label htmlFor="email" className="text-[10px] text-pn-text-muted uppercase font-bold">Grid Email ID</Label>
                <Input 
                  id="email" 
                  type="email" 
                  {...register('email')} 
                  placeholder="admin@phantomnet.local" 
                  className="bg-[#05050A] border-pn-border text-xs focus:border-pn-neon-blue focus:ring-1 focus:ring-pn-neon-blue text-white rounded-lg h-10 placeholder:text-[#555]"
                />
                {errors.email && <p className="text-rose-400 text-[10px] mt-1">{errors.email.message}</p>}
              </div>

              <div className="space-y-1 relative">
                <Label htmlFor="password" className="text-[10px] text-pn-text-muted uppercase font-bold">Cryptographic Password</Label>
                <Input 
                  id="password" 
                  type={showPassword ? 'text' : 'password'} 
                  {...register('password')} 
                  placeholder="••••••••" 
                  className="bg-[#05050A] border-pn-border text-xs focus:border-pn-neon-blue focus:ring-1 focus:ring-pn-neon-blue text-white rounded-lg h-10 placeholder:text-[#555]"
                />
                <button
                  type="button"
                  onClick={() => {
                    playCyberBeep(650, 0.05);
                    setShowPassword(!showPassword);
                  }}
                  className="absolute right-3 top-[2.2rem] text-pn-text-muted hover:text-pn-neon-blue transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
                {errors.password && <p className="text-rose-400 text-[10px] mt-1">{errors.password.message}</p>}
              </div>

              {/* Role custom radio buttons */}
              <div className="space-y-1">
                <Label className="text-[10px] text-pn-text-muted uppercase font-bold">Access Authority Role</Label>
                <div className="grid grid-cols-2 gap-3 mt-1.5">
                  <button
                    type="button"
                    onClick={() => {
                      playCyberBeep(450, 0.05);
                      setValue('role', 'user');
                    }}
                    className={`py-2 px-3 border rounded-lg text-xs font-bold transition-all text-center flex justify-center items-center gap-1.5 ${
                      selectedRole === 'user'
                        ? 'border-pn-neon-blue bg-pn-neon-blue/10 text-white font-extrabold shadow-[0_0_10px_rgba(0,240,255,0.1)]'
                        : 'border-pn-border text-pn-text-muted hover:border-pn-border/80'
                    }`}
                  >
                    <User size={12} />
                    User Shield
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      playCyberBeep(450, 0.05);
                      setValue('role', 'admin');
                    }}
                    className={`py-2 px-3 border rounded-lg text-xs font-bold transition-all text-center flex justify-center items-center gap-1.5 ${
                      selectedRole === 'admin'
                        ? 'border-pn-neon-blue bg-pn-neon-blue/10 text-white font-extrabold shadow-[0_0_10px_rgba(0,240,255,0.1)]'
                        : 'border-pn-border text-pn-text-muted hover:border-pn-border/80'
                    }`}
                  >
                    <Lock size={12} />
                    Root Admin
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-end pt-1">
                <Link to="/forgot-password" className="text-[10px] text-primary hover:underline hover:text-pn-neon-blue transition-colors">
                  Reset Lost Credentials?
                </Link>
              </div>

              <Button 
                type="submit" 
                className="w-full h-11 bg-pn-neon-blue text-pn-dark-blue hover:bg-pn-electric-purple hover:text-white transition-all text-xs font-bold rounded-lg mt-3 flex justify-center items-center gap-2 shadow-[0_0_15px_rgba(0,240,255,0.15)]" 
                disabled={isSubmitting}
              >
                {isSubmitting ? <LoaderCircle className="animate-spin" size={16} /> : 'Authenticate Credentials'}
              </Button>
            </form>
          </div>

          <div className="text-center text-[10px] font-mono text-pn-text-muted mt-6 border-t border-pn-border/30 pt-4 space-y-2">
            <div>
              Access restricted to authorized operational operators. Handshakes logged cryptographically.
            </div>
            <div>
              New operator?{' '}
              <Link to="/register" className="text-primary hover:text-pn-neon-blue hover:underline transition-all">
                Register Grid Account
              </Link>
            </div>
          </div>
        </motion.div>

      </div>
    </div>
  );
};

export default LoginPage;
