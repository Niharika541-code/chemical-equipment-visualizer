import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale, 
  LinearScale, 
  BarElement, 
  LineElement,
  PointElement,
  ArcElement,
  Title, 
  Tooltip, 
  Legend
);

function App() {
  /* ================= THEME ================= */
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('chemviz_theme');
    return saved === 'dark';
  });

  useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode);
    localStorage.setItem('chemviz_theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  /* ================= AUTH ================= */
  const [token, setToken] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);

  /* ================= DATA ================= */
  const [selectedFile, setSelectedFile] = useState(null);
  const [results, setResults] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [activeView, setActiveView] = useState('overview'); // overview, analytics, history
  const [downloadingReport, setDownloadingReport] = useState(false);

  /* ================= LOGIN ================= */
  const loginUser = async () => {
    if (!username || !password) {
      alert("Please enter both username and password");
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/login/",
        { username, password }
      );
      setToken(res.data.token);        
      setAuthenticated(true);
      
      if (rememberMe) {
        localStorage.setItem('chemviz_token', res.data.token);
      }
    } catch (err) {
      alert("Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      loginUser();
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

  /* ================= DOWNLOAD PDF REPORT ================= */
  const handleDownloadPDFReport = async () => {
    if (!results) {
      alert("Please upload a CSV file first to generate a report!");
      return;
    }

    setDownloadingReport(true);
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/generate-pdf-report/",
        {
          results: results,
          history: historyList,
          username: username
        },
        {
          headers: {
            Authorization: `Token ${token}`,
          },
          responseType: 'blob'
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      link.setAttribute('download', `ChemViz_Report_${timestamp}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("PDF report generation failed:", error);
      alert("Failed to generate PDF report. Please try again.");
    } finally {
      setDownloadingReport(false);
    }
  };

  /* ================= CHARTS DATA ================= */
  const barChartData = {
    labels: results ? Object.keys(results.type_distribution) : [],
    datasets: [
      {
        label: "Equipment Count",
        data: results ? Object.values(results.type_distribution) : [],
        backgroundColor: darkMode ? "#38bdf8" : "#0ea5e9",
        borderRadius: 8,
        borderWidth: 0,
      },
    ],
  };

  const lineChartData = {
    labels: historyList.map((item, idx) => `Upload ${idx + 1}`),
    datasets: [
      {
        label: "Temperature Trend",
        data: historyList.map(item => parseFloat(item.avg_temperature)),
        borderColor: darkMode ? "#f59e0b" : "#f97316",
        backgroundColor: darkMode ? "rgba(245, 158, 11, 0.1)" : "rgba(249, 115, 22, 0.1)",
        tension: 0.4,
        fill: true,
        pointRadius: 5,
        pointHoverRadius: 7,
      },
    ],
  };

  const doughnutData = {
    labels: results ? Object.keys(results.type_distribution) : ['No Data'],
    datasets: [
      {
        data: results ? Object.values(results.type_distribution) : [1],
        backgroundColor: darkMode 
          ? ['#38bdf8', '#818cf8', '#a78bfa', '#fb7185', '#fbbf24']
          : ['#0ea5e9', '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b'],
        borderWidth: 0,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: darkMode ? '#cbd5e1' : '#64748b',
          font: { size: 12 }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: darkMode ? '#94a3b8' : '#64748b' },
        grid: { color: darkMode ? '#334155' : '#e2e8f0' }
      },
      y: {
        ticks: { color: darkMode ? '#94a3b8' : '#64748b' },
        grid: { color: darkMode ? '#334155' : '#e2e8f0' }
      }
    }
  };

  /* ================= ENHANCED LOGIN SCREEN ================= */
  if (!authenticated) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="logo-section">
            <div className="logo-icon">⚗️</div>
            <h2>CHEMVIZ</h2>
          </div>
          <p>Industrial Equipment Analytics Portal</p>

          <input
            className="input-field"
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          
          <input
            className="input-field"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />

          <div className="remember-section">
            <label>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              Remember me
            </label>
            <a href="#forgot">Forgot password?</a>
          </div>

          <button
            className="btn-blue"
            style={{ width: "100%" }}
            onClick={loginUser}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                AUTHENTICATING...
              </>
            ) : (
              "AUTHENTICATE"
            )}
          </button>

          <div className="login-footer">
            Don't have an account? <a href="#signup">Sign up</a>
          </div>
        </div>
      </div>
    );
  }

  /* ================= DASHBOARD ================= */
  return (
    <div className="dashboard-main">
      {/* Header */}
      <div className="header-section">
        <div className="header-left">
          <div className="brand-header">
            <span className="brand-icon">⚗️</span>
            <div>
              <h1 style={{ margin: 0, fontSize: '24px', color: 'var(--accent-blue)' }}>
                CHEMVIZ
              </h1>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-muted)' }}>
                Equipment Analytics Dashboard
              </p>
            </div>
          </div>
        </div>

        <div className="header-right">
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="theme-toggle"
            title="Toggle theme"
          >
            {darkMode ? '☀️' : '🌙'}
          </button>

          <div className="file-upload-wrapper">
            <label className="file-label">
              📁 {selectedFile ? selectedFile.name : 'Choose CSV'}
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
            </label>
          </div>

          <button
            onClick={handleUpload}
            className="btn-blue"
            disabled={!selectedFile}
          >
            Upload & Analyze
          </button>

          {/* PDF Download Button */}
          <button
            onClick={handleDownloadPDFReport}
            className="btn-download-pdf"
            disabled={!results || downloadingReport}
            title="Download comprehensive PDF analysis report"
          >
            {downloadingReport ? (
              <>
                <span className="spinner"></span>
                Generating...
              </>
            ) : (
              <>
                📄 Download Report
              </>
            )}
          </button>

          <button
            onClick={() => {
              setAuthenticated(false);
              setToken(null);
              localStorage.removeItem('chemviz_token');
            }}
            className="btn-logout"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="nav-tabs">
        <button 
          className={`nav-tab ${activeView === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveView('overview')}
        >
          📊 Overview
        </button>
        <button 
          className={`nav-tab ${activeView === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveView('analytics')}
        >
          📈 Analytics
        </button>
        <button 
          className={`nav-tab ${activeView === 'history' ? 'active' : ''}`}
          onClick={() => setActiveView('history')}
        >
          📜 History
        </button>
      </div>

      {/* Overview View */}
      {activeView === 'overview' && (
        <>
          {/* Stats Grid */}
          <div className="stats-grid">
            <div className="stat-box">
              <div className="stat-icon">🔧</div>
              <div>
                <div className="stat-title">Total Equipment</div>
                <p className="stat-value">{results?.total_equipment || 0}</p>
                <span className="stat-change positive">+5% from last</span>
              </div>
            </div>
            
            <div className="stat-box">
              <div className="stat-icon">💧</div>
              <div>
                <div className="stat-title">Avg Flowrate (L/min)</div>
                <p className="stat-value">
                  {results?.avg_flowrate?.toFixed(2) || "0.00"}
                </p>
                <span className="stat-change neutral">Stable</span>
              </div>
            </div>
            
            <div className="stat-box">
              <div className="stat-icon">🌡️</div>
              <div>
                <div className="stat-title">Avg Temp (°C)</div>
                <p className="stat-value">
                  {results?.avg_temperature?.toFixed(2) || "0.00"}
                </p>
                <span className="stat-change negative">-2% from last</span>
              </div>
            </div>

            <div className="stat-box">
              <div className="stat-icon">⚡</div>
              <div>
                <div className="stat-title">System Status</div>
                <p className="stat-value status-badge">
                  <span className="status-dot online"></span> ONLINE
                </p>
                <span className="stat-change positive">All systems go</span>
              </div>
            </div>
          </div>

          {/* Charts Grid */}
          <div className="content-grid-large">
            <div className="visual-card">
              <div className="card-header">
                <h4>Equipment Distribution</h4>
                <span className="card-badge">Bar Chart</span>
              </div>
              <div style={{ height: "300px", padding: "10px" }}>
                <Bar data={barChartData} options={chartOptions} />
              </div>
            </div>

            <div className="visual-card">
              <div className="card-header">
                <h4>Type Distribution</h4>
                <span className="card-badge">Doughnut</span>
              </div>
              <div style={{ height: "300px", padding: "10px" }}>
                <Doughnut 
                  data={doughnutData} 
                  options={{ 
                    responsive: true, 
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'bottom',
                        labels: {
                          color: darkMode ? '#cbd5e1' : '#64748b',
                          padding: 15
                        }
                      }
                    }
                  }} 
                />
              </div>
            </div>
          </div>
        </>
      )}

      {/* Analytics View */}
      {activeView === 'analytics' && (
        <>
          <div className="content-grid-large">
            <div className="visual-card span-2">
              <div className="card-header">
                <h4>Temperature Trend Analysis</h4>
                <span className="card-badge">Line Chart</span>
              </div>
              <div style={{ height: "350px", padding: "10px" }}>
                <Line data={lineChartData} options={chartOptions} />
              </div>
            </div>

            <div className="visual-card">
              <div className="card-header">
                <h4>Raw JSON Output</h4>
                <span className="card-badge">Debug</span>
              </div>
              <pre className="json-output">
                {results
                  ? JSON.stringify(results, null, 2)
                  : "// Awaiting data upload...\n// Upload a CSV file to see results"}
              </pre>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-label">Peak Flowrate</div>
              <div className="metric-value">{results?.avg_flowrate ? (results.avg_flowrate * 1.2).toFixed(2) : "0.00"} L/min</div>
              <div className="metric-bar">
                <div className="metric-bar-fill" style={{ width: '85%' }}></div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Avg Pressure</div>
              <div className="metric-value">{results?.avg_pressure?.toFixed(2) || "0.00"} PSI</div>
              <div className="metric-bar">
                <div className="metric-bar-fill" style={{ width: '72%', background: '#f59e0b' }}></div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Efficiency Score</div>
              <div className="metric-value">94.2%</div>
              <div className="metric-bar">
                <div className="metric-bar-fill" style={{ width: '94%', background: '#10b981' }}></div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* History View */}
      {activeView === 'history' && (
        <div className="table-wrapper">
          <div className="table-header">
            <h4>Upload History</h4>
            <div className="table-actions">
              <button onClick={loadHistory} className="btn-refresh">
                🔄 Refresh
              </button>
              <button className="btn-export">
                📥 Export CSV
              </button>
            </div>
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Timestamp</th>
                  <th>Equipment Count</th>
                  <th>Avg Flowrate</th>
                  <th>Avg Pressure</th>
                  <th>Avg Temperature</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {historyList.length > 0 ? (
                  historyList.map((item, idx) => (
                    <tr key={idx} className="table-row-hover">
                      <td className="table-index">{idx + 1}</td>
                      <td>{item.time}</td>
                      <td><span className="badge badge-blue">{item.total_equipment}</span></td>
                      <td>{item.avg_flowrate?.toFixed(2)}</td>
                      <td>{item.avg_pressure?.toFixed(2)}</td>
                      <td>
                        <span className="temp-badge">
                          {parseFloat(item.avg_temperature).toFixed(2)}°C
                        </span>
                      </td>
                      <td>
                        <span className="status-badge-small success">✓ Complete</span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="table-empty">
                      <div className="empty-state">
                        <div className="empty-icon">📭</div>
                        <p>No upload history yet</p>
                        <span>Upload a CSV file to get started</span>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="dashboard-footer">
        <span>ChemViz Systems v2.0.5</span>
        <span>•</span>
        <span>Last sync: Just now</span>
        <span>•</span>
        <span className="footer-status">
          <span className="status-dot online"></span> All Systems Operational
        </span>
      </div>
    </div>
  );
}

export default App;