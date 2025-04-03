import { motion, useAnimation } from "framer-motion";
import { useInView } from "react-intersection-observer";
import { useEffect } from "react";

export default function HeroSection() {
  const controls = useAnimation();
  const [ref, inView] = useInView();

  useEffect(() => {
    if (inView) {
      controls.start("visible");
    }
  }, [controls, inView]);

  const variants = {
    visible: { 
      opacity: 1, 
      y: 0, 
      transition: { staggerChildren: 0.2 } 
    },
    hidden: { opacity: 0, y: 50 }
  };

  return (
    <motion.section 
      ref={ref}
      initial="hidden"
      animate={controls}
      variants={variants}
      className="hero-gradient" // CSS: linear-gradient(135deg, #6366f1, #10b981)
    >
      <motion.h1 variants={variants} className="hero-title">
        Revolutionize <span>Retail</span> with AI Agents
      </motion.h1>
      <motion.p variants={variants} className="hero-subtitle">
        Real-time inventory optimization that learns as you grow.
      </motion.p>
      <motion.div variants={variants}>
        <button className="cta-button pulse-animation">
          Live Demo 🚀
        </button>
      </motion.div>
      
      {/* Animated floating AI agent illustration */}
      <motion.div 
        className="ai-illustration"
        animate={{
          y: [0, -15, 0],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
    </motion.section>
  );
}