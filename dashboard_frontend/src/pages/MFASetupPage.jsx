import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { LoaderCircle, CheckCircle, XCircle } from 'lucide-react';
import QRCode from 'qrcode.react'; // You might need to install 'qrcode.react' (npm install qrcode.react)

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import api from '@/services/api';
import useAuthStore from '@/store/authStore';

const mfaVerifySchema = z.object({
  code: z.string().min(6, { message: 'Code must be 6 digits.' }).max(6, { message: 'Code must be 6 digits.' }).regex(/^\d+$/, { message: 'Code must be numeric.' }),
});

const MFASetupPage = () => {
  const [apiError, setApiError] = useState(null);
  const [secret, setSecret] = useState(null);
  const [recoveryCodes, setRecoveryCodes] = useState([]);
  const [setupStep, setSetupStep] = useState(1); // 1: Enable, 2: Verify, 3: Recovery Codes
  const user = useAuthStore((state) => state.user);
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(mfaVerifySchema),
    mode: 'onChange',
  });

  const generateQRCodeUrl = (totpSecret) => {
    if (!user || !user.username) return '';
    const issuer = encodeURIComponent('PhantomNet');
    const accountName = encodeURIComponent(user.username);
    return `otpauth://totp/${issuer}:${accountName}?secret=${totpSecret}&issuer=${issuer}`;
  };

  const handleEnable2FA = async () => {
    setApiError(null);
    try {
      const response = await api.post('/api/auth/enable-2fa');
      setSecret(response.data.secret);
      setSetupStep(2); // Move to verify step
    } catch (err) {
      setApiError(err.response?.data?.detail || 'Failed to enable 2FA.');
    }
  };

  const onVerify = async (data) => {
    setApiError(null);
    try {
      const response = await api.post('/api/auth/verify-2fa', { code: data.code });
      setRecoveryCodes(response.data.recovery_codes);
      setSetupStep(3); // Move to recovery codes step
    } catch (err) {
      setApiError(err.response?.data?.detail || 'Invalid 2FA code. Please try again.');
    }
  };

  const handleDisable2FA = async (data) => {
    setApiError(null);
    try {
      await api.post('/api/auth/disable-2fa', { code: data.code });
      setSecret(null);
      setRecoveryCodes([]);
      setSetupStep(1); // Back to enable step
      alert("2FA disabled successfully.");
      // Optionally refresh user state
    } catch (err) {
      setApiError(err.response?.data?.detail || 'Failed to disable 2FA. Invalid code?');
    }
  };

  // Redirect if user not logged in, or adjust based on current user 2FA status
  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
    // You might fetch user's 2FA status here if it's not in the authStore
  }, [user, navigate]);


  // Check if qrcode.react is available, if not, provide a fallback or instruct user to install
  if (typeof QRCode === 'undefined') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertTitle>Missing Dependency</AlertTitle>
          <AlertDescription>
            The 'qrcode.react' library is not installed. Please install it using `npm install qrcode.react`.
          </AlertDescription>
        </Alert>
      </div>
    );
  }


  return (
    <div className="flex items-center justify-center min-h-screen bg-background text-foreground p-4">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md p-8 space-y-6 bg-card rounded-2xl shadow-2xl shadow-primary/10 border border-border"
      >
        <div className="text-center">
          <h1 className="text-4xl font-bold text-primary">2FA Setup</h1>
          <p className="text-muted-foreground mt-2">Secure your account with Multi-Factor Authentication.</p>
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

        {setupStep === 1 && (
          <div className="space-y-4 text-center">
            <p className="text-lg">Two-Factor Authentication is currently not enabled.</p>
            <Button onClick={handleEnable2FA} className="w-full">
              Enable 2FA
            </Button>
          </div>
        )}

        {setupStep === 2 && secret && (
          <form onSubmit={handleSubmit(onVerify)} className="space-y-4">
            <h3 className="text-xl font-semibold text-center">Step 2: Scan QR Code & Verify</h3>
            <p className="text-center text-muted-foreground">
              Scan the QR code with your authenticator app (e.g., Google Authenticator, Authy).
            </p>
            <div className="flex justify-center p-4 bg-white rounded-lg">
              <QRCode value={generateQRCodeUrl(secret)} size={256} level="H" />
            </div>
            <p className="text-center text-sm font-mono break-all bg-gray-100 p-2 rounded">
              Manual Code: {secret}
            </p>
            <div>
              <Label htmlFor="code">Enter 6-digit code from app</Label>
              <Input id="code" type="text" inputMode="numeric" {...register('code')} placeholder="XXXXXX" />
              {errors.code && <p className="text-destructive text-sm mt-1">{errors.code.message}</p>}
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? <LoaderCircle className="animate-spin" /> : 'Verify 2FA'}
            </Button>
            <Button variant="outline" className="w-full" onClick={() => setSetupStep(1)} disabled={isSubmitting}>
              Cancel
            </Button>
          </form>
        )}

        {setupStep === 3 && recoveryCodes.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-center">Step 3: Save Recovery Codes</h3>
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>2FA Enabled Successfully!</AlertTitle>
              <AlertDescription>
                <p>Save these recovery codes in a safe place. They can be used to log in if you lose access to your authenticator app.</p>
                <ul className="list-disc list-inside mt-2 font-mono bg-gray-100 p-2 rounded">
                  {recoveryCodes.map((code, index) => (
                    <li key={index}>{code}</li>
                  ))}
                </ul>
                <p className="mt-2 text-sm text-red-500">
                  **WARNING:** These codes will not be shown again.
                </p>
              </AlertDescription>
            </Alert>
            <Button onClick={() => navigate('/dashboard')} className="w-full">
              Go to Dashboard
            </Button>
            {/* Optionally, allow disabling 2FA from here if already enabled */}
            <Button variant="outline" className="w-full" onClick={() => setSetupStep(1)}>
              Done
            </Button>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default MFASetupPage;