import React from 'react';

/**
 * Material Symbols Outlined icon wrapper.
 * @param {Object} props
 * @param {string} props.name - Material symbol icon identifier
 * @param {string} [props.className] - Optional Tailwind/CSS utility classes
 * @param {Object} [props.style] - Optional inline CSS styles
 */
export const Icon = ({ name, className = '', style }) => {
  return (
    <span
      className={`material-symbols-outlined select-none inline-flex items-center justify-center ${className}`}
      style={style}
      aria-hidden="true"
    >
      {name}
    </span>
  );
};

export default Icon;
