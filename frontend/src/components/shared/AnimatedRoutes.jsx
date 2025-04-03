import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';

const pageVariants = {
  initial: {
    opacity: 0,
    x: -30,
  },
  in: {
    opacity: 1,
    x: 0,
  },
  out: {
    opacity: 0,
    x: 30,
  }
};

const pageTransition = {
  type: 'spring',
  stiffness: 100,
  damping: 20
};

export const AnimatedRoutes = ({ children }) => {
  const location = useLocation();

  return (
    <motion.div
      key={location.key}
      initial="initial"
      animate="in"
      exit="out"
      variants={pageVariants}
      transition={pageTransition}
    >
      {children}
    </motion.div>
  );
};