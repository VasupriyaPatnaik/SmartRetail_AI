import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import './Home.css';

export const Home = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: '📊',
      title: 'AI Demand Forecasting',
      description: 'Predict sales trends with 95% accuracy'
    },
    {
      icon: '🔄',
      title: 'Auto Inventory Optimization',
      description: 'Reduce stockouts by 40%'
    },
    {
      icon: '🚨',
      title: 'Anomaly Detection',
      description: 'Instant alerts for unusual patterns'
    }
  ];

  return (
    <motion.div 
      className="home-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Hero Section */}
      <section className="hero-section">
        <motion.div
          className="hero-content"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          <h1>
            Smarter <span>Inventory</span> with AI
          </h1>
          <p className="hero-subtitle">
            Reduce costs and boost sales with real-time retail optimization
          </p>
          <motion.button
            className="cta-button"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate('/dashboard')}
          >
            Launch Dashboard →
          </motion.button>
        </motion.div>

        <motion.div
          className="hero-graphic"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          <div className="graphic-circle"></div>
          <div className="graphic-circle"></div>
          <div className="graphic-circle"></div>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="features-section">
        <h2>Key Features</h2>
        <div className="features-grid">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              className="feature-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.1, duration: 0.5 }}
              whileHover={{ y: -5 }}
            >
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>
    </motion.div>
  );
};