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
const PORT = process.env.PORT || 8000;

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

// ------------------------------
// Save Sensor Reading (enhanced logs)
// ------------------------------
async function saveReadingToCassandra(data) {
    if (!cassandraConnected) {
        console.warn('⚠️ Attempted to save data but Cassandra is not connected:', JSON.stringify(data, null, 2));
        return;
    }

    try {
        const timestamp = new Date(data.timestamp || Date.now());

        const query = `
            INSERT INTO air_quality_data (
                sensor_id, timestamp, location_name, area_type,
                latitude, longitude,
                pm2_5, pm10, aqi, health_risk,
                visibility_meters, temperature_celsius, humidity_percent,
                weather_condition, pressure_hpa
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `;

        const params = [
            data.sensor_id,
            timestamp,
            data.location_name || 'Unknown',
            data.area_type || 'Unknown',
            data.latitude || null,
            data.longitude || null,
            data.pm2_5 ?? null,
            data.pm10 ?? null,
            data.aqi ?? 'Unknown',
            data.health_risk ?? 'Unknown',
            data.visibility_meters ?? null,
            data.temperature ?? null,
            data.humidity ?? null,
            data.weather_condition ?? null,
            data.pressure_hpa ?? null
        ];


        console.log(`💾 Saving reading for sensor ${data.sensor_id} at ${timestamp.toISOString()}`);
        await cassandraClient.execute(query, params, { prepare: true });
        console.log(`✅ Successfully saved data for sensor ${data.sensor_id}`);
    } catch (error) {
        console.error('❌ Failed to save reading to Cassandra');
        console.error('📦 Sensor Data:', JSON.stringify(data, null, 2));
        console.error('🛑 Error Details:', error.stack || error.message || error);
    }
}

// ------------------------------
// Kafka Consumer (enhanced logs)
// ------------------------------
function connectToKafka() {
    try {
        const consumer = new kafka.Consumer(
            new kafka.KafkaClient({ kafkaHost: KAFKA_BROKER }),
            [{ topic: 'air-quality-data', partition: 0 }],
            { autoCommit: true }
        );

        consumer.on('message', async (message) => {
            try {
                const data = JSON.parse(message.value);
                if (!data.sensor_id) {
                    console.warn('⚠️ Kafka message missing sensor_id:', message.value);
                    return;
                }

                console.log('📊 Received air quality data:', data.sensor_id);

                await saveReadingToCassandra(data);

                wss.clients.forEach(client => {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(JSON.stringify({
                            type: 'realtime_update',
                            sensor: data,
                            timestamp: new Date().toISOString()
                        }));
                    }
                });

                await checkAirQualityAlerts(data);
            } catch (err) {
                console.error('❌ Error processing Kafka message:', err.stack || err.message || err);
                console.error('📦 Original message:', message.value);
            }
        });

        consumer.on('error', error => {
            console.error('❌ Kafka consumer error:', error.stack || error.message || error);
            if (error.errors) {
                error.errors.forEach((e, idx) => {
                    console.error(`  [${idx}] Address: ${e.address}, Port: ${e.port}, Code: ${e.code}`);
                });
            }
        });

        kafkaConsumer = consumer;
        console.log('✅ Kafka consumer connected');
    } catch (error) {
        console.error('❌ Failed to connect to Kafka:', error.stack || error.message || error);
    }
}

app.post('/api/sensors/:sensorId', async (req, res) => {
    const { sensorId } = req.params;
    const data = req.body;

    try {
        // Save data to Cassandra
        await saveReadingToCassandra(data); // reuse your existing function
         await checkAirQualityAlerts(data); 
        res.status(200).json({ message: `Data received for ${sensorId}` });
    } catch (err) {
        console.error('Error saving sensor data:', err);
        res.status(500).json({ error: 'Internal server error' });
    }
});



