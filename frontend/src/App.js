import React, { useEffect, useState } from 'react';
import './App.css';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

function fetchRevenueData() {
  return fetch(`${BACKEND_URL}/revenue`).then(res => res.json()).then(res => res.data);
}

async function triggerUpdate() {
  try {
    const response = await fetch(`${BACKEND_URL}/trigger-update`, {
      method: 'POST',
    });
    const data = await response.json();
    if (data.status === 'success') {
      // Refresh the data after successful update
      const newData = await fetchRevenueData();
      return newData;
    } else {
      alert('Failed to update data: ' + data.message);
    }
  } catch (error) {
    alert('Failed to update data: ' + error.message);
  }
}

function fetchLastUpdated() {
  return fetch(`${BACKEND_URL}/last_updated.txt`).then(res => res.text());
}

const ownerMap = {
  'aj@sfdata.com': 'AJ',
  'kiriti@sfdata.com': 'Kiriti',
  // Add more mappings as needed
  '(no owner)': 'Unassigned',
};

function formatCurrency(num) {
  if (num == null) return '$0';
  return '$' + num.toLocaleString();
}

function getMonthName(key) {
  if (!key) return '';
  const [mon, year] = key.split('_');
  return mon.charAt(0).toUpperCase() + mon.slice(1) + ' ' + year;
}

function getMonthKeys(data) {
  // Get all month keys from the first AE
  if (!data.length) return [];
  return Object.keys(data[0]).filter(k => /\d{4}/.test(k));
}

function getProgressBarColor(progress) {
  if (progress >= 100) return '#2ecc40'; // Green
  if (progress >= 90) return '#2ecc40'; // Green
  if (progress >= 50) return '#f7d51d'; // Yellow
  if (progress >= 0) return '#ff7043'; // Red/Orange
  return '#ccc';
}

