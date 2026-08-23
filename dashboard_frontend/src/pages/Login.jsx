import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, LoaderCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import useAuthStore from '@/store/authStore';
import api from '@/services/api';

const loginSchema = z.object({
  email: z.string().email({ message: 'Enter a valid email address.' }),
  password: z.string().min(8, { message: 'Password must be at least 8 characters.' }),
});

const LoginPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState(null);
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(loginSchema), mode: 'onChange',
  });

  const onSubmit = async (data) => {
    setApiError(null);
    try {
      const params = new URLSearchParams();
      params.append('username', data.email);
      params.append('password', data.password);
      const response = await api.post('/auth/token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      login(response);
      navigate(response.user?.role === 'admin' ? '/admin/dashboard' : '/dashboard');
    } catch (err) {
      if (err.code === '2FA_REQUIRED' || err.message === '2FA required') {
        sessionStorage.setItem('mfa_username', data.email);
        sessionStorage.setItem('mfa_password', data.password);
        navigate('/mfa-challenge');
        return;
      }
      setApiError(err.message || 'Authentication credentials were refused.');
    }
  };

  return <main className="flex min-h-screen items-center justify-center bg-background p-4 text-foreground">
    <section className="w-full max-w-md rounded-xl border border-border bg-panel-solid p-8 shadow-xl">
      <h1 className="text-2xl font-bold">PhantomNet Sign In</h1>
      <p className="mt-2 text-sm text-muted-foreground">Authentication is evaluated by the server. Access roles are assigned by server-side policy, not selected in this form.</p>
      {apiError && <p role="alert" className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{apiError}</p>}
      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
        <div><Label htmlFor="email">Email</Label><Input id="email" type="email" autoComplete="username" {...register('email')} />{errors.email && <p className="mt-1 text-sm text-destructive">{errors.email.message}</p>}</div>
        <div className="relative"><Label htmlFor="password">Password</Label><Input id="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" {...register('password')} />
          <button type="button" aria-label="Toggle password visibility" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-8 text-muted-foreground">{showPassword ? <EyeOff size={16} /> : <Eye size={16} />}</button>
          {errors.password && <p className="mt-1 text-sm text-destructive">{errors.password.message}</p>}</div>
        <div className="flex justify-end"><Link to="/forgot-password" className="text-sm text-primary hover:underline">Reset password</Link></div>
        <Button type="submit" className="w-full" disabled={isSubmitting}>{isSubmitting ? <LoaderCircle className="animate-spin" size={16} /> : 'Sign in'}</Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">New user? <Link to="/register" className="text-primary hover:underline">Register an account</Link></p>
    </section>
  </main>;
};

export default LoginPage;
