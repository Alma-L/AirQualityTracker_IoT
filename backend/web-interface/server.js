const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const cassandra = require('cassandra-driver');
const kafka = require('kafka-node');
const path = require('path');
const cors = require('cors');
const axios = require('axios');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Configuration
const CASSANDRA_HOST = process.env.CASSANDRA_HOST || 'localhost';
const KAFKA_BROKER = process.env.KAFKA_BROKER || 'localhost:9092';
const PORT = process.env.PORT || 3000;

// Twilio Configuration (optional)
const TWILIO_CONFIG = {
    accountSid: process.env.TWILIO_ACCOUNT_SID || '',
    authToken: process.env.TWILIO_AUTH_TOKEN || '',
    phoneNumber: process.env.TWILIO_PHONE_NUMBER || '',
    targetPhone: process.env.ALERT_PHONE_NUMBERS || ''
};

// Initialize Twilio client
let twilioClient = null;
try {
    const twilio = require('twilio');
    if (TWILIO_CONFIG.accountSid && TWILIO_CONFIG.authToken) {
        twilioClient = twilio(TWILIO_CONFIG.accountSid, TWILIO_CONFIG.authToken);
        console.log('📱 Twilio client initialized');
    }
} catch (error) {
    console.log('⚠️ Twilio not available:', error.message);
}

// Alert system
let alertBatch = [];
let lastSMSSent = 0;
const SMS_COOLDOWN = 1800000; // 30 minutes between SMS batches

// Initialize Cassandra connection
let cassandraClient = null;
let cassandraConnected = false;

async function connectToCassandra() {
    try {
        const cluster = new cassandra.Client({
            contactPoints: [CASSANDRA_HOST],
            localDataCenter: 'datacenter1',
            keyspace: 'air_quality_monitoring'
        });
        
        await cluster.connect();
        cassandraClient = cluster;
        cassandraConnected = true;
        console.log('✅ Connected to Cassandra');
    } catch (error) {
        console.error('❌ Failed to connect to Cassandra:', error);
        cassandraConnected = false;
    }
}

// Initialize Kafka consumer
let kafkaConsumer = null;

function connectToKafka() {
    try {
        const consumer = new kafka.Consumer(
            new kafka.KafkaClient({ kafkaHost: KAFKA_BROKER }),
            [{ topic: 'air-quality-data', partition: 0 }],
            { autoCommit: true }
        );

        consumer.on('message', function (message) {
            try {
                const data = JSON.parse(message.value);
                console.log('📊 Received air quality data:', data.sensor_id);
                
                // Broadcast to all connected WebSocket clients
                wss.clients.forEach((client) => {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(JSON.stringify({
                            type: 'realtime_update',
                            sensor: data,
                            timestamp: new Date().toISOString()
                        }));
                    }
                });
                
                // Check for alerts
                checkAirQualityAlerts(data);
                
            } catch (error) {
                console.error('Error processing Kafka message:', error);
            }
        });

        consumer.on('error', function (error) {
            console.error('Kafka consumer error:', error);
        });

        kafkaConsumer = consumer;
        console.log('✅ Kafka consumer connected');
    } catch (error) {
        console.error('❌ Failed to connect to Kafka:', error);
    }
}

// Air Quality Alert System
function checkAirQualityAlerts(data) {
    try {
        const pm2_5 = data.air_quality_data?.pm2_5 || 0;
        const pm10 = data.air_quality_data?.pm10 || 0;
        const aqi = data.air_quality_data?.aqi || 'Unknown';
        const health_risk = data.air_quality_data?.health_risk || 'Unknown';
        
        let alert = null;
        
        // Create alerts based on air quality thresholds
        if (pm2_5 > 55.4 || pm10 > 254) {  // Unhealthy levels
            alert = {
                id: `alert_${Date.now()}_${data.sensor_id}`,
                type: 'POOR_AIR_QUALITY',
                severity: 'HIGH',
                message: `Poor air quality detected: PM2.5=${pm2_5}, PM10=${pm10}, AQI=${aqi}`,
                sensor_id: data.sensor_id,
                location: data.location?.name || 'Unknown',
                timestamp: new Date().toISOString(),
                aqi_level: aqi
            };
        } else if (pm2_5 > 35.4 || pm10 > 154) {  // Moderate levels
            alert = {
                id: `alert_${Date.now()}_${data.sensor_id}`,
                type: 'MODERATE_AIR_QUALITY',
                severity: 'MEDIUM',
                message: `Moderate air quality: PM2.5=${pm2_5}, PM10=${pm10}, AQI=${aqi}`,
                sensor_id: data.sensor_id,
                location: data.location?.name || 'Unknown',
                timestamp: new Date().toISOString(),
                aqi_level: aqi
            };
        }
        
        if (alert) {
            // Add to batch
            alertBatch.push(alert);
            
            // Broadcast alert to WebSocket clients
            wss.clients.forEach((client) => {
                if (client.readyState === WebSocket.OPEN) {
                    client.send(JSON.stringify({
                        type: 'alert_update',
                        alert: alert,
                        timestamp: new Date().toISOString()
                    }));
                }
            });
            
            // Process batched alerts
            processBatchedAlerts();
        }
        
    } catch (error) {
        console.error('❌ Error checking air quality alerts:', error);
    }
}

