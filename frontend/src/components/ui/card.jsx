import { motion, useTransform, useMotionTemplate } from 'framer-motion';
import { useRef } from 'react';
import { useTiltAnimation } from '@/hooks/useTiltAnimation'; // Custom hook
import './Card.css';

export const Card = ({ 
  children,
  variant = 'default',
  glowColor = '#6366f1',
  hoverEffect = true,
  className = ''
}) => {
  const cardRef = useRef(null);
  const { rotateX, rotateY, handleMouseMove, handleMouseLeave } = 
    useTiltAnimation(cardRef, 15); // 15° max tilt

  const background = useTransform(
    [rotateX, rotateY],
    ([x, y]) => `linear-gradient(
      ${45 + x * 2}deg,
      rgba(99, 102, 241, 0.15),
      rgba(16, 185, 129, ${0.1 + Math.abs(y * 0.005)})
    )`
  );

  const boxShadow = useTransform(
    [rotateX, rotateY],
    ([x, y]) => `${y * 2}px ${x * 2}px 30px rgba(0, 0, 0, 0.2)`
  );

  const style = useMotionTemplate`
    background: ${background};
    box-shadow: ${boxShadow};
    transform: perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg);
  `;

  return (
    <motion.div
      ref={cardRef}
      className={`card ${variant} ${hoverEffect ? 'hover-effect' : ''} ${className}`}
      style={hoverEffect ? style : undefined}
      onMouseMove={hoverEffect ? handleMouseMove : undefined}
      onMouseLeave={hoverEffect ? handleMouseLeave : undefined}
      whileHover={hoverEffect ? { zIndex: 1 } : undefined}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      {hoverEffect && (
        <div 
          className="card-glow" 
          style={{ '--glow-color': glowColor }} 
        />
      )}
      <div className="card-content">
        {children}
      </div>
    </motion.div>
  );
};

export const CardHeader = ({ children }) => (
  <div className="card-header">
    {children}
  </div>
);

export const CardBody = ({ children }) => (
  <div className="card-body">
    {children}
  </div>
);