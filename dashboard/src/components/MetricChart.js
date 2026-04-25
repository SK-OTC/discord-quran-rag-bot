import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './MetricChart.css';

function MetricChart({ title, data }) {
  const dataKey = data?.[0] ? Object.keys(data[0]).find((key) => key !== 'time') : null;

  return (
    <div className="metric-chart">
      <h3 className="chart-title">{title}</h3>
      <div className="chart-container">
        {dataKey ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey={dataKey}
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="no-data-message">No chart data available</div>
        )}
      </div>
    </div>
  );
}

export default MetricChart;