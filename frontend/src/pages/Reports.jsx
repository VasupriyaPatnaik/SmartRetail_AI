import React from 'react';
import { motion } from 'framer-motion';
import { Card, GlowButton } from '@/components/ui'; // Using your UI components
import './Reports.css';

function Reports() {
  const reportCards = [
    {
      icon: '📈',
      title: 'Sales Trends',
      description: 'AI-powered predictions with 92% accuracy',
      buttonVariant: 'primary',
      animationDelay: 0.1
    },
    {
      icon: '📦',
      title: 'Stock Levels',
      description: 'Real-time inventory across 5 warehouses',
      buttonVariant: 'success',
      animationDelay: 0.2
    },
    {
      icon: '🚚',
      title: 'Supplier Efficiency',
      description: 'On-time delivery performance analytics',
      buttonVariant: 'warning', 
      animationDelay: 0.3
    }
  ];

  return (
    <motion.div 
      className="reports-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <motion.div
        className="header"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <h1>📊 Inventory Intelligence</h1>
        <p className="subtitle">AI-powered insights for smarter decisions</p>
      </motion.div>
      
      <div className="report-grid">
        {reportCards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + card.animationDelay, duration: 0.5 }}
          >
            <Card className="report-card">
              <div className="card-icon">{card.icon}</div>
              <h3>{card.title}</h3>
              <p>{card.description}</p>
              <GlowButton 
                variant={card.buttonVariant}
                onClick={() => console.log(`View ${card.title}`)}
              >
                Analyze Now →
              </GlowButton>
            </Card>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

export default Reports;