import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';

const NotFoundPage = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background text-foreground">
      <h1 className="text-9xl font-bold text-primary">404</h1>
      <h2 className="text-2xl font-semibold text-muted-foreground mt-4">Page Not Found</h2>
      <p className="mt-2 text-center">The page you are looking for does not exist.</p>
      <Button asChild className="mt-8">
        <Link to="/">Go to Homepage</Link>
      </Button>
    </div>
  );
};

export default NotFoundPage;
