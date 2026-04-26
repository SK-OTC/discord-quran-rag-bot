import React, { useEffect, useState } from 'react';
import { Activity, MessageSquare, Clock, Star, AlertTriangle } from 'lucide-react';
import MetricCard from './components/MetricCard';
import MetricChart from './components/MetricChart';
import './App.css';

const DEFAULT_PROMETHEUS_URL = 'http://localhost:9090';
const PROMETHEUS_URL = process.env.REACT_APP_PROMETHEUS_URL || DEFAULT_PROMETHEUS_URL;

const buildUrl = (path, params) => {
  const url = new URL(`${PROMETHEUS_URL}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) url.searchParams.append(key, String(value));
  });
  return url.toString();
};

const queryInstant = async (expr) => {
  const response = await fetch(buildUrl('/api/v1/query', { query: expr }));
  console.log(buildUrl('/api/v1/query', { query: expr }));
  if (!response.ok) throw new Error(`Prometheus instant query failed: ${expr}`);
  return response.json();
};

const queryRange = async (expr, start, end, step) => {
  const response = await fetch(buildUrl('/api/v1/query_range', { query: expr, start, end, step }));
  if (!response.ok) throw new Error(`Prometheus range query failed: ${expr}`);
  return response.json();
};

const parseInstantValue = (payload) => {
  const value = payload?.data?.result?.[0]?.value?.[1];
  return value !== undefined ? Number(value) : null;
};

const parseRangeSeries = (payload, fieldName) => {
  const values = payload?.data?.result?.[0]?.values || [];
  return values.map(([timestamp, value]) => ({
    time: new Date(timestamp * 1000).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    }),
    [fieldName]: Number(value),
  }));
};

function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('Loading...');
  const [commandCount, setCommandCount] = useState(null);
  const [avgLatency, setAvgLatency] = useState(null);
  const [feedbackRating, setFeedbackRating] = useState(null);
  const [commandChartData, setCommandChartData] = useState([]);
  const [latencyChartData, setLatencyChartData] = useState([]);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);

    const now = Math.floor(Date.now() / 1000);
    const oneHourAgo = now - 3600;
    const step = 300;

    try {
      const results = await Promise.allSettled([
        queryInstant('sum(up{job="quran-bot"})'),
        queryInstant('sum(discord_commands_total)'),
        queryInstant('histogram_quantile(0.5, sum(rate(rag_query_duration_seconds_bucket[5m])) by (le))'),
        queryInstant('histogram_quantile(0.5, sum(rate(feedback_rating_distribution_bucket[5m])) by (le))'),
        queryRange('sum(rate(discord_commands_total[5m]))', oneHourAgo, now, step),
        queryRange('histogram_quantile(0.5, sum(rate(rag_query_duration_seconds_bucket[5m])) by (le))', oneHourAgo, now, step),
      ]);

      const [statusResult, commandsResult, latencyResult, feedbackResult, commandSeriesResult, latencySeriesResult] = results;

      const statusValue = statusResult.status === 'fulfilled' ? parseInstantValue(statusResult.value) : null;
      const resolvedStatus = statusValue === null ? 'Unknown' : statusValue === 0 ? 'Offline' : 'Online';
      setStatus(resolvedStatus);

      const commandsValue = commandsResult.status === 'fulfilled' ? parseInstantValue(commandsResult.value) : null;
      setCommandCount(commandsValue !== null ? Math.round(commandsValue) : null);

      const latencyValue = latencyResult.status === 'fulfilled' ? parseInstantValue(latencyResult.value) : null;
      setAvgLatency(latencyValue !== null ? latencyValue : null);

      const feedbackValue = feedbackResult.status === 'fulfilled' ? parseInstantValue(feedbackResult.value) : null;
      setFeedbackRating(feedbackValue !== null ? feedbackValue : null);

      setCommandChartData(
        commandSeriesResult.status === 'fulfilled' ? parseRangeSeries(commandSeriesResult.value, 'commands') : []
      );
      setLatencyChartData(
        latencySeriesResult.status === 'fulfilled' ? parseRangeSeries(latencySeriesResult.value, 'latency') : []
      );
    } catch (err) {
      setError(err.message || 'Unable to fetch Prometheus metrics');
    } finally {
      setLoading(false);
    }
  };

  const statusColor = status === 'Online' ? '#10b981' : '#ef4444';

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1><Activity className="icon" /> Quran Bot Metrics Dashboard</h1>
        <p>Real-time monitoring of Discord bot performance</p>
      </header>

      {error && (
        <div className="error-banner">
          <AlertTriangle className="icon" />
          <span>Error: {error}</span>
        </div>
      )}

      <div className="metrics-grid">
        <MetricCard
          title="Bot Status"
          value={loading ? 'Loading...' : status}
          icon={<Activity />}
          color={statusColor}
        />
        <MetricCard
          title="Discord Commands"
          value={commandCount !== null ? commandCount.toLocaleString() : 'N/A'}
          icon={<MessageSquare />}
          color="#3b82f6"
        />
        <MetricCard
          title="Median Response Time"
          value={avgLatency !== null ? `${avgLatency.toFixed(2)}s` : 'N/A'}
          icon={<Clock />}
          color="#f59e0b"
        />
        <MetricCard
          title="Median Feedback Rating"
          value={feedbackRating !== null ? `${feedbackRating.toFixed(1)}/5` : 'N/A'}
          icon={<Star />}
          color="#ef4444"
        />
      </div>

      <div className="charts-section">
        <MetricChart title="Command Rate (per second)" data={commandChartData} />
        <MetricChart title="Median RAG Latency" data={latencyChartData} />
      </div>
    </div>
  );
}

export default App;
