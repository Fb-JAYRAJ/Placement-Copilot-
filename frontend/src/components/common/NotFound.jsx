import React from 'react';
import { Link } from 'react-router-dom';
import Icon from './Icon';

export const NotFound = () => {
  return (
    <div className="min-h-screen bg-surface flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-[8px] bg-surface-container border border-outline-variant flex items-center justify-center text-error mb-4">
        <Icon name="search_off" className="text-3xl" />
      </div>
      <div className="label-mono text-xs text-outline mb-1">ERROR 404</div>
      <h1 className="text-3xl font-extrabold text-on-surface tracking-tight mb-2">Page Not Found</h1>
      <p className="text-sm text-on-surface-variant max-w-md mb-6">
        The requested pathway does not exist in the Placement Copilot index. Check the URL or return to your dashboard.
      </p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 px-4 py-2.5 rounded-[4px] bg-primary text-on-primary text-xs font-bold uppercase tracking-wider hover:bg-primary-container transition-colors"
      >
        <Icon name="arrow_back" className="text-base" />
        <span>Return to Dashboard</span>
      </Link>
    </div>
  );
};

export default NotFound;
