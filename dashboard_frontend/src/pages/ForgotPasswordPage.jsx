import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

const MotionDiv = motion.div;

const ForgotPasswordPage = () => (
  <div className="flex items-center justify-center min-h-screen bg-background text-foreground p-4">
    <MotionDiv
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative z-10 w-full max-w-md p-8 space-y-6 bg-card rounded-2xl shadow-2xl shadow-primary/10 border border-border"
    >
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-bold text-primary">Password Reset Unavailable</h1>
        <p className="text-muted-foreground">
          PhantomNet’s legacy simulated password-reset flow has been retired because it did not provide verified out-of-band delivery or a durable token lifecycle.
        </p>
        <p className="text-sm text-muted-foreground">
          Contact your organization’s approved account administrator for a supported recovery process.
        </p>
      </div>
      <div className="text-center text-sm text-muted-foreground">
        Remember your password?{' '}
        <Link to="/login" className="text-primary hover:underline">
          Login
        </Link>
      </div>
    </MotionDiv>
  </div>
);

export default ForgotPasswordPage;
