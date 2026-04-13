import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // You can also log the error to an error reporting service
    console.error("Uncaught error:", error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-background text-foreground">
            <h1 className="text-3xl font-bold text-destructive">Something went wrong.</h1>
            <p className="text-muted-foreground">Please try refreshing the page.</p>
            {this.state.error && (
                <details className="mt-4 p-4 bg-card rounded-md w-full max-w-2xl text-sm">
                    <summary>Error Details</summary>
                    <pre className="mt-2 text-destructive whitespace-pre-wrap">
                        {this.state.error.toString()}
                        <br />
                        {this.state.errorInfo?.componentStack}
                    </pre>
                </details>
            )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
