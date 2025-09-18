const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = process.env.PORT || 3001;
const SPARK_PYTHON_PATH = process.env.SPARK_PYTHON_PATH || 'python';
const SPARK_SERVICE_PATH = path.join(__dirname, 'spark_streaming_service.py');

// Store connected clients
const clients = new Set();
let sparkProcess = null;
let isSparkRunning = false;

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// WebSocket connection handling
wss.on('connection', (ws) => {
    console.log('🔌 New WebSocket client connected');
    clients.add(ws);
    
    ws.on('close', () => {
        console.log('🔌 WebSocket client disconnected');
        clients.delete(ws);
    });
    
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        clients.delete(ws);
    });
});

// Broadcast data to all connected clients
function broadcast(data) {
    const message = JSON.stringify(data);
    clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
}

// Start Spark Streaming service
function startSparkStreaming() {
    if (isSparkRunning) {
        console.log('Spark streaming already running');
        return;
    }
    
    console.log('🚀 Starting Spark Streaming service...');
    
    sparkProcess = spawn(SPARK_PYTHON_PATH, [SPARK_SERVICE_PATH], {
        cwd: __dirname,
        stdio: ['pipe', 'pipe', 'pipe']
    });
    
    sparkProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log('Spark stdout:', output);
        
        // Try to parse JSON data from Spark service
        try {
            const lines = output.split('\n');
            for (const line of lines) {
                if (line.trim().startsWith('{') && line.trim().endsWith('}')) {
                    const jsonData = JSON.parse(line.trim());
                    broadcast({
                        type: 'realtime_update',
                        data: jsonData
                    });
                }
            }
        } catch (error) {
            // Not JSON data, just log it
        }
    });
    
    sparkProcess.stderr.on('data', (data) => {
        console.error('Spark stderr:', data.toString());
    });
    
    sparkProcess.on('close', (code) => {
        console.log(`Spark process exited with code ${code}`);
        isSparkRunning = false;
        sparkProcess = null;
    });
    
    sparkProcess.on('error', (error) => {
        console.error('Failed to start Spark process:', error);
        isSparkRunning = false;
        sparkProcess = null;
    });
    
    isSparkRunning = true;
    console.log('✅ Spark Streaming service started');
}

// Stop Spark Streaming service
function stopSparkStreaming() {
    if (sparkProcess) {
        console.log('🛑 Stopping Spark Streaming service...');
        sparkProcess.kill('SIGTERM');
        sparkProcess = null;
        isSparkRunning = false;
        console.log('✅ Spark Streaming service stopped');
    }
}

// API Routes

// Health check
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        message: 'Air Quality Tracker with Spark Streaming',
        version: '2.0.0',
        spark_running: isSparkRunning,
        websocket_connections: clients.size,
        timestamp: new Date().toISOString()
    });
});

// Get real-time data
app.get('/api/realtime', (req, res) => {
    // This would typically query the Spark service for real-time data
    res.json({
        message: 'Real-time data endpoint - data comes via WebSocket',
        spark_running: isSparkRunning
    });
});

// Get system statistics
app.get('/api/stats', async (req, res) => {
    try {
        // This would typically query the Spark service for statistics
        res.json({
            sensorCount: 0,
            totalRecords: 0,
            activeAlerts: 0,
            averageAQI: 0,
            uptimeSeconds: 0,
            spark_running: isSparkRunning
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get sensors list
app.get('/api/sensors', (req, res) => {
    res.json({
        sensors: [
            'sensor-urban-1',
            'sensor-industrial-1',
            'sensor-residential-1',
            'sensor-mobile-1',
            'sensor-wearable-1',
            'sensor-drone-1'
        ]
    });
});

// Get sensor analytics
app.get('/api/analytics/:sensorId', async (req, res) => {
    const { sensorId } = req.params;
    const hours = parseInt(req.query.hours) || 24;
    
    try {
        // This would typically query the Spark service for analytics
        res.json({
            sensor_id: sensorId,
            time_period_hours: hours,
            pm25: { min: 0, max: 0, average: 0 },
            pm10: { min: 0, max: 0, average: 0 },
            aqi: { min: 0, max: 0, average: 0 },
            readings_count: 0,
            trend: 'stable'
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get latest sensor readings
app.get('/api/sensors/latest', (req, res) => {
    res.json([]);
});

// Get recent readings for a sensor
app.get('/api/sensors/:sensorId/recent', (req, res) => {
    const { sensorId } = req.params;
    const limit = parseInt(req.query.limit) || 20;
    
    res.json([]);
});

// ML Analysis endpoint
app.get('/api/ml-analysis', (req, res) => {
    const { sensor, algorithm, hours } = req.query;
    
    res.json({
        sensor: sensor,
        algorithm: algorithm,
        hours: parseInt(hours),
        total_readings: 0,
        anomalies_count: 0,
        anomalies: [],
        timestamps: [],
        pm25: [],
        pm10: [],
        scores: []
    });
});

// Alerts endpoint
app.get('/api/alerts', (req, res) => {
    res.json([]);
});

// Control endpoints
app.post('/api/spark/start', (req, res) => {
    startSparkStreaming();
    res.json({ message: 'Spark streaming started', running: isSparkRunning });
});

app.post('/api/spark/stop', (req, res) => {
    stopSparkStreaming();
    res.json({ message: 'Spark streaming stopped', running: isSparkRunning });
});

app.get('/api/spark/status', (req, res) => {
    res.json({ running: isSparkRunning });
});

// Serve the main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down server...');
    stopSparkStreaming();
    server.close(() => {
        console.log('✅ Server closed');
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Shutting down server...');
    stopSparkStreaming();
    server.close(() => {
        console.log('✅ Server closed');
        process.exit(0);
    });
});

// Start the server
server.listen(PORT, () => {
    console.log(`🚀 Server running on http://localhost:${PORT}`);
    console.log(`📊 WebSocket server running on ws://localhost:${PORT}`);
    console.log(`🔧 Spark integration available at /api/spark/*`);
    
    // Auto-start Spark streaming
    startSparkStreaming();
});

module.exports = { app, server, wss };

