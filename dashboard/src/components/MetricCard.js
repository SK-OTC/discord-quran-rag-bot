import React from 'react';
import './MetricCard.css';

function MetricCard({ title, value, icon, color }) {
  return (
    <div className="metric-card" style={{ borderLeftColor: color }}>
      <div className="metric-icon" style={{ color }}>
        {icon}
      </div>
      <div className="metric-content">
        <h3 className="metric-title">{title}</h3>
        <p className="metric-value">{value}</p>
      </div>
    </div>
  );
}

export default MetricCard;