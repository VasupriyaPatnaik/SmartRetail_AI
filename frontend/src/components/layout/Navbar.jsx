import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { colors } from '@/theme';

const navItems = [
  { path: '/', name: 'Dashboard' },
  { path: '/forecasting', name: 'Forecasting' },
  { path: '/inventory', name: 'Inventory' },
  { path: '/suppliers', name: 'Suppliers' },
  { path: '/analytics', name: 'Analytics' }
];

export default function Navbar() {
  return (
    <header className="navbar">
      <motion.div 
        className="logo"
        whileHover={{ scale: 1.05 }}
      >
        <Link to="/">SmartRetail <span>AI</span></Link>
      </motion.div>
      
      <nav>
        <ul>
          {navItems.map((item) => (
            <motion.li
              key={item.path}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.95 }}
            >
              <Link to={item.path}>{item.name}</Link>
            </motion.li>
          ))}
        </ul>
      </nav>
    </header>
  );
}