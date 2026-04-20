import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { LoaderCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import useAuthStore from '@/store/authStore';
import api from '@/services/api';

const mfaSchema = z.object({
  code: z.string().min(6, { message: 'Code must be 6 digits.' }).max(6, { message: 'Code must be 6 digits.' }).regex(/^\d+$/, { message: 'Code must be numeric.' }),
  type: z.enum(['totp', 'recovery']).default('totp'),
});

const MFAChallengePage = () => {
  const [apiError, setApiError] = useState(null);
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(mfaSchema),
    mode: 'onChange',
    defaultValues: {
      type: 'totp',
    }
  });

  const challengeType = watch('type');

  const onSubmit = async (data) => {
    setApiError(null);
    const username = sessionStorage.getItem('mfa_username');
    const password = sessionStorage.getItem('mfa_password');

    if (!username || !password) {
      setApiError('Authentication session expired. Please log in again.');
      navigate('/login');
      return;
    }

    try {
      const headers = {};
      if (data.type === 'totp') {
        headers['X-2FA-Code'] = data.code;
      } else {
        headers['X-Recovery-Code'] = data.code;
      }

      const response = await api.post(
        '/api/auth/token',
        { username, password },
        { headers }
      );

      sessionStorage.removeItem('mfa_username');
      sessionStorage.removeItem('mfa_password');
      login(response.data);

      if (response.data.user.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setApiError(err.response?.data?.detail || 'Invalid code. Please try again.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background text-foreground p-4">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md p-8 space-y-6 bg-card rounded-2xl shadow-2xl shadow-primary/10 border border-border"
      >
        <div className="text-center">
          <h1 className="text-4xl font-bold text-primary">MFA Challenge</h1>
          <p className="text-muted-foreground mt-2">Enter your 2FA code or a recovery code.</p>
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
            <Label htmlFor="code">{challengeType === 'totp' ? '2FA Code' : 'Recovery Code'}</Label>
            <Input id="code" type="text" inputMode="numeric" {...register('code')} placeholder="XXXXXX" />
            {errors.code && <p className="text-destructive text-sm mt-1">{errors.code.message}</p>}
          </div>

          <div className="flex justify-center space-x-4">
            <Button
              type="button"
              variant={challengeType === 'totp' ? 'default' : 'outline'}
              onClick={() => setValue('type', 'totp')}
            >
              Use 2FA App
            </Button>
            <Button
              type="button"
              variant={challengeType === 'recovery' ? 'default' : 'outline'}
              onClick={() => setValue('type', 'recovery')}
            >
              Use Recovery Code
            </Button>
          </div>
          
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? <LoaderCircle className="animate-spin" /> : 'Verify Code'}
          </Button>
        </form>
      </motion.div>
    </div>
  );
};

export default MFAChallengePage;
