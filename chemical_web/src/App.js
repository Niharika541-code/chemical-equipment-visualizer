import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function App() {
  /* ================= AUTH ================= */
  const [token, setToken] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");


  /* ================= DATA ================= */
  const [selectedFile, setSelectedFile] = useState(null);
  const [results, setResults] = useState(null);
  const [historyList, setHistoryList] = useState([]);

  /* ================= LOGIN ================= */
  const loginUser = async () => {
    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/login/",
        { username, password }
      );
      setToken(res.data.token);        
      setAuthenticated(true);
    } catch (err) {
      alert("Invalid username or password");
    }
  };

  /* ================= FILE ================= */
  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      alert("Please choose a CSV file first!");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/upload/",
        formData,
        {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "multipart/form-data",
          },
        }
      );
      setResults(response.data.summary);
      loadHistory();
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed (Unauthorized or backend error)");
    }
  };

  const loadHistory = async () => {
    try {
      const response = await axios.get(
        "http://127.0.0.1:8000/api/history/",
        {
          headers: {
            Authorization: `Token ${token}`,
          },
        }
      );
      setHistoryList(response.data);
    } catch (err) {
      console.error("History error:", err);
    }
  };

  /* ================= CHART ================= */
  const chartData = {
    labels: results ? Object.keys(results.type_distribution) : [],
    datasets: [
      {
        label: "Count",
        data: results ? Object.values(results.type_distribution) : [],
        backgroundColor: "#0ea5e9",
        borderRadius: 5,
      },
    ],
  };

  /* ================= LOGIN SCREEN ================= */
  if (!authenticated) {
    return (
      <div className="login-container">
        <div className="login-card">
          <h2 style={{ color: "#0ea5e9", marginBottom: "5px" }}>CHEMVIZ</h2>
          <p style={{ color: "#64748b", fontSize: "12px", marginBottom: "25px" }}>
            Portal Login
          </p>

          <input
            className="input-field"
            type="text"
            placeholder="Username"
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            className="input-field"
            type="password"
            placeholder="Password"
            onChange={(e) => setPassword(e.target.value)}
          />

          <button
            className="btn-blue"
            style={{ width: "100%" }}
            onClick={loginUser}
          >
            AUTHENTICATE
          </button>
        </div>
      </div>
    );
  }

  /* ================= DASHBOARD ================= */
  return (
    <div className="dashboard-main">
      <div className="header-section">
        <div>
          <h2 style={{ margin: 0 }}>Equipment Visualizer</h2>
          <p style={{ margin: 0, color: "#64748b", fontSize: "13px" }}>
            System Version 2.0.5
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <input type="file" onChange={handleFileChange} />
          <button className="btn-blue" onClick={handleUpload}>
            UPLOAD CSV
          </button>
          <button
            onClick={() => {
              setAuthenticated(false);
              setToken(null);
            }}
            style={{
              background: "none",
              border: "none",
              color: "#ef4444",
              cursor: "pointer",
              fontWeight: "600",
            }}
          >
            Logout
          </button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-box">
          <div className="stat-title">Total Equipment</div>
          <p className="stat-value">{results?.total_equipment || 0}</p>
        </div>
        <div className="stat-box">
          <div className="stat-title">Avg Flowrate (L/min)</div>
          <p className="stat-value">
            {results?.avg_flowrate?.toFixed(2) || "0.00"}
          </p>
        </div>
        <div className="stat-box">
          <div className="stat-title">Avg Temp (°C)</div>
          <p className="stat-value">
            {results?.avg_temperature || "0.0"}
          </p>
        </div>
      </div>

      <div className="content-grid">
        <div className="visual-card">
          <h4 style={{ marginTop: 0, marginBottom: "20px" }}>
            Distribution Map
          </h4>
          <div style={{ height: "300px" }}>
            <Bar
              data={chartData}
              options={{ responsive: true, maintainAspectRatio: false }}
            />
          </div>
        </div>

        <div className="visual-card">
          <h4 style={{ marginTop: 0, marginBottom: "20px" }}>
            Raw Output
          </h4>
          <pre>
            {results
              ? JSON.stringify(results, null, 2)
              : "// Awaiting data upload..."}
          </pre>
        </div>
      </div>

      <div className="table-wrapper">
        <div
          style={{
            padding: "15px 20px",
            display: "flex",
            justifyContent: "space-between",
            borderBottom: "1px solid var(--border-color)",
          }}
        >
          <h4 style={{ margin: 0 }}>Last 5 Uploads</h4>
          <button
            onClick={loadHistory}
            style={{
              color: "#0ea5e9",
              border: "none",
              background: "none",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            REFRESH
          </button>
        </div>

        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Count</th>
              <th>Flowrate</th>
              <th>Pressure</th>
              <th>Temperature</th>
            </tr>
          </thead>
          <tbody>
            {historyList.map((item, idx) => (
              <tr key={idx}>
                <td style={{ color: "#64748b" }}>{item.time}</td>
                <td>{item.total_equipment}</td>
                <td>{item.avg_flowrate?.toFixed(2)}</td>
                <td>{item.avg_pressure?.toFixed(2)}</td>
                <td
                  style={{ color: "#0ea5e9", fontWeight: "bold" }}
                >
                  {item.avg_temperature}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