app.get('/api/sensors/latest', async (req, res) => {
    if (!cassandraConnected) {
        return res.status(503).json({ error: 'Database not connected' });
    }

    try {
        // distinct sensor ids
        const sensorQuery = 'SELECT DISTINCT sensor_id FROM air_quality_data';
        const sensorRows = await cassandraClient.execute(sensorQuery);
        const sensorIds = sensorRows.rows.map(r => r.sensor_id);

        const latestReadings = [];
        for (const sensorId of sensorIds) {
            const query = `
                SELECT sensor_id, timestamp, location_name, area_type, latitude, longitude,
                       pm2_5, pm10, aqi, health_risk,
                       temperature_celsius, humidity_percent, weather_condition, pressure_hpa
                FROM air_quality_data
                WHERE sensor_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            `;
            const result = await cassandraClient.execute(query, [sensorId], { prepare: true });
            if (result.rows.length > 0) {
                latestReadings.push(result.rows[0]);
            }
        }

        res.json(latestReadings);
    } catch (error) {
        console.error('❌ Error in /api/sensors/latest:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.get('/api/sensors/:sensorId/recent', async (req, res) => {
    if (!cassandraConnected) {
        return res.status(503).json({ error: 'Database not connected' });
    }

    const { sensorId } = req.params;
    const limit = parseInt(req.query.limit || 20, 10);

    try {
        const query = `
            SELECT sensor_id, timestamp, pm2_5, pm10, aqi, health_risk,
                   temperature_celsius, humidity_percent, weather_condition,
                   location_name, area_type
            FROM air_quality_data
            WHERE sensor_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        `;
        const result = await cassandraClient.execute(query, [sensorId, limit], { prepare: true });
        res.json(result.rows);
    } catch (error) {
        console.error('❌ Error in /api/sensors/:sensorId/recent:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});


app.get('/api/analytics/:sensorId', async (req, res) => {
    if (!cassandraConnected) {
        return res.status(503).json({ error: 'Cassandra database not connected' });
    }

    const { sensorId } = req.params;
    const hours = parseInt(req.query.hours || "24", 10);

    try {
        const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000);

        const query = `
            SELECT pm2_5, pm10, aqi, timestamp
            FROM air_quality_data
            WHERE sensor_id = ? AND timestamp >= ?
            ALLOW FILTERING
        `;
        const result = await cassandraClient.execute(query, [sensorId, cutoffTime], { prepare: true });

        if (!result.rows.length) {
            return res.json({ error: "No data available for this sensor in the requested period" });
        }

        // Extract readings
        const pm25Values = result.rows.map(r => r.pm2_5).filter(v => v !== null && v !== undefined);
        const pm10Values = result.rows.map(r => r.pm10).filter(v => v !== null && v !== undefined);

        const aqiValues = result.rows
            .map(r => {
                if (r.aqi && r.aqi !== "Unknown") {
                    const parsed = parseFloat(r.aqi);
                    return isNaN(parsed) ? null : parsed;
                }
                return null;
            })
            .filter(v => v !== null);

        if (!pm25Values.length || !pm10Values.length) {
            return res.json({ error: "Insufficient data for analysis" });
        }

        res.json({
            sensor_id: sensorId,
            time_period_hours: hours,
            readings_count: pm25Values.length,
            pm25: {
                min: Math.min(...pm25Values),
                max: Math.max(...pm25Values),
                average: +(pm25Values.reduce((a, b) => a + b, 0) / pm25Values.length).toFixed(2),
            },
            pm10: {
                min: Math.min(...pm10Values),
                max: Math.max(...pm10Values),
                average: +(pm10Values.reduce((a, b) => a + b, 0) / pm10Values.length).toFixed(2),
            },
            aqi: {
                min: aqiValues.length ? Math.min(...aqiValues) : 0,
                max: aqiValues.length ? Math.max(...aqiValues) : 0,
                average: aqiValues.length
                    ? +(aqiValues.reduce((a, b) => a + b, 0) / aqiValues.length).toFixed(1)
                    : 0,
            },
            trend: "stable" // placeholder
        });

    } catch (error) {
        console.error("❌ Error in /api/analytics/:sensorId:", error);
        res.status(500).json({ error: `Error fetching analytics: ${error.message}` });
    }
});


let smartSensorsData = {};

function getSmartAQIClass(aqi) {
    if (aqi <= 50) return 'aqi-good';
    if (aqi <= 100) return 'aqi-moderate';
    if (aqi <= 150) return 'aqi-unhealthy';
    return 'aqi-hazardous';
}

function getSmartBatteryClass(battery) {
    if (battery >= 70) return 'battery-high';
    if (battery >= 30) return 'battery-medium';
    return 'battery-low';
}
const { v4: uuidv4 } = require('uuid');

// ------------------------------
// Alerts & Stats Generators
// ------------------------------
function generateSmartAlerts(sensor) {
    const alerts = [];
    
    // AQI alert
    if (sensor.air_quality_index > 100) {
        alerts.push({
            alert_id: uuidv4(),
            sensor_id: sensor.sensor_id,
            timestamp: new Date(),
            alert_type: 'air_quality_alert',
            severity: sensor.air_quality_index > 150 ? 'critical' : 'high',
            message: `AQI is high: ${sensor.air_quality_index}`,
            battery_low: false,
            signal_weak: false
        });
    }

    // Battery alert
    if (sensor.battery_level < 30) {
        alerts.push({
            alert_id: uuidv4(),
            sensor_id: sensor.sensor_id,
            timestamp: new Date(),
            alert_type: 'battery_low',
            severity: 'medium',
            message: `Battery is low: ${sensor.battery_level}%`,
            battery_low: true,
            signal_weak: false
        });
    }

    // Signal alert
    if (sensor.signal_strength < 40) {
        alerts.push({
            alert_id: uuidv4(),
            sensor_id: sensor.sensor_id,
            timestamp: new Date(),
            alert_type: 'signal_weak',
            severity: 'medium',
            message: `Signal is weak: ${sensor.signal_strength}%`,
            battery_low: false,
            signal_weak: true
        });
    }

    return alerts;
}


function computeSmartStats(sensors) {
    const now = new Date();
    const windowStart = new Date(now.getTime() - 5 * 60 * 1000); // last 5 min
    return Object.values(sensors).map(sensor => ({
        sensor_id: sensor.sensor_id,
        window_start: windowStart,
        window_end: now,
        total_readings: 1,
        avg_aqi: sensor.air_quality_index,
        max_aqi: sensor.air_quality_index,
        min_aqi: sensor.air_quality_index,
        avg_pm2_5: sensor.pm2_5,
        max_pm2_5: sensor.pm2_5,
        min_pm2_5: sensor.pm2_5,
        avg_battery: sensor.battery_level,
        avg_signal: sensor.signal_strength
    }));
}

// ------------------------------
// Cassandra Insert Functions
// ------------------------------
async function saveSmartAlerts(alerts) {
    for (const alert of alerts) {
        const query = `
            INSERT INTO smart_sensor_alerts (
                alert_id, sensor_id, timestamp, alert_type, severity, message, battery_low, signal_weak
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `;
        const params = [
            alert.alert_id, alert.sensor_id, alert.timestamp, alert.alert_type,
            alert.severity, alert.message, alert.battery_low, alert.signal_weak
        ];
        await cassandraClient.execute(query, params, { prepare: true });
    }
}

async function saveSmartStats(stats) {
    for (const stat of stats) {
        const query = `
            INSERT INTO smart_sensor_stats (
                sensor_id, window_start, window_end, total_readings,
                avg_aqi, max_aqi, min_aqi,
                avg_pm2_5, max_pm2_5, min_pm2_5,
                avg_battery, avg_signal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `;
        const params = [
            stat.sensor_id, stat.window_start, stat.window_end, stat.total_readings,
            stat.avg_aqi, stat.max_aqi, stat.min_aqi,
            stat.avg_pm2_5, stat.max_pm2_5, stat.min_pm2_5,
            stat.avg_battery, stat.avg_signal
        ];
        await cassandraClient.execute(query, params, { prepare: true });
    }
}

// ------------------------------
// Upsert Smart Sensor
// ------------------------------
async function upsertSmartSensor(data) {
    if (!data.sensor_id) return;

    // Update in-memory
    smartSensorsData[data.sensor_id] = {
        ...smartSensorsData[data.sensor_id],
        ...data,
        timestamp: new Date().toISOString()
    };

    if (!cassandraConnected) return;

    try {
        // Insert sensor
        const query = `
            INSERT INTO smart_virtual_sensors (
                sensor_id, sensor_type, location, category,
                air_quality_index, pm2_5, pm10,
                temperature, humidity, pressure,
                wind_speed, wind_direction,
                battery_level, signal_strength, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `;

        const params = [
            data.sensor_id,
            data.sensor_type || null,
            data.location || null,
            data.category || null,
            data.air_quality_index ?? null,
            data.pm2_5 ?? null,
            data.pm10 ?? null,
            data.temperature ?? null,
            data.humidity ?? null,
            data.pressure ?? null,
            data.wind_speed ?? null,
            data.wind_direction ?? null,
            data.battery_level ?? null,
            data.signal_strength ?? null,
            new Date()
        ];

        await cassandraClient.execute(query, params, { prepare: true });

        // Alerts
        const alerts = generateSmartAlerts(data);
        if (alerts.length) await saveSmartAlerts(alerts);

        // Stats
        const stats = computeSmartStats(smartSensorsData);
        await saveSmartStats(stats);

        console.log(`✅ Sensor, alerts, stats saved: ${data.sensor_id}`);
    } catch (err) {
        console.error('❌ Failed to save sensor data:', err);
    }
}

// ------------------------------
// API Endpoints
// ------------------------------
app.post('/api/smart-sensors/:sensorId', async (req, res) => {
    const sensorData = req.body;
    sensorData.sensor_id = req.params.sensorId;

    try {
        await upsertSmartSensor(sensorData);

        // Broadcast via WebSocket
        wss.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify({ type: 'smart_sensor_update', sensor: sensorData, timestamp: new Date() }));
            }
        });

        res.status(200).json({ message: `Sensor updated: ${sensorData.sensor_id}` });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.get('/api/smart-sensors', (req, res) => {
    res.json(Object.values(smartSensorsData));
});

// Optional: Endpoint to get all smart sensors
app.get('/api/smart-sensors', (req, res) => {
    res.json(Object.values(smartSensorsData));
});


app.get("/api/sensors", async (req, res) => {
  if (!cassandraConnected) {
    return res.status(503).json({ detail: "Cassandra database not connected" });
  }

  try {
    // Get all unique sensor IDs
    const query = "SELECT DISTINCT sensor_id FROM air_quality_data";
    const result = await cassandraClient.execute(query);
    const sensorIds = result.rows.map(row => row.sensor_id);

    const sensorsList = [];

    for (const sensorId of sensorIds) {
      // Get the latest reading to extract location info
      const queryLatest = `
        SELECT location_name, area_type 
        FROM air_quality_data 
        WHERE sensor_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
      `;
      const sensorResult = await cassandraClient.execute(queryLatest, [sensorId], { prepare: true });

      if (sensorResult && sensorResult.rowLength > 0) {
        const row = sensorResult.rows[0];
        let locationName = row.location_name || "Unknown";
        let areaType = row.area_type || "Unknown";

        // Determine sensor type
        let sensorType = "Unknown";
        const sensorIdLower = sensorId.toLowerCase();
        const areaTypeLower = areaType.toLowerCase();

        if (sensorIdLower.includes("urban") || areaTypeLower.includes("urban")) {
          sensorType = "Urban";
          locationName = "City Center";
        } else if (sensorIdLower.includes("industrial") || areaTypeLower.includes("industrial")) {
          sensorType = "Industrial";
          locationName = "Factory Zone";
        } else if (sensorIdLower.includes("residential") || areaTypeLower.includes("residential")) {
          sensorType = "Residential";
          locationName = "Suburban Area";
        } else if (sensorIdLower.includes("bus")) {
          sensorType = "Mobile";
          locationName = "City Bus Route";
        } else if (sensorIdLower.includes("wearable")) {
          sensorType = "Wearable";
          locationName = "Cyclist / Pedestrian";
        } else if (sensorIdLower.includes("drone")) {
          sensorType = "Drone";
          locationName = "Aerial / City Monitoring";
        }

        sensorsList.push({
          id: sensorId,
          type: sensorType,
          location_name: locationName,
          img: `/images/sensor_${sensorType.toLowerCase()}.png`
        });
      }
    }

    res.json({ sensors: sensorsList });

  } catch (err) {
    console.error("❌ Error fetching sensors:", err);
    res.status(500).json({ detail: `Error fetching sensors: ${err.message}` });
  }
});


app.get('/api/stats', async (req, res) => {
    if (!cassandraConnected) {
        return res.status(503).json({ error: 'Database not connected' });
    }

    try {
        // total sensors
        const sensorRows = await cassandraClient.execute('SELECT DISTINCT sensor_id FROM air_quality_data');
        const sensorIds = sensorRows.rows.map(r => r.sensor_id);
        const sensorCount = sensorIds.length;

        // total records
        const totalRecordsRow = await cassandraClient.execute('SELECT COUNT(*) as count FROM air_quality_data');
        const totalRecords = totalRecordsRow.rows[0]?.count?.toString() || "0";

        // active alerts
        const alertsRows = await cassandraClient.execute('SELECT is_active FROM air_quality_alerts');
        const activeAlerts = alertsRows.rows.filter(r => r.is_active === true).length;

        res.json({
            sensorCount,
            totalRecords,
            activeAlerts,
            uptimeSeconds: Math.floor(process.uptime()),
            systemVersion: "2.0.0",
            sensors: sensorIds.map(id => ({ id }))
        });
    } catch (error) {
        console.error('❌ Error in /api/stats:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

const SUPPORTED_ALGORITHMS = ["random-forest", "svm", "kmeans"];

app.get("/api/ml-analysis", async (req, res) => {
  const { sensor, algorithm = "random-forest", hours = 24 } = req.query;
  console.log("📥 Incoming ML request:", { sensor, algorithm, hours });

  if (!sensor) {
    console.warn("⚠️ No sensor parameter provided");
    return res.status(400).json({ error: "Sensor parameter is required" });
  }
  if (!SUPPORTED_ALGORITHMS.includes(algorithm.toLowerCase())) {
    console.warn(`⚠️ Unsupported algorithm requested: ${algorithm}`);
    return res.status(400).json({
      error: `Algorithm '${algorithm}' not supported. Choose from ${SUPPORTED_ALGORITHMS}`
    });
  }

  try {
    // Call the FastAPI ML service
    console.log("🌐 Calling FastAPI ML service...");
    const response = await axios.get("http://localhost:8002/api/ml-analysis", {
      params: { sensor, algorithm, hours }
    });

    console.log("✅ FastAPI ML response received");
    res.json(response.data);
  } catch (err) {
    console.error("🔥 Error calling FastAPI ML service:", err.message);
    if (err.response) {
      console.error("FastAPI status:", err.response.status, "data:", err.response.data);
    }
    res.status(500).json({ error: "Failed to run ML analysis" });
  }
});

app.get("/api/alerts", async (req, res) => {
  const limit = parseInt(req.query.limit) || 10;

  if (!cassandraConnected) {
    return res.status(503).json({ error: "Cassandra database not connected" });
  }

  try {
    // Ensure we have an index on is_active
    // CREATE INDEX IF NOT EXISTS idx_air_quality_alerts_is_active ON air_quality_alerts(is_active);

    // Fetch all active alerts and order by timestamp descending
    const query = `
      SELECT * FROM air_quality_alerts WHERE is_active = true ALLOW FILTERING;`;

    const result = await cassandraClient.execute(query);

    // Sort by timestamp descending and take the last 'limit' alerts
    const sortedAlerts = result.rows
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, limit);

    const alerts = sortedAlerts.map(row => ({
      id: row.alert_id,
      type: row.alert_type,
      severity: row.severity,
      message: row.message,
      sensor_id: row.sensor_id,
      timestamp: row.timestamp ? new Date(row.timestamp).toISOString() : null,
      aqi_level: row.aqi_level || "Unknown",
      status: "active",
    }));

    res.json(alerts);
  } catch (err) {
    console.error("❌ Error fetching alerts:", err);
    res.status(500).json({ error: `Error fetching alerts: ${err.message}` });
  }
});

app.listen(8001, () => {
  console.log("Node.js server running on port 8001");
});


// ------------------------------
// General error logging helper
// ------------------------------
function logError(context, error, extraData = null) {
    console.error(`❌ Error in ${context}:`, error.stack || error.message || error);
    if (extraData) {
        console.error('📦 Additional Data:', JSON.stringify(extraData, null, 2));
    }
}


async function saveAlertToCassandra(alert) {
    if (!cassandraConnected) {
        console.warn('⚠️ Cassandra not connected, cannot save alert:', alert);
        return;
    }
    try {
        console.log('🔔 Attempting to save alert:', alert); // <--- new log
        const query = `
            INSERT INTO air_quality_alerts (
                alert_id, sensor_id, timestamp, alert_type, 
                severity, message, aqi_level, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `;
        const params = [
            alert.alert_id,
            alert.sensor_id,
            alert.timestamp,
            alert.alert_type,
            alert.severity,
            alert.message,
            alert.aqi_level,
            alert.is_active
        ];
        await cassandraClient.execute(query, params, { prepare: true });
        console.log(`✅ Successfully saved alert: ${alert.alert_id}`);
    } catch (error) {
        console.error('❌ Failed to save alert to Cassandra', error);
    }
}

async function checkAirQualityAlerts(data) {
    try {
        const pm2_5 = data.pm2_5 ?? 0;
        const pm10 = data.pm10 ?? 0;
        const aqi = data.aqi ?? 'Unknown';

        let alert = null;

        if (pm2_5 > 55.4 || pm10 > 254) {
            // HIGH
            alert = {
                alert_id: `alert_${Date.now()}_${data.sensor_id}`,
                sensor_id: data.sensor_id,
                timestamp: new Date(),
                alert_type: 'POOR_AIR_QUALITY',
                severity: 'HIGH',
                message: `Poor air quality detected: PM2.5=${pm2_5}, PM10=${pm10}, AQI=${aqi}`,
                aqi_level: aqi.toString(),
                is_active: true
            };
        } else if (pm2_5 > 35.4 || pm10 > 154) {
            // MEDIUM
            alert = {
                alert_id: `alert_${Date.now()}_${data.sensor_id}`,
                sensor_id: data.sensor_id,
                timestamp: new Date(),
                alert_type: 'MODERATE_AIR_QUALITY',
                severity: 'MEDIUM',
                message: `Moderate air quality: PM2.5=${pm2_5}, PM10=${pm10}, AQI=${aqi}`,
                aqi_level: aqi.toString(),
                is_active: true
            };
        } else if (pm2_5 > 12 || pm10 > 54) {
            // LOW
            alert = {
                alert_id: `alert_${Date.now()}_${data.sensor_id}`,
                sensor_id: data.sensor_id,
                timestamp: new Date(),
                alert_type: 'MILD_AIR_QUALITY',
                severity: 'LOW',
                message: `Slightly elevated levels: PM2.5=${pm2_5}, PM10=${pm10}, AQI=${aqi}`,
                aqi_level: aqi.toString(),
                is_active: true
            };
        }

        if (alert) {
            console.log(`⚠️ Triggered alert for sensor ${alert.sensor_id}: ${alert.message}`);

            await saveAlertToCassandra(alert);

            alertBatch.push(alert);

            // Push to WebSocket clients
            wss.clients.forEach(client => {
                if (client.readyState === WebSocket.OPEN) {
                    client.send(JSON.stringify({
                        type: 'alert_update',
                        alert,
                        timestamp: new Date().toISOString()
                    }));
                }
            });

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


let kafkaConsumer = null;

// /api/health endpoint
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        cassandra: cassandraConnected ? 'connected' : 'disconnected',
        kafka: kafkaConsumer ? 'connected' : 'disconnected',
        websocketConnections: wss.clients.size, 
        uptimeSeconds: Math.floor(process.uptime()),
        timestamp: new Date().toISOString(),
        systemVersion: "2.0.0"
    });
});



app.get('/api/sensors/latest', async (req, res) => {
    if (!cassandraConnected) {
        return res.status(503).json({ error: 'Database not connected' });
    }

    try {
        // 1. Get all sensor IDs from the sensors table
        const sensorsQuery = 'SELECT sensor_id FROM air_quality_data';
        const sensorsResult = await cassandraClient.execute(sensorsQuery);
        const sensorIds = sensorsResult.rows.map(r => r.sensor_id);

        // 2. Fetch latest reading for each sensor
        const latestReadings = [];
        for (const sensorId of sensorIds) {
            const readingQuery = `
                SELECT sensor_id, timestamp, location_name, area_type, 
                       pm2_5, pm10, aqi, health_risk, 
                       temperature_celsius, humidity_percent, weather_condition
                FROM air_quality_data
                WHERE sensor_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            `;
            const result = await cassandraClient.execute(readingQuery, [sensorId], { prepare: true });
            if (result.rows.length > 0) {
                latestReadings.push(result.rows[0]);
            }
        }

        res.json(latestReadings);

    } catch (error) {
        console.error('Error fetching latest readings:', error);
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
        const sensorCountQuery = 'SELECT COUNT(*) as count FROM air_quality_data';
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