async function processBatchedAlerts() {
    try {
        const now = Date.now();
        
        // Check cooldown period
        if (now - lastSMSSent < SMS_COOLDOWN) {
            return;
        }
        
        // If no alerts in batch, skip
        if (alertBatch.length === 0) {
            return;
        }
        
        console.log(`📱 Processing ${alertBatch.length} batched alerts...`);
        
        // Group alerts by severity
        const highAlerts = alertBatch.filter(a => a.severity === 'HIGH');
        const mediumAlerts = alertBatch.filter(a => a.severity === 'MEDIUM');
        
        // Create batched SMS message
        let smsMessage = `🌍 AIR QUALITY ALERTS SUMMARY\n`;
        smsMessage += `📊 Total: ${alertBatch.length} alerts\n\n`;
        
        // Add high priority alerts first
        if (highAlerts.length > 0) {
            smsMessage += `🔴 HIGH PRIORITY (${highAlerts.length}):\n`;
            highAlerts.slice(0, 3).forEach(alert => {
                smsMessage += `• ${alert.location}: ${alert.type}\n`;
            });
            if (highAlerts.length > 3) {
                smsMessage += `• +${highAlerts.length - 3} more high alerts\n`;
            }
            smsMessage += `\n`;
        }
        
        // Add medium priority summary
        if (mediumAlerts.length > 0) {
            smsMessage += `🟡 MEDIUM: ${mediumAlerts.length} alerts\n`;
        }
        
        smsMessage += `\n⏰ ${new Date().toLocaleTimeString()}`;
        
        // Send batched SMS if there are HIGH priority alerts
        if (highAlerts.length > 0 && twilioClient) {
            try {
                const message = await twilioClient.messages.create({
                    body: smsMessage,
                    from: TWILIO_CONFIG.phoneNumber,
                    to: TWILIO_CONFIG.targetPhone
                });
                
                console.log('✅ Batched SMS sent successfully! Message SID:', message.sid);
            } catch (twilioError) {
                console.error('❌ Twilio SMS failed:', twilioError.message);
            }
        }
        
        // Clear batch and update timestamp
        alertBatch = [];
        lastSMSSent = now;
        
    } catch (error) {
        console.error('❌ Error processing batched alerts:', error);
    }
}

// API Endpoints
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        cassandra: cassandraConnected ? 'connected' : 'disconnected',
        kafka: kafkaConsumer ? 'connected' : 'disconnected',
        websocket: wss.clients.size,
        timestamp: new Date().toISOString()
    });
});

// Get latest readings from all sensors
app.get('/api/sensors/latest', async (req, res) => {
    if (!cassandraConnected) {
        return res.status(503).json({ error: 'Database not connected' });
    }

    try {
        const query = `
            SELECT sensor_id, timestamp, location_name, area_type, 
                   pm2_5, pm10, aqi, health_risk, 
                   temperature_celsius, humidity_percent, weather_condition
            FROM air_quality_data 
            WHERE timestamp IN (
                SELECT MAX(timestamp) 
                FROM air_quality_data 
                GROUP BY sensor_id
            )
            ALLOW FILTERING
        `;
        
        const result = await cassandraClient.execute(query);
        res.json(result.rows);
    } catch (error) {
        console.error('Error fetching latest readings:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Get recent readings for a specific sensor
app.get('/api/sensors/:sensorId/recent', async (req, res) => {
    if (!cassandraConnected) {
        return res.status(503).json({ error: 'Database not connected' });
    }

    try {
        const { sensorId } = req.params;
        const limit = parseInt(req.query.limit) || 20;
        
        const query = `
            SELECT timestamp, pm2_5, pm10, aqi, health_risk, 
                   temperature_celsius, humidity_percent, weather_condition
            FROM air_quality_data 
            WHERE sensor_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        `;
        
        const result = await cassandraClient.execute(query, [sensorId, limit]);
        res.json(result.rows);
    } catch (error) {
        console.error('Error fetching sensor readings:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Get system statistics
app.get('/api/stats', async (req, res) => {
    if (!cassandraConnected) {
        return res.status(503).json({ error: 'Database not connected' });
    }

    try {
        // Get basic stats
        const sensorCountQuery = 'SELECT COUNT(DISTINCT sensor_id) as count FROM air_quality_data';
        const sensorCountResult = await cassandraClient.execute(sensorCountQuery);
        const sensorCount = sensorCountResult.rows[0]?.count || 0;

        // Get total records
        const totalRecordsQuery = 'SELECT COUNT(*) as count FROM air_quality_data';
        const totalRecordsResult = await cassandraClient.execute(totalRecordsQuery);
        const totalRecords = totalRecordsResult.rows[0]?.count || 0;

        // Get alerts count
        const alertsCountQuery = 'SELECT COUNT(*) as count FROM air_quality_alerts';
        const alertsCountResult = await cassandraClient.execute(alertsCountQuery);
        const alertsCount = alertsCountResult.rows[0]?.count || 0;

        res.json({
            sensorCount,
            totalRecords,
            alertsCount,
            uptime: process.uptime(),
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Error fetching system stats:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// WebSocket connection handling
wss.on('connection', (ws) => {
    console.log('🔌 New WebSocket connection');
    
    ws.on('close', () => {
        console.log('🔌 WebSocket connection closed');
    });
});

// Start server
async function startServer() {
    try {
        await connectToCassandra();
        connectToKafka();
        
        server.listen(PORT, () => {
            console.log(`🚀 Air Quality Web Interface running on port ${PORT}`);
            console.log(`📊 Health check: http://localhost:${PORT}/api/health`);
        });
    } catch (error) {
        console.error('❌ Failed to start server:', error);
        process.exit(1);
    }
}

startServer();
