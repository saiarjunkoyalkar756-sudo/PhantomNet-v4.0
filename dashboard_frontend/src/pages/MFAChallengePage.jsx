import React, { useEffect, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { AnimatePresence, motion } from 'framer-motion';import { useNavigate } from 'react-router-dom';
import { LoaderCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import useAuthStore from '@/store/authStore';
import api from '@/services/api';
import {
  clearMfaPendingCredentials,
  getMfaPendingCredentials,
} from '@/services/mfaChallenge';

const MotionDiv = motion.div;

const mfaSchema = z.object({
  code: z.string().trim(),
  type: z.enum(['totp', 'recovery']).default('totp'),
}).superRefine(({ code, type }, context) => {
  const valid = type === 'totp'
    ? /^\d{6}$/.test(code)
    : /^[A-Z0-9]{10}$/.test(code.toUpperCase());

  if (!valid) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['code'],
      message: type === 'totp'
        ? 'Enter a six-digit authenticator code.'
        : 'Enter a ten-character recovery code.',
    });
  }
});

const MFAChallengePage = () => {
  const [apiError, setApiError] = useState(null);
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  useEffect(() => () => clearMfaPendingCredentials(), []);

  const {
    register,
    handleSubmit,
    setValue,
    control,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(mfaSchema),
    mode: 'onChange',
    defaultValues: {
      type: 'totp',
    }
  });

  const challengeType = useWatch({ control, name: 'type' });

  const onSubmit = async (data) => {
    setApiError(null);
    const credentials = getMfaPendingCredentials();

    if (!credentials) {
      setApiError('Authentication session expired. Please sign in again.');
      navigate('/login');
      return;
    }

    try {
      const headers = {};
      if (data.type === 'totp') {
        headers['X-2FA-Code'] = data.code;
      } else {
        headers['X-Recovery-Code'] = data.code.toUpperCase();
      }

      const params = new URLSearchParams();
      params.append('username', credentials.username);
      params.append('password', credentials.password);
      const response = await api.post('/auth/token', params, {
        headers: { ...headers, 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      clearMfaPendingCredentials();
      login(response);

      if (response.user?.role === 'admin') {
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
      <MotionDiv
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
        </AnimatePresence>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="code">{challengeType === 'totp' ? '2FA Code' : 'Recovery Code'}</Label>
            <Input
              id="code"
              type="text"
              inputMode={challengeType === 'totp' ? 'numeric' : 'text'}
              autoComplete="one-time-code"
              {...register('code')}
              placeholder={challengeType === 'totp' ? 'XXXXXX' : 'XXXXXXXXXX'}
            />
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
      </MotionDiv>
    </div>
  );
};

export default MFAChallengePage;
