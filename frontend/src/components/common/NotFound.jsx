import React from 'react';
import { Link } from 'react-router-dom';
import Icon from './Icon';

export const NotFound = () => {
  return (
    <div className="min-h-screen bg-[#131313] flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-[8px] bg-[#1f1f1f] border border-[#3d4a3d] flex items-center justify-center text-[#ffb4ab] mb-4">
        <Icon name="search_off" className="text-3xl" />
      </div>
      <div className="label-mono text-xs text-[#869585] mb-1">ERROR 404</div>
      <h1 className="text-3xl font-extrabold text-[#e2e2e2] tracking-tight mb-2">Page Not Found</h1>
      <p className="text-sm text-[#bccbb9] max-w-md mb-6">
        The requested pathway does not exist in the Placement Copilot index. Check the URL or return to your dashboard.
      </p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 px-4 py-2.5 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] transition-colors"
      >
        <Icon name="arrow_back" className="text-base" />
        <span>Return to Dashboard</span>
      </Link>
    </div>
  );
};

export default NotFound;
