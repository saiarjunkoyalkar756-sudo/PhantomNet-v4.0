import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { AnimatePresence, motion } from 'framer-motion';import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, LoaderCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import api from '@/services/api';

const MotionDiv = motion.div;

const registerSchema = z.object({
  username: z.string().email({ message: 'Invalid email address.' }),
  password: z.string().min(8, { message: 'Password must be at least 8 characters.' }),
});

const RegisterPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(registerSchema),
    mode: 'onChange',
  });

  const onSubmit = async (data) => {
    setApiError(null);
    try {
      await api.post('/api/auth/register', { username: data.username, password: data.password });
      setRegistrationSuccess(true);
      // Optionally, automatically log in or redirect after a short delay
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setApiError(err.response?.data?.detail || 'An unexpected error occurred during registration.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background text-foreground p-4">
      <div className="absolute inset-0 z-0 h-full w-full bg-background bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]"></div>
      <MotionDiv
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md p-8 space-y-6 bg-card rounded-2xl shadow-2xl shadow-primary/10 border border-border"
      >
        <div className="text-center">
          <h1 className="text-4xl font-bold text-primary">PhantomNet</h1>
          <p className="text-muted-foreground mt-2">Create your account</p>
        </div>

        <AnimatePresence>
            {apiError && (
                 <MotionDiv
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-3 mb-4 text-sm text-center text-destructive-foreground bg-destructive rounded-lg"
                    role="alert"
                >
                    {apiError}
                </MotionDiv>
            )}
            {registrationSuccess && (
                 <MotionDiv
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-3 mb-4 text-sm text-center text-success-foreground bg-success rounded-lg"
                    role="alert"
                >
                    Registration successful! Redirecting to login...
                </MotionDiv>
            )}
        </AnimatePresence>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="username">Email (Username)</Label>
            <Input id="username" type="email" {...register('username')} placeholder="user@phantom.net" />
            {errors.username && <p className="text-destructive text-sm mt-1">{errors.username.message}</p>}
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
          <p className="text-sm text-muted-foreground">
            Self-registration creates a standard user account. Privileged access must be provisioned through a governed administrator workflow.
          </p>
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? <LoaderCircle className="animate-spin" /> : 'Register'}
          </Button>
        </form>
        <div className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" className="text-primary hover:underline">
            Login
          </Link>
        </div>
      </MotionDiv>
    </div>
  );
};

export default RegisterPage;
