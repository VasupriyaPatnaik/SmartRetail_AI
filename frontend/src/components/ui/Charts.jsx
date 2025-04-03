import { useEffect, useRef } from 'react';
import './Charts.css';

export const SimpleChart = ({ data, type = 'line' }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!data || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Chart styling
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';

    // Calculate scales
    const xValues = data.map(item => item.date);
    const yValues = data.map(item => item.value);
    const xScale = width / (xValues.length - 1);
    const yMax = Math.max(...yValues) * 1.2;
    const yScale = height / yMax;

    // Draw axes
    ctx.strokeStyle = '#ddd';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height - 20);
    ctx.lineTo(width, height - 20);
    ctx.stroke();

    // Draw data
    if (type === 'line') {
      ctx.strokeStyle = '#6366f1';
      ctx.lineWidth = 3;
      ctx.beginPath();

      data.forEach((item, i) => {
        const x = i * xScale;
        const y = height - (item.value * yScale) - 20;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });

      ctx.stroke();

      // Draw points
      data.forEach((item, i) => {
        const x = i * xScale;
        const y = height - (item.value * yScale) - 20;
        ctx.fillStyle = '#6366f1';
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
      });

    } else if (type === 'bar') {
      const barWidth = (width / data.length) * 0.6;
      
      data.forEach((item, i) => {
        const x = i * (width / data.length) + (width / data.length - barWidth) / 2;
        const barHeight = item.value * yScale;
        ctx.fillStyle = '#10b981';
        ctx.fillRect(x, height - barHeight - 20, barWidth, barHeight);
      });
    }

    // Draw labels
    data.forEach((item, i) => {
      if (i % 2 === 0) { // Skip some labels for clarity
        const x = i * xScale;
        ctx.fillStyle = '#666';
        ctx.fillText(item.date.slice(0, 3), x, height - 5);
      }
    });

  }, [data, type]);

  return (
    <div className="chart-container">
      <canvas 
        ref={canvasRef}
        width={600}
        height={300}
      />
      <div className="chart-title">
        {type === 'line' ? 'Demand Forecast' : 'Stock Levels'}
      </div>
    </div>
  );
};