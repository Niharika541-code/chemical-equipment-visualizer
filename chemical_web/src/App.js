import React, { useState, useEffect } from "react";
import axios from "axios";
import { Bar } from "react-chartjs-2";
import "./App.css";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend
);

function App() {
  /* ================= AUTH ================= */
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isCreatingUser, setIsCreatingUser] = useState(false);

  /* ================= DATA ================= */
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState(null);

  /* ================= TIME ================= */
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  /* ================= LOGIN ================= */
  const loginUser = async () => {
    try {
      const res = await axios.post("http://127.0.0.1:8000/api/login/", {
        username,
        password,
      });
      setToken(res.data.token);
    } catch {
      alert("Invalid credentials");
    }
  };

  /* ================= CREATE USER ================= */
  const createUser = async () => {
    try {
      await axios.post("http://127.0.0.1:8000/api/create-user/", {
        username,
        password,
      });
      alert("User created successfully! Please login.");
      setIsCreatingUser(false);
    } catch {
      alert("User already exists or error occurred");
    }
  };

  /* ================= FILE UPLOAD ================= */
  const uploadFile = async () => {
    if (!file) return alert("Select CSV first");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/upload/",
        formData,
        { headers: { Authorization: `Token ${token}` } }
      );
      setSummary(res.data.summary);
    } catch {
      alert("Upload failed");
    }
  };

  const loadHistory = async () => {
    await axios.get("http://127.0.0.1:8000/api/history/", {
      headers: { Authorization: `Token ${token}` },
    });
    alert("History loaded (check table if enabled)");
  };

  const downloadReport = () => {
    window.open("http://127.0.0.1:8000/api/report/", "_blank");
  };

  /* ================= LOGIN SCREEN ================= */
  if (!token) {
    return (
      <div className="login-bg">
        <div className="login-card">
          <h2>CHEM-VIZ</h2>

          <input
            placeholder="Username"
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            onChange={(e) => setPassword(e.target.value)}
          />

          {!isCreatingUser ? (
            <>
              <button onClick={loginUser}>Login</button>
              <p className="link" onClick={() => setIsCreatingUser(true)}>
                Create new user
              </p>
            </>
          ) : (
            <>
              <button onClick={createUser}>Create User</button>
              <p className="link" onClick={() => setIsCreatingUser(false)}>
                Back to login
              </p>
            </>
          )}
        </div>
      </div>
    );
  }

  /* ================= DASHBOARD ================= */
  return (
    <div className="layout">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div>
          <div className="logo">🧪 CHEM-VIZ</div>

          <p className="section-title">Data Upload</p>
          <input type="file" onChange={(e) => setFile(e.target.files[0])} />
          <button onClick={uploadFile}>Upload CSV</button>
          <button onClick={loadHistory}>Load History</button>
        </div>

        <div className="sidebar-footer">
          <div className="big-time">
            {time.toLocaleDateString()} <br />
            {time.toLocaleTimeString()}
          </div>
          <div className="user-btn">👤 {username}</div>
        </div>
      </aside>

      {/* MAIN */}
      <main className="dashboard">
        <header className="topbar">
          <h2>Chemical Equipment Parameter Visualizer</h2>
        </header>

        {summary && (
          <>
            <div className="cards">
              <div className="card">
                <p>Total Equipment</p>
                <h1>{summary.total_equipment}</h1>
              </div>
              <div className="card">
                <p>Avg Flowrate</p>
                <h1>{summary.avg_flowrate}</h1>
              </div>
              <div className="card">
                <p>Avg Pressure</p>
                <h1>{summary.avg_pressure}</h1>
              </div>
              <div className="card">
                <p>Avg Temperature</p>
                <h1>{summary.avg_temperature}</h1>
              </div>
            </div>

            <div className="grid">
              <div className="panel">
                <Bar
                  data={{
                    labels: Object.keys(summary.type_distribution),
                    datasets: [
                      {
                        label: "Equipment",
                        data: Object.values(summary.type_distribution),
                        backgroundColor: "#3b82f6",
                      },
                    ],
                  }}
                />
              </div>

              <div className="panel">
                <pre>{JSON.stringify(summary, null, 2)}</pre>
                <button onClick={downloadReport}>Download PDF</button>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
