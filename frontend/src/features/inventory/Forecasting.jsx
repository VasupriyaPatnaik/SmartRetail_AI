import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Forecasting() {
  const [forecast, setForecast] = useState([]);

  useEffect(() => {
    axios.get('http://127.0.0.1:5000/forecast')
      .then(response => setForecast(response.data))
      .catch(error => console.error('Error fetching data:', error));
  }, []);

  return (
    <div>
      <h2>📈 Demand Forecasting</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Predicted Sales</th>
          </tr>
        </thead>
        <tbody>
          {forecast.map((item, index) => (
            <tr key={index}>
              <td>{item.date}</td>
              <td>{item.sales_quantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Forecasting;