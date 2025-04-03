import { motion, useAnimation } from 'framer-motion';
import { useEffect } from 'react';
import './Button.css'; // For advanced effects

const Button = ({ 
  children, 
  onClick, 
  variant = 'primary',
  size = 'medium',
  icon,
  pulse = false
}) => {
  const controls = useAnimation();
  
  // Glow animation on mount
  useEffect(() => {
    controls.start({
      boxShadow: [
        '0 0 0 0 rgba(99, 102, 241, 0)',
        '0 0 20px 5px rgba(99, 102, 241, 0.3)',
        '0 0 0 0 rgba(99, 102, 241, 0)'
      ],
      transition: { duration: 2, repeat: Infinity, repeatDelay: 3 }
    });
  }, []);

  const baseStyle = {
    primary: 'bg-indigo-600 hover:bg-indigo-700',
    secondary: 'bg-emerald-500 hover:bg-emerald-600',
    danger: 'bg-rose-500 hover:bg-rose-600',
    ghost: 'bg-transparent border-2 border-indigo-400'
  };

  const sizeStyle = {
    small: 'py-1 px-3 text-sm',
    medium: 'py-2 px-4 text-base',
    large: 'py-3 px-6 text-lg'
  };

  return (
    <motion.button
      onClick={onClick}
      className={`button ${baseStyle[variant]} ${sizeStyle[size]} relative overflow-hidden`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ 
        opacity: 1, 
        y: 0,
        transition: { type: 'spring', stiffness: 300 }
      }}
      whileHover={{
        scale: 1.05,
        transition: { duration: 0.2 }
      }}
      whileTap={{
        scale: 0.95,
        transition: { duration: 0.1 }
      }}
    >
      {/* Holographic overlay */}
      <motion.span 
        className="holographic-overlay"
        animate={controls}
      />
      
      {/* Animated border */}
      <span className="border-animation" />
      
      {/* Content */}
      <div className="flex items-center gap-2 relative z-10">
        {icon && <span className="button-icon">{icon}</span>}
        {children}
      </div>
      
      {/* Optional pulse effect */}
      {pulse && (
        <motion.span
          className="pulse-dot"
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.7, 0]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeOut"
          }}
        />
      )}
    </motion.button>
  );
};

export default Button;