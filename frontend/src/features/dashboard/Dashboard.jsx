import { motion } from 'framer-motion';
import { Card, StatsCard } from '@/components/ui';
import { colors, animations } from '@/theme';

const stats = [
  { value: '98%', label: 'Stock Accuracy', icon: '📊' },
  { value: '24h', label: 'Avg Restock Time', icon: '⏱️' },
  { value: '12%', label: 'Cost Savings', icon: '💰' }
];

// In your Dashboard component
const Dashboard = () => {
    const { 
      agents, 
      collaborationLog, 
      optimizeInventory 
    } = useAgentSystem();
  
    const { 
      liveData, 
      isConnected 
    } = useLiveData(['inventory', 'sales']);
  
    return (
      <div>
        <button onClick={optimizeInventory}>
          Run AI Optimization
        </button>
        
        <div>
          {isConnected ? (
            <InventoryChart data={liveData.inventory} />
          ) : (
            <p>Connecting to live data...</p>
          )}
        </div>
      </div>
    );
  };

export default function Dashboard() {
  return (
    <motion.div initial="slideUp" animate="visible" variants={animations}>
      <div className="dashboard-header">
        <h1>SmartRetail <span className="ai-text">AI</span> Dashboard</h1>
        <p>Real-time inventory optimization powered by AI agents</p>
      </div>

      <div className="stats-grid">
        {stats.map((stat, i) => (
          <StatsCard 
            key={stat.label}
            delay={i * 0.1}
            {...stat}
          />
        ))}
      </div>

      <div className="action-grid">
        <Card hoverEffect>
          <h3>📈 Demand Forecast</h3>
          <p>AI-powered sales predictions</p>
        </Card>
        <Card hoverEffect accent>
          <h3>🔄 Auto-Replenish</h3>
          <p>Smart restocking system</p>
        </Card>
      </div>
    </motion.div>
  );
}