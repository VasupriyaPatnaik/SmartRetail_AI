import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Table } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import axios from "axios";

const Anomalies = () => {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get("http://localhost:5000/api/anomalies")
      .then(response => {
        setAnomalies(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching anomalies:", error);
        setLoading(false);
      });
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Inventory Anomalies</h2>
      <Card>
        {loading ? (
          <p>Loading anomalies...</p>
        ) : (
          <Table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Issue</th>
                <th>Detected At</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((anomaly, index) => (
                <tr key={index}>
                  <td>{anomaly.product}</td>
                  <td>{anomaly.issue}</td>
                  <td>{new Date(anomaly.timestamp).toLocaleString()}</td>
                  <td>
                    <Button variant="destructive">Resolve</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
};

export default Anomalies;