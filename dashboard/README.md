# Quran Bot Metrics Dashboard

A React-based web dashboard for monitoring Quran Discord Bot metrics from Prometheus.

## Features

- Real-time metrics display
- Interactive charts for command usage and response times
- Responsive design
- Auto-refresh every 30 seconds

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Usage

The dashboard connects to Prometheus at `http://localhost:9090` to fetch metrics. Make sure Prometheus is running and accessible.

## Integration with Discord

You can add a `/dashboard` command to your Discord bot that provides a link to this dashboard, or embed it in Discord messages.