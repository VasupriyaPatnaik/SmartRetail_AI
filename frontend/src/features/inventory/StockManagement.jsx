import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table } from "@/components/ui/table";
import { Loader } from "lucide-react";

const StockManagement = () => {
  const [stockData, setStockData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStockData();
  }, []);

  const fetchStockData = async () => {
    try {
      const response = await axios.get("http://localhost:5000/api/stock");
      setStockData(response.data);
    } catch (error) {
      console.error("Error fetching stock data:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Stock Management</h1>
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader className="animate-spin text-gray-500" size={40} />
        </div>
      ) : (
        <Card>
          <CardContent>
            <Table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Stock Level</th>
                  <th>Reorder Status</th>
                </tr>
              </thead>
              <tbody>
                {stockData.map((item) => (
                  <tr key={item.id}>
                    <td>{item.product_name}</td>
                    <td>{item.stock_level}</td>
                    <td>
                      {item.reorder_needed ? (
                        <Button variant="destructive">Reorder Now</Button>
                      ) : (
                        <span className="text-green-500">Sufficient</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default StockManagement;