import { BrowserRouter as Router } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import AnimatedRoutes from '@/components/AnimatedRoutes';
import { colors } from '@/theme';
import '@/App.css';

function App() {
  return (
    <Router>
      <div className="app-container" style={{ '--primary': colors.primary }}>
        <Navbar />
        <main className="main-content">
          <AnimatePresence mode="wait">
            <AnimatedRoutes />
          </AnimatePresence>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;