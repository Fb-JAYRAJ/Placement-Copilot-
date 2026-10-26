import React from 'react';
import Icon from './Icon';

/**
 * Standard Error Boundary component.
 * Catches render errors anywhere in the child tree, logs them, and displays a friendly
 * fallback with a Retry button rather than crashing into a blank screen.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught a render exception:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const isRoot = this.props.level === 'root';

      return (
        <div
          role="alert"
          className={`${
            isRoot ? 'min-h-screen' : 'min-h-[320px] my-4'
          } bg-[#131313] flex flex-col items-center justify-center p-6 text-center rounded-[8px] border border-[#ffb4ab]/20`}
        >
          <div className="w-14 h-14 rounded-[8px] bg-[#93000a]/20 border border-[#ffb4ab]/30 flex items-center justify-center text-[#ffb4ab] mb-4">
            <Icon name="error" className="text-3xl" />
          </div>
          <div className="label-mono text-xs text-[#ffb4ab] mb-1">
            {isRoot ? 'ROOT APPLICATION ERROR' : 'SECTION ERROR'}
          </div>
          <h2 className="text-2xl font-extrabold text-[#e2e2e2] tracking-tight mb-2">
            {this.props.title || 'Something went wrong'}
          </h2>
          <p className="text-sm text-[#bccbb9] max-w-md mb-2">
            {this.props.message ||
              'A rendering issue occurred in this section. You can try refreshing the component.'}
          </p>
          {this.state.error?.message && (
            <div className="p-2.5 my-3 rounded-[4px] bg-[#1b1b1b] border border-[#3d4a3d] font-mono text-xs text-[#ffb4ab] max-w-lg overflow-x-auto text-left">
              {this.state.error.message}
            </div>
          )}
          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={this.handleRetry}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] transition-colors"
            >
              <Icon name="refresh" className="text-base" />
              <span>Retry</span>
            </button>
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-[4px] bg-[#1f1f1f] border border-[#3d4a3d] text-xs font-semibold text-[#e2e2e2] hover:bg-[#2a2a2a] transition-colors"
            >
              <span>Reload Page</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
