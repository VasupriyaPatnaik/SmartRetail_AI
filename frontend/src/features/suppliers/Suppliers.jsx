import { useEffect, useState } from "react";
import axios from "axios";

const Suppliers = () => {
    const [suppliers, setSuppliers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios.get("http://localhost:5000/api/suppliers")
            .then(response => {
                setSuppliers(response.data);
                setLoading(false);
            })
            .catch(error => {
                setError("Failed to fetch supplier data");
                setLoading(false);
            });
    }, []);

    const handleRestock = (supplierId) => {
        axios.post(`http://localhost:5000/api/restock/${supplierId}`)
            .then(() => {
                alert("Restock request sent successfully!");
            })
            .catch(() => {
                alert("Failed to send restock request");
            });
    };

    if (loading) return <p>Loading suppliers...</p>;
    if (error) return <p>{error}</p>;

    return (
        <div className="container mt-4">
            <h2>Supplier Management</h2>
            <table className="table table-bordered">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Contact</th>
                        <th>Stock Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {suppliers.map(supplier => (
                        <tr key={supplier.id}>
                            <td>{supplier.id}</td>
                            <td>{supplier.name}</td>
                            <td>{supplier.contact}</td>
                            <td>{supplier.stock_status}</td>
                            <td>
                                <button className="btn btn-primary" onClick={() => handleRestock(supplier.id)}>
                                    Restock
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default Suppliers;