import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, LoaderCircle } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import useAuthStore from '@/store/authStore';
import api from '@/services/api';

const loginSchema = z.object({
  email: z.string().email({ message: 'Invalid email address.' }),
  password: z.string().min(8, { message: 'Password must be at least 8 characters.' }),
  role: z.enum(['admin', 'user']),
});

const LoginPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState(null);
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
    mode: 'onChange',
  });

  const onSubmit = async (data) => {
    setApiError(null);
    try {
      const response = await api.post('/auth/token', data); // Use /auth/token for login
      
      // Check for 2FA requirement
      if (response.headers['x-2fa-required'] === 'true') {
        // Store user/password temporarily for MFA challenge
        sessionStorage.setItem('mfa_username', data.email); // Backend uses username as email
        sessionStorage.setItem('mfa_password', data.password);
        navigate('/mfa-challenge');
        return;
      }

      login(response.data);
      if (response.data.user.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      if (err.response?.headers['x-2fa-required'] === 'true') {
        sessionStorage.setItem('mfa_username', data.email);
        sessionStorage.setItem('mfa_password', data.password);
        navigate('/mfa-challenge');
        return;
      }
      setApiError(err.response?.data?.detail || 'An unexpected error occurred. Please try again.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background text-foreground p-4">
      <div className="absolute inset-0 z-0 h-full w-full bg-background bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]"></div>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md p-8 space-y-6 bg-card rounded-2xl shadow-2xl shadow-primary/10 border border-border"
      >
        <div className="text-center">
          <h1 className="text-4xl font-bold text-primary">PhantomNet</h1>
          <p className="text-muted-foreground mt-2">Autonomous Cyber Defense Platform</p>
        </div>

        <AnimatePresence>
            {apiError && (
                 <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-3 mb-4 text-sm text-center text-destructive-foreground bg-destructive rounded-lg"
                    role="alert"
                >
                    {apiError}
                </motion.div>
            )}
        </AnimatePresence>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" {...register('email')} placeholder="admin@phantom.net" />
            {errors.email && <p className="text-destructive text-sm mt-1">{errors.email.message}</p>}
          </div>
          <div className="relative">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type={showPassword ? 'text' : 'password'} {...register('password')} placeholder="••••••••" />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-[2.3rem] text-muted-foreground"
            >
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
            {errors.password && <p className="text-destructive text-sm mt-1">{errors.password.message}</p>}
          </div>
          <div>
            <Label htmlFor="role">Role</Label>
            <Select onValueChange={(value) => control.setValue('role', value)} defaultValue="user">
              <SelectTrigger>
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="user">User</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center justify-end">
            <a href="#" className="text-sm text-primary hover:underline">
              Forgot Password?
            </a>
          </div>
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? <LoaderCircle className="animate-spin" /> : 'Login'}
          </Button>
        </form>
        <div className="text-center text-sm text-muted-foreground">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary hover:underline">
            Register
          </Link>
        </div>
        <div className="text-center text-sm text-muted-foreground">
          <Link to="/forgot-password" className="text-primary hover:underline">
            Forgot Password?
          </Link>
        </div>
      </motion.div>
    </div>
  );
};

export default LoginPage;