function App() {
  const [data, setData] = useState([]);
  const [lastUpdated, setLastUpdated] = useState('');
  const [goals, setGoals] = useState({});
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    fetchRevenueData().then(setData);
    fetchLastUpdated().then(setLastUpdated);
  }, []);

  const monthKeys = getMonthKeys(data);
  const currentMonthKey = monthKeys[monthKeys.length - 1];

  // Move 'Unassigned' to the end of the data array
  const sortedData = [
    ...data.filter(ae => (ae.owner_email && ae.owner_email !== '(no owner)')),
    ...data.filter(ae => ae.owner_email === '(no owner)')
  ];

  // Team totals for current month
  const teamCurrentRevenue = sortedData.reduce((sum, ae) => sum + (ae[currentMonthKey] || 0), 0);
  const teamGoal = sortedData.reduce((sum, ae) => {
    const lastMonth = monthKeys[monthKeys.length - 2];
    const defaultGoal = Math.round((ae[lastMonth] || 0) * 1.25);
    const goal = goals[ae.owner_email] || defaultGoal;
    return sum + goal;
  }, 0);
  const teamProgress = teamGoal ? Math.round((teamCurrentRevenue / teamGoal) * 100) : 0;

  // Find top performer for current month by percent of goal achieved
  const topPerformer = sortedData.reduce((top, ae) => {
    const lastMonth = monthKeys[monthKeys.length - 2];
    const defaultGoal = Math.round((ae[lastMonth] || 0) * 1.25);
    const goal = goals[ae.owner_email] || defaultGoal;
    const currentRevenue = ae[currentMonthKey] || 0;
    const percent = goal ? (currentRevenue / goal) * 100 : 0;
    if (!top) return { ...ae, percent };
    return percent > top.percent ? { ...ae, percent } : top;
  }, null);

  // Find last place performer for current month by percent of goal achieved
  const lastPerformer = sortedData.reduce((last, ae) => {
    const lastMonth = monthKeys[monthKeys.length - 2];
    const defaultGoal = Math.round((ae[lastMonth] || 0) * 1.25);
    const goal = goals[ae.owner_email] || defaultGoal;
    const currentRevenue = ae[currentMonthKey] || 0;
    const percent = goal ? (currentRevenue / goal) * 100 : 0;
    if (!last) return { ...ae, percent };
    return percent < last.percent ? { ...ae, percent } : last;
  }, null);

  return (
    <div className="App">
      {topPerformer && (
        <div className="top-performer-tile">
          <span role="img" aria-label="trophy" style={{ fontSize: 28, marginRight: 10 }}>🏆</span>
          <span style={{ fontWeight: 700, fontSize: 20 }}>Top Performer:</span>
          <span style={{ fontWeight: 600, marginLeft: 10, color: '#3a3a8a', fontSize: 18 }}>
            {(() => {
              const name = ownerMap[topPerformer.owner_email] || topPerformer.owner_email;
              return name.split('@')[0].charAt(0).toUpperCase() + name.split('@')[0].slice(1);
            })()}
          </span>
          <span style={{ marginLeft: 16, fontSize: 16 }}>
            Progress: <b>{Math.round(topPerformer.percent || 0)}%</b>
          </span>
        </div>
      )}
      {lastPerformer && (
        <div className="top-performer-tile" style={{ background: '#e6fff7', border: '2px solid #80cbc4' }}>
          <span role="img" aria-label="turtle" style={{ fontSize: 28, marginRight: 10 }}>🐢</span>
          <span style={{ fontWeight: 700, fontSize: 20 }}>In Last:</span>
          <span style={{ fontWeight: 600, marginLeft: 10, color: '#3a3a8a', fontSize: 18 }}>
            {(() => {
              const name = ownerMap[lastPerformer.owner_email] || lastPerformer.owner_email;
              return name.split('@')[0].charAt(0).toUpperCase() + name.split('@')[0].slice(1);
            })()}
          </span>
          <span style={{ marginLeft: 16, fontSize: 16 }}>
            Progress: <b>{Math.round(lastPerformer.percent || 0)}%</b>
          </span>
        </div>
      )}
      <h2>AE Revenue Live Tracker</h2>
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
        <div style={{ fontSize: 12, color: '#888' }}>Last updated: {lastUpdated && new Date(lastUpdated).toLocaleString()}</div>
        <button 
          onClick={async () => {
            setIsUpdating(true);
            await triggerUpdate();
            setIsUpdating(false);
          }}
          disabled={isUpdating}
          style={{
            padding: '8px 16px',
            backgroundColor: '#3a3a8a',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isUpdating ? 'not-allowed' : 'pointer',
            opacity: isUpdating ? 0.7 : 1
          }}
        >
          {isUpdating ? 'Updating...' : '🔄 Update Data'}
        </button>
      </div>
      <div className="team-card">
        <div className="ae-name" style={{ fontSize: '1.4em', marginBottom: 8 }}>Team</div>
        <div style={{ marginBottom: 8 }}>
          <b>Current Month ({getMonthName(currentMonthKey)}):</b> {formatCurrency(teamCurrentRevenue)}<br />
          <span>Goal: {formatCurrency(teamGoal)} | Progress: {teamProgress}%</span>
        </div>
        <div className="progress-bar-bg" style={{ marginBottom: 0 }}>
          <div
            className="progress-bar"
            style={{
              width: `${teamProgress}%`,
              background: getProgressBarColor(teamProgress),
            }}
          >
            {teamProgress > 0 && (
              <span style={{ color: '#fff', fontWeight: 700, fontSize: 16 }}>
                {teamProgress}%
              </span>
            )}
            {teamProgress >= 100 && (
              <span style={{
                color: '#fff',
                fontWeight: 700,
                marginLeft: 8,
                fontSize: 18,
                verticalAlign: 'middle',
              }}>✔</span>
            )}
          </div>
        </div>
      </div>
      {/* First row: first 2 cards */}
      <div className="card-grid">
        {sortedData.slice(0, 2).map((ae, idx) => {
          const name = ownerMap[ae.owner_email] || ae.owner_email;
          const pastRevenue = monthKeys.slice(0, -1).map(k => ({
            key: k,
            value: ae[k] || 0,
          }));
          const currentRevenue = ae[currentMonthKey] || 0;
          const lastMonth = monthKeys[monthKeys.length - 2];
          const defaultGoal = Math.round((ae[lastMonth] || 0) * 1.25);
          const goal = goals[ae.owner_email] || defaultGoal;
          const progress = goal ? Math.round((currentRevenue / goal) * 100) : 0;
          const chartData = monthKeys.map(k => ({
            month: getMonthName(k),
            revenue: ae[k] || 0,
          }));
          return (
            <div className="ae-card" key={ae.owner_email}>
              <div className="ae-name">{name.split('@')[0].charAt(0).toUpperCase() + name.split('@')[0].slice(1)}</div>
              <div className="ae-past-revenue">
                <b>Past Revenue:</b>
                <ul>
                  {pastRevenue.map(pr => (
                    <li key={pr.key}>{getMonthName(pr.key)}: <b>{formatCurrency(pr.value)}</b></li>
                  ))}
                </ul>
              </div>
              <div className="ae-current">
                <b>Current Month ({getMonthName(currentMonthKey)}):</b> {formatCurrency(currentRevenue)}<br />
                <span>Goal: $</span>
                <input
                  type="number"
                  className="goal-input"
                  value={goal}
                  onChange={e => setGoals({ ...goals, [ae.owner_email]: Number(e.target.value) })}
                  style={{ width: 80, marginRight: 8 }}
                />
                <span>Progress: {progress}%</span>
                <div className="progress-bar-bg">
                  <div
                    className="progress-bar"
                    style={{
                      width: `${progress}%`,
                      background: getProgressBarColor(progress),
                    }}
                  >
                    {progress > 0 && (
                      <span style={{ color: '#fff', fontWeight: 700, fontSize: 16 }}>
                        {progress}%
                      </span>
                    )}
                    {progress >= 100 && (
                      <span style={{
                        color: '#fff',
                        fontWeight: 700,
                        marginLeft: 8,
                        fontSize: 18,
                        verticalAlign: 'middle',
                      }}>✔</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="ae-chart">
                <b>Monthly Revenue Chart:</b>
                <ResponsiveContainer width="100%" height={120}>
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="month" fontSize={10} />
                    <YAxis fontSize={10} />
                    <Tooltip formatter={formatCurrency} />
                    <Bar dataKey="revenue" fill="#8884d8" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>
      {/* Second row: the rest of the cards */}
      <div className="card-grid">
        {sortedData.slice(2).map((ae, idx) => {
          const name = ownerMap[ae.owner_email] || ae.owner_email;
          const pastRevenue = monthKeys.slice(0, -1).map(k => ({
            key: k,
            value: ae[k] || 0,
          }));
          const currentRevenue = ae[currentMonthKey] || 0;
          const lastMonth = monthKeys[monthKeys.length - 2];
          const defaultGoal = Math.round((ae[lastMonth] || 0) * 1.25);
          const goal = goals[ae.owner_email] || defaultGoal;
          const progress = goal ? Math.round((currentRevenue / goal) * 100) : 0;
          const chartData = monthKeys.map(k => ({
            month: getMonthName(k),
            revenue: ae[k] || 0,
          }));
          return (
            <div className="ae-card" key={ae.owner_email}>
              <div className="ae-name">{name.split('@')[0].charAt(0).toUpperCase() + name.split('@')[0].slice(1)}</div>
              <div className="ae-past-revenue">
                <b>Past Revenue:</b>
                <ul>
                  {pastRevenue.map(pr => (
                    <li key={pr.key}>{getMonthName(pr.key)}: <b>{formatCurrency(pr.value)}</b></li>
                  ))}
                </ul>
              </div>
              <div className="ae-current">
                <b>Current Month ({getMonthName(currentMonthKey)}):</b> {formatCurrency(currentRevenue)}<br />
                <span>Goal: $</span>
                <input
                  type="number"
                  className="goal-input"
                  value={goal}
                  onChange={e => setGoals({ ...goals, [ae.owner_email]: Number(e.target.value) })}
                  style={{ width: 80, marginRight: 8 }}
                />
                <span>Progress: {progress}%</span>
                <div className="progress-bar-bg">
                  <div
                    className="progress-bar"
                    style={{
                      width: `${progress}%`,
                      background: getProgressBarColor(progress),
                    }}
                  >
                    {progress > 0 && (
                      <span style={{ color: '#fff', fontWeight: 700, fontSize: 16 }}>
                        {progress}%
                      </span>
                    )}
                    {progress >= 100 && (
                      <span style={{
                        color: '#fff',
                        fontWeight: 700,
                        marginLeft: 8,
                        fontSize: 18,
                        verticalAlign: 'middle',
                      }}>✔</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="ae-chart">
                <b>Monthly Revenue Chart:</b>
                <ResponsiveContainer width="100%" height={120}>
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="month" fontSize={10} />
                    <YAxis fontSize={10} />
                    <Tooltip formatter={formatCurrency} />
                    <Bar dataKey="revenue" fill="#8884d8" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default App;