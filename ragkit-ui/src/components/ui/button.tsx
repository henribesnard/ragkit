import { ButtonHTMLAttributes } from 'react';
import { cn } from '@/utils/cn';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'outline';
  size?: 'sm' | 'md';
}

export function Button({ variant = 'primary', size = 'md', className, ...props }: ButtonProps) {
  const styles = {
    primary: 'bg-accent text-white hover:bg-accent/90 shadow-glow',
    ghost: 'bg-transparent text-ink hover:bg-white/70',
    outline: 'border border-accent/30 text-accent hover:bg-accent/10',
  };
  const sizes = {
    sm: 'rounded-full px-3 py-1 text-xs font-semibold transition',
    md: 'rounded-full px-4 py-2 text-sm font-semibold transition',
  };
  return (
    <button
      className={cn(
        sizes[size],
        styles[variant],
        className
      )}
      {...props}
    />
  );
}
