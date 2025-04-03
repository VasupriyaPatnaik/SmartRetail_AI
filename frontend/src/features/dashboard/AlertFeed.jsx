import { motion, AnimatePresence } from 'framer-motion';
import './AlertFeed.css';

export const AlertFeed = ({ alerts }) => {
  return (
    <div className="alert-feed">
      <h3 className="feed-title">🚨 Live Alerts</h3>
      
      <div className="alerts-container">
        <AnimatePresence>
          {alerts.map((alert) => (
            <motion.div
              key={alert.id}
              className={`alert-item ${alert.severity}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ type: 'spring', stiffness: 300 }}
              layout
            >
              <div className="alert-icon">
                {alert.severity === 'critical' ? '🔥' : '⚠️'}
              </div>
              <div className="alert-content">
                <p className="alert-message">{alert.message}</p>
                <span className="alert-time">{alert.timestamp}</span>
              </div>
              {alert.severity === 'critical' && (
                <div className="pulse-dot"></div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};