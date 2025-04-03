import { motion } from 'framer-motion';
import './StatsCard.css';

export const StatsCard = ({ 
  value, 
  label, 
  icon = '📊',
  trend = 'up', // 'up', 'down', or 'neutral'
  delay = 0
}) => {
  return (
    <motion.div
      className={`stats-card ${trend}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.1, type: 'spring' }}
      whileHover={{ scale: 1.03 }}
    >
      <div className="card-icon">{icon}</div>
      
      <div className="card-content">
        <h3>{value}</h3>
        <p>{label}</p>
      </div>

      {trend !== 'neutral' && (
        <div className={`trend-indicator ${trend}`}>
          {trend === 'up' ? '↑' : '↓'}
        </div>
      )}
    </motion.div>
  );
};