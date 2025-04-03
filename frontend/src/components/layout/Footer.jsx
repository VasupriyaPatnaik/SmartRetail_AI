import React from "react";

const Footer = () => {
  return (
    <footer className="bg-dark text-white text-center py-3 mt-4">
      <p>&copy; {new Date().getFullYear()} SmartRetail AI. All rights reserved.</p>
      <p>
        <a href="/privacy" className="text-white me-3">Privacy Policy</a>
        <a href="/terms" className="text-white">Terms of Service</a>
      </p>
    </footer>
  );
};

export default Footer;