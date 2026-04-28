import React, { useState, useEffect, useRef } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import {
  StyleSheet, Text, View, ScrollView, TouchableOpacity, Platform,
  Image, Switch, Modal, FlatList, Dimensions
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Speech from 'expo-speech';
import * as Location from 'expo-location';
import Voice from '@react-native-voice/voice';
import { getTheme, getThemeNames, THEMES } from './themes';
import { Ionicons } from '@expo/vector-icons';
import MapView, { Marker, UrlTile } from 'react-native-maps';

const Tab = createBottomTabNavigator();
const { width, height } = Dimensions.get('window');

// BACKEND URL
// ---------------------------------------------------------
// 🔧 BACKEND CONFIGURATION
// ---------------------------------------------------------
// IMPORTANT: Choose the appropriate backend URL based on your environment
//
// 1. FOR LOCAL TESTING: 
//    Uncomment the line below and use your computer's IP address
//    Find your IP: Windows (ipconfig), Mac/Linux (ifconfig)
//    const BACKEND_URL = 'http://192.168.68.106:8000'; 
//
// 2. FOR PRODUCTION DEPLOYMENT (Hugging Face): 
//    This is your deployed backend URL on Hugging Face Spaces
//    ✅ CURRENTLY ACTIVE - Ready for EAS build and deployment
const BACKEND_URL = 'https://fragliglint-shohochor-back.hf.space';
//
// 3. ALTERNATIVE: Use app.config.js (Advanced)
//    If you've set up app.config.js, you can use:
//    import Constants from 'expo-constants';
//    const BACKEND_URL = Constants.expoConfig.extra.backendUrl;
//
// ---------------------------------------------------------

// Main App Component
export default function App() {
  const [currentTheme, setCurrentTheme] = useState('cyber_nexus');
  const [settings, setSettings] = useState({
    language: 'en',
    voiceEnabled: true,
    ocrEnabled: true,
    emergencyMode: true,
    autoDetection: true,
    confidence: 0.25,
    alertFrequency: 3,
  });

  const theme = getTheme(currentTheme);

  return (
    <NavigationContainer>
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <Tab.Navigator
          screenOptions={{
            tabBarStyle: {
              backgroundColor: theme.cardBg,
              borderTopColor: theme.primary,
              borderTopWidth: 2,
              height: 70,
              paddingBottom: 10,
            },
            tabBarActiveTintColor: theme.primary,
            tabBarInactiveTintColor: theme.textSecondary,
            headerStyle: {
              backgroundColor: theme.cardBg,
            },
            headerTintColor: theme.text,
            headerTitleStyle: {
              fontWeight: 'bold',
              fontSize: 20,
            },
          }}
        >
          <Tab.Screen
            name="Camera"
            options={{
              tabBarLabel: 'Live',
              title: '🔴 Live Detection',
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="camera" size={size} color={color} />
              )
            }}
          >
            {props => <CameraScreen {...props} theme={theme} settings={settings} />}
          </Tab.Screen>

          <Tab.Screen
            name="Analytics"
            options={{
              tabBarLabel: 'Stats',
              title: '📊 Analytics',
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="stats-chart" size={size} color={color} />
              )
            }}
          >
            {props => <AnalyticsScreen {...props} theme={theme} />}
          </Tab.Screen>

          <Tab.Screen
            name="Map"
            options={{
              tabBarLabel: 'Map',
              title: '🗺️ Detection Map',
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="map" size={size} color={color} />
              )
            }}
          >
            {props => <MapScreen {...props} theme={theme} />}
          </Tab.Screen>

          <Tab.Screen
            name="History"
            options={{
              tabBarLabel: 'History',
              title: '📋 History',
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="list" size={size} color={color} />
              )
            }}
          >
            {props => <HistoryScreen {...props} theme={theme} />}
          </Tab.Screen>

          <Tab.Screen
            name="Settings"
            options={{
              tabBarLabel: 'Settings',
              title: '⚙️ Settings',
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="settings" size={size} color={color} />
              )
            }}
          >
            {props => (
              <SettingsScreen
                {...props}
                theme={theme}
                currentTheme={currentTheme}
                setCurrentTheme={setCurrentTheme}
                settings={settings}
                setSettings={setSettings}
              />
            )}
          </Tab.Screen>
        </Tab.Navigator>
      </View>
    </NavigationContainer>
  );
}

// Camera Screen Component
function CameraScreen({ theme, settings }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [detections, setDetections] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [alertText, setAlertText] = useState('Welcome to SHOHOCHOR!');
  const [stats, setStats] = useState({ objects: 0, critical: 0, fps: 0 });
  const [connectionStatus, setConnectionStatus] = useState('connected'); // connected, error
  const [alertsPaused, setAlertsPaused] = useState(false);
  const cameraRef = useRef(null);
  const lastSpeechTime = useRef(0);
  const alertResumeTimer = useRef(null);
  const [location, setLocation] = useState(null);

  // Ref to track latest settings in closures (setInterval, event listeners)
  const settingsRef = useRef(settings);
  useEffect(() => {
    settingsRef.current = settings;
  }, [settings]);

  useEffect(() => {
    (async () => {
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status === 'granted') {
        let loc = await Location.getCurrentPositionAsync({});
        setLocation(loc.coords);
      }
    })();
  }, []);

  // Voice recognition setup
  useEffect(() => {
    startContinuousListening();

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
      if (alertResumeTimer.current) {
        clearTimeout(alertResumeTimer.current);
      }
    };
  }, []);

  const startContinuousListening = async () => {
    try {
      Voice.onSpeechResults = handleSpeechResults;
      Voice.onSpeechError = (e) => {
        console.log('Voice error:', e);
        setTimeout(() => Voice.start('en-US'), 1000);
      };
      Voice.onSpeechEnd = () => {
        setTimeout(() => Voice.start('en-US'), 500);
      };

      await Voice.start('en-US');
    } catch (error) {
      console.log('Failed to start voice:', error);
    }
  };

  const handleSpeechResults = async (e) => {
    if (!e.value || e.value.length === 0) return;

    const spokenText = e.value[0].toLowerCase();
    console.log('Heard:', spokenText);

    // Check for location query wake phrases
    const locationQueries = [
      'hey shohochor where am i',
      'shohochor where am i',
      'hey shohochor ami ekhon kothay',
      'shohochor ami ekhon kothay',
      'hey shohochor ami kothay',
      'shohochor ami kothay'
    ];

    const isLocationQuery = locationQueries.some(query =>
      spokenText.includes(query)
    );

    if (isLocationQuery) {
      await handleLocationQuery();
    }
  };

  const handleLocationQuery = async () => {
    // 1. PAUSE ALERTS IMMEDIATELY
    setAlertsPaused(true);
    Speech.stop(); // Stop any ongoing alert speech

    // 2. SPEAK LOCATION
    await speakLocation();

    // 3. AUTO-RESUME ALERTS AFTER 5 SECONDS
    if (alertResumeTimer.current) {
      clearTimeout(alertResumeTimer.current);
    }
    alertResumeTimer.current = setTimeout(() => {
      setAlertsPaused(false);
      console.log('Alerts resumed');
    }, 5000); // 5 seconds
  };

  const speakLocation = async () => {
    const currentSettings = settingsRef.current;
    if (!location) {
      const noLocationMsg = currentSettings.language === 'bn'
        ? 'অবস্থান উপলব্ধ নেই'
        : 'Location not available';
      Speech.speak(noLocationMsg, {
        language: currentSettings.language === 'bn' ? 'bn' : 'en',
        rate: 0.8
      });
      return;
    }

    try {
      const langParam = currentSettings.language === 'bn' ? 'bn' : 'en';
      const response = await fetch(
        `${BACKEND_URL}/location/address?lat=${location.latitude}&lon=${location.longitude}&lang=${langParam}`
      );
      const data = await response.json();

      // Build location text
      let locationText;
      if (currentSettings.language === 'bn') {
        locationText = `আপনি আছেন ${data.address}`;
      } else {
        locationText = `You are at ${data.address}`;
      }

      // Speak with correct language
      Speech.speak(locationText, {
        language: currentSettings.language === 'bn' ? 'bn' : 'en',
        rate: 0.8,
        pitch: 1.0
      });

      console.log('Location spoken:', locationText);
    } catch (error) {
      console.error('Location fetch error:', error);

      // Fallback to coordinates
      const fallbackMsg = currentSettings.language === 'bn'
        ? `অক্ষাংশ ${location.latitude.toFixed(4)}, দ্রাঘিমাংশ ${location.longitude.toFixed(4)}`
        : `Latitude ${location.latitude.toFixed(4)}, Longitude ${location.longitude.toFixed(4)}`;

      Speech.speak(fallbackMsg, {
        language: currentSettings.language === 'bn' ? 'bn' : 'en',
        rate: 0.8
      });
    }
  };

  useEffect(() => {
    if (!settings.autoDetection) return;

    const interval = setInterval(() => {
      if (!isProcessing && cameraRef.current) {
        takePictureAndInfer();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isProcessing, settings.autoDetection]);

  const takePictureAndInfer = async () => {
    if (cameraRef.current) {
      setIsProcessing(true);
      const startTime = Date.now();
      const currentSettings = settingsRef.current;

      try {
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.5,
          base64: false,
        });

        // Send to backend
        const formData = new FormData();
        formData.append('file', {
          uri: Platform.OS === 'android' ? photo.uri : photo.uri.replace('file://', ''),
          type: 'image/jpeg',
          name: 'frame.jpg',
        });
        formData.append('conf', currentSettings.confidence.toString());
        formData.append('lang', currentSettings.language); // Send selected language to backend

        console.log('[API] Sending detection request with lang:', currentSettings.language);

        const response = await fetch(`${BACKEND_URL}/infer/frame`, {
          method: 'POST',
          body: formData,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        if (response.ok) {
          setConnectionStatus('connected');
          const data = await response.json();

          // Normalize detections for display
          const normalizedDetections = data.detections.map(d => ({
            ...d,
            normalizedBox: {
              left: d.box_xyxy[0] / photo.width,
              top: d.box_xyxy[1] / photo.height,
              width: (d.box_xyxy[2] - d.box_xyxy[0]) / photo.width,
              height: (d.box_xyxy[3] - d.box_xyxy[1]) / photo.height,
            }
          }));

          setDetections(normalizedDetections);
          // Ensure we always have text, fallback to "Scanning..." if empty
          const newAlertText = data.alert_text || 'Scanning area...';
          console.log('[API] Received alert text:', newAlertText);
          console.log('[API] Language was:', currentSettings.language);
          setAlertText(newAlertText);

          const criticalCount = data.detections?.filter(d =>
            ['fire', 'knife', 'gun', 'car', 'bus', 'truck'].some(c =>
              d.class_name.toLowerCase().includes(c)
            )
          ).length || 0;

          const fps = Math.round(1000 / (Date.now() - startTime));
          setStats({
            objects: data.detections?.length || 0,
            critical: criticalCount,
            fps: fps
          });

          // TTS Logic
          if (currentSettings.voiceEnabled && newAlertText &&
            !alertsPaused &&  // Respect pause state
            Date.now() - lastSpeechTime.current > (currentSettings.alertFrequency * 1000)) {

            // Fix: Use proper language locale codes
            const ttsLanguage = currentSettings.language === 'bn' ? 'bn-BD' : 'en-US';
            console.log('[TTS] Speaking:', ttsLanguage, newAlertText);

            Speech.speak(newAlertText, {
              language: ttsLanguage,  // Use proper locale
              pitch: 1.0,
              rate: 0.9,
            });
            lastSpeechTime.current = Date.now();
          }
        } else {
          setConnectionStatus('error');
          console.log('Server returned error:', response.status);
        }
      } catch (error) {
        setConnectionStatus('error');
        console.log('Inference error:', error);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  if (!permission) {
    return <View style={[styles.container, { backgroundColor: theme.background }]} />;
  }

  if (!permission.granted) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background, justifyContent: 'center', padding: 20 }]}>
        <Text style={[styles.text, { color: theme.text, textAlign: 'center', marginBottom: 20 }]}>
          We need camera permission for object detection
        </Text>
        <TouchableOpacity
          onPress={requestPermission}
          style={[styles.button, { backgroundColor: theme.primary }]}
        >
          <Text style={[styles.buttonText, { color: '#fff' }]}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.flex1}>
      <CameraView
        style={styles.flex1}
        facing="back"
        ref={cameraRef}
      >
        {/* Logo Header */}
        <View style={styles.logoContainer}>
          <Image
            source={require('./assets/logo.png')}
            style={styles.logo}
            resizeMode="contain"
          />
        </View>

        {/* Connection Error Banner */}
        {connectionStatus === 'error' && (
          <View style={[styles.alertBanner, { backgroundColor: theme.error, top: 100 }]}>
            <Text style={[styles.alertText, { color: '#fff' }]}>
              ⚠️ Connection Error! Check Backend.
            </Text>
          </View>
        )}

        {/* Stats Bar */}
        <View style={[styles.statsBar, { backgroundColor: theme.cardBg }]}>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: theme.primary }]}>{stats.objects}</Text>
            <Text style={[styles.statLabel, { color: theme.textSecondary }]}>Objects</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: theme.error }]}>{stats.critical}</Text>
            <Text style={[styles.statLabel, { color: theme.textSecondary }]}>Critical</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: theme.success }]}>{stats.fps}</Text>
            <Text style={[styles.statLabel, { color: theme.textSecondary }]}>FPS</Text>
          </View>
        </View>

        {/* Detection Overlay */}
        <View style={StyleSheet.absoluteFill}>
          {detections.map((det, index) => (
            <View
              key={index}
              style={{
                position: 'absolute',
                left: `${det.normalizedBox.left * 100}%`,
                top: `${det.normalizedBox.top * 100}%`,
                width: `${det.normalizedBox.width * 100}%`,
                height: `${det.normalizedBox.height * 100}%`,
                borderWidth: 2,
                borderColor: det.critical ? theme.error : theme.success,
                zIndex: 10,
              }}
            >
              <View style={{
                backgroundColor: det.critical ? theme.error : theme.success,
                alignSelf: 'flex-start',
                paddingHorizontal: 4,
                paddingVertical: 2,
              }}>
                <Text style={{
                  color: '#fff',
                  fontSize: 12,
                  fontWeight: 'bold'
                }}>
                  {det.class_name} {Math.round(det.confidence * 100)}%
                </Text>
              </View>
            </View>
          ))}
        </View>

        {/* Alert Banner */}
        {alertText ? (
          <View style={[styles.alertBanner, { backgroundColor: theme.error + 'CC' }]}>
            <Text style={[styles.alertText, { color: theme.text }]}>🔊 {alertText}</Text>
          </View>
        ) : null}

        {/* Controls */}
        <View style={[styles.controls, { backgroundColor: theme.cardBg }]}>
          <TouchableOpacity
            onPress={() => settings.voiceEnabled && Speech.speak(alertText || 'No alerts', { language: settings.language })}
            style={[styles.controlButton, { backgroundColor: theme.primary }]}
          >
            <Text style={styles.controlButtonText}>🔊</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={takePictureAndInfer}
            style={[styles.controlButton, { backgroundColor: theme.secondary, width: 80, height: 80 }]}
            disabled={isProcessing}
          >
            <Text style={[styles.controlButtonText, { fontSize: 32 }]}>
              {isProcessing ? '⏳' : '📸'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => setAlertText('')}
            style={[styles.controlButton, { backgroundColor: theme.accent }]}
          >
            <Text style={styles.controlButtonText}>🔇</Text>
          </TouchableOpacity>
        </View>
      </CameraView>
    </View>
  );
}

// Analytics Screen Component
function AnalyticsScreen({ theme }) {
  const [sessionData, setSessionData] = useState(null);

  useEffect(() => {
    // Fetch analytics data from backend
    fetch(`${BACKEND_URL}/`)
      .then(res => res.json())
      .then(data => {
        setSessionData(data);
      })
      .catch(err => console.log('Analytics fetch error:', err));
  }, []);

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.padding20}>
        <Text style={[styles.title, { color: theme.text }]}>📊 Analytics Dashboard</Text>

        {/* Metrics Grid */}
        <View style={styles.metricsGrid}>
          <MetricCard title="Session Time" value="12m 34s" icon="⏱️" theme={theme} />
          <MetricCard title="Total Objects" value="156" icon="🔍" theme={theme} />
          <MetricCard title="Critical Alerts" value="8" icon="⚠️" theme={theme} />
          <MetricCard title="Locations" value="23" icon="📍" theme={theme} />
        </View>

        {/* Charts Placeholder */}
        <View style={[styles.card, { backgroundColor: theme.cardBg, marginTop: 20 }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>📈 Detection Timeline</Text>
          <Text style={[styles.cardText, { color: theme.textSecondary }]}>
            Chart visualization would go here
          </Text>
        </View>

        <View style={[styles.card, { backgroundColor: theme.cardBg, marginTop: 20 }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>📊 Object Frequency</Text>
          <Text style={[styles.cardText, { color: theme.textSecondary }]}>
            Bar chart visualization would go here
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

// Map Screen Component
function MapScreen({ theme }) {
  const [location, setLocation] = useState(null);
  const [detections, setDetections] = useState([]);
  const [mapError, setMapError] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        let { status } = await Location.requestForegroundPermissionsAsync();
        if (status === 'granted') {
          let loc = await Location.getCurrentPositionAsync({});
          setLocation({
            latitude: loc.coords.latitude,
            longitude: loc.coords.longitude,
            latitudeDelta: 0.01,
            longitudeDelta: 0.01,
          });

          // Mock detection locations around current location for demo
          const mockDetections = Array.from({ length: 5 }, (_, i) => ({
            id: i,
            latitude: loc.coords.latitude + (Math.random() - 0.5) * 0.008,
            longitude: loc.coords.longitude + (Math.random() - 0.5) * 0.008,
            critical: Math.random() > 0.7,
            type: ['person', 'car', 'bicycle', 'obstacle'][Math.floor(Math.random() * 4)],
          }));
          setDetections(mockDetections);
        }
      } catch (error) {
        console.log('Location error:', error);
        setMapError(true);
      }
    })();
  }, []);

  // Dark map style for better visibility
  const mapDarkStyle = [
    { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
    { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
    { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
    {
      featureType: "road",
      elementType: "geometry",
      stylers: [{ color: "#38414e" }],
    },
    {
      featureType: "road",
      elementType: "geometry.stroke",
      stylers: [{ color: "#212a37" }],
    },
    {
      featureType: "water",
      elementType: "geometry",
      stylers: [{ color: "#17263c" }],
    },
  ];

  // If map crashes, show error instead of crashing app
  if (mapError) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background, justifyContent: 'center', padding: 20 }]}>
        <Text style={[styles.title, { color: theme.text, textAlign: 'center' }]}>🗺️ Map View</Text>
        <View style={[styles.card, { backgroundColor: theme.cardBg, marginTop: 20 }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>⚠️ Map Configuration Needed</Text>
          <Text style={[styles.cardText, { color: theme.textSecondary }]}>
            The map requires a Google Maps API key to be configured.{'\n\n'}
            Please add a Google Maps API key in app.json under android.config.googleMaps.apiKey
          </Text>
        </View>
        {location && (
          <View style={[styles.card, { backgroundColor: theme.cardBg, marginTop: 15 }]}>
            <Text style={[styles.cardTitle, { color: theme.text }]}>📍 Your Location</Text>
            <Text style={[styles.cardText, { color: theme.textSecondary }]}>
              Lat: {location.latitude.toFixed(6)}{'\n'}
              Lon: {location.longitude.toFixed(6)}
            </Text>
          </View>
        )}
      </View>
    );
  }

  return (
    <View style={styles.flex1}>
      {location ? (
        <MapView
          provider={null}
          style={styles.flex1}
          initialRegion={location}
          mapType={Platform.OS == "android" ? "none" : "standard"}
          showsUserLocation={true}
          showsMyLocationButton={true}
          onError={() => setMapError(true)}
        >
          {/* OpenStreetMap Tiles */}
          <UrlTile
            urlTemplate="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            maximumZ={19}
            flipY={false}
          />

          {/* User location marker (Custom UI on top of map) */}
          <Marker
            coordinate={{ latitude: location.latitude, longitude: location.longitude }}
            title="Your Location"
            description="Current position"
            pinColor={theme.primary}
          >
            <View style={{
              backgroundColor: theme.primary,
              padding: 8,
              borderRadius: 20,
              borderWidth: 3,
              borderColor: '#fff',
            }}>
              <Ionicons name="person" size={20} color="#fff" />
            </View>
          </Marker>

          {/* Detection markers */}
          {detections.map(det => (
            <Marker
              key={det.id}
              coordinate={{ latitude: det.latitude, longitude: det.longitude }}
              title={det.critical ? `⚠️ ${det.type}` : det.type}
              description={det.critical ? "Critical object detected" : "Object detected"}
            >
              <View style={{
                backgroundColor: det.critical ? theme.error : theme.success,
                padding: 6,
                borderRadius: 15,
                borderWidth: 2,
                borderColor: '#fff',
              }}>
                <Ionicons
                  name={det.critical ? "warning" : "checkmark-circle"}
                  size={16}
                  color="#fff"
                />
              </View>
            </Marker>
          ))}
        </MapView>
      ) : (
        <View style={[styles.container, { backgroundColor: theme.background, justifyContent: 'center' }]}>
          <Text style={[styles.text, { color: theme.text }]}>Loading map...</Text>
          <Text style={[styles.cardText, { color: theme.textSecondary, marginTop: 10, textAlign: 'center' }]}>
            Requesting location permissions...
          </Text>
        </View>
      )}
    </View>
  );
}

// History Screen Component
function HistoryScreen({ theme }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    // Mock history data
    const mockHistory = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      timestamp: new Date(Date.now() - i * 60000).toLocaleTimeString(),
      objects: Math.floor(Math.random() * 10) + 1,
      critical: Math.floor(Math.random() * 3),
      alert: `Detection ${i + 1} - ${Math.random() > 0.5 ? 'Clear path' : 'Objects detected'}`,
    }));
    setHistory(mockHistory);
  }, []);

  const renderHistoryItem = ({ item }) => (
    <View style={[styles.card, { backgroundColor: theme.cardBg, marginBottom: 10 }]}>
      <View style={styles.historyHeader}>
        <Text style={[styles.historyTime, { color: theme.primary }]}>🕐 {item.timestamp}</Text>
        <View style={styles.historyBadges}>
          <Text style={[styles.badge, { backgroundColor: theme.success + '40', color: theme.success }]}>
            {item.objects} obj
          </Text>
          {item.critical > 0 && (
            <Text style={[styles.badge, { backgroundColor: theme.error + '40', color: theme.error }]}>
              {item.critical} ⚠️
            </Text>
          )}
        </View>
      </View>
      <Text style={[styles.historyAlert, { color: theme.textSecondary }]}>{item.alert}</Text>

      <View style={styles.historyActions}>
        <TouchableOpacity style={[styles.smallButton, { backgroundColor: theme.success + '40' }]}>
          <Text style={[styles.smallButtonText, { color: theme.success }]}>👍 Correct</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.smallButton, { backgroundColor: theme.error + '40' }]}>
          <Text style={[styles.smallButtonText, { color: theme.error }]}>👎 Wrong</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <FlatList
        data={history}
        renderItem={renderHistoryItem}
        keyExtractor={item => item.id.toString()}
        contentContainerStyle={styles.padding20}
      />
    </View>
  );
}

// Settings Screen Component
function SettingsScreen({ theme, currentTheme, setCurrentTheme, settings, setSettings }) {
  const [showThemeModal, setShowThemeModal] = useState(false);

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.padding20}>
        <Text style={[styles.title, { color: theme.text }]}>⚙️ Settings</Text>

        {/* Theme Selection */}
        <View style={[styles.card, { backgroundColor: theme.cardBg }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>🎨 Theme</Text>
          <TouchableOpacity
            onPress={() => setShowThemeModal(true)}
            style={[styles.themeButton, { backgroundColor: theme.primary }]}
          >
            <Text style={[styles.buttonText, { color: '#fff' }]}>
              {THEMES[currentTheme].name}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Voice & Language Settings */}
        <View style={[styles.card, { backgroundColor: theme.cardBg }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>🔊 Voice & Language</Text>

          <View style={styles.settingRow}>
            <Text style={[styles.settingLabel, { color: theme.textSecondary }]}>Enable Voice Alerts</Text>
            <Switch
              value={settings.voiceEnabled}
              onValueChange={(val) => setSettings({ ...settings, voiceEnabled: val })}
              trackColor={{ false: theme.textSecondary, true: theme.primary }}
            />
          </View>

          <View style={styles.settingRow}>
            <TouchableOpacity
              onPress={() => Speech.speak("This is a test of the voice system.", { language: settings.language })}
              style={[styles.button, { backgroundColor: theme.secondary, padding: 10, borderRadius: 8 }]}
            >
              <Text style={{ color: '#fff', fontWeight: 'bold' }}>Test Voice 🔊</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.settingRow}>
            <Text style={[styles.settingLabel, { color: theme.textSecondary }]}>Language</Text>
            <View style={styles.languageButtons}>
              <TouchableOpacity
                onPress={() => setSettings({ ...settings, language: 'en' })}
                style={[styles.langButton, {
                  backgroundColor: settings.language === 'en' ? theme.primary : theme.cardBg,
                  borderColor: theme.primary
                }]}
              >
                <Text style={[styles.langButtonText, { color: theme.text }]}>English</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => setSettings({ ...settings, language: 'bn' })}
                style={[styles.langButton, {
                  backgroundColor: settings.language === 'bn' ? theme.primary : theme.cardBg,
                  borderColor: theme.primary
                }]}
              >
                <Text style={[styles.langButtonText, { color: theme.text }]}>বাংলা</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Detection Settings */}
        <View style={[styles.card, { backgroundColor: theme.cardBg }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>🎯 Detection</Text>

          <View style={styles.settingRow}>
            <Text style={[styles.settingLabel, { color: theme.textSecondary }]}>Auto Detection</Text>
            <Switch
              value={settings.autoDetection}
              onValueChange={(val) => setSettings({ ...settings, autoDetection: val })}
              trackColor={{ false: theme.textSecondary, true: theme.primary }}
            />
          </View>

          <View style={styles.settingRow}>
            <Text style={[styles.settingLabel, { color: theme.textSecondary }]}>OCR Text Reading</Text>
            <Switch
              value={settings.ocrEnabled}
              onValueChange={(val) => setSettings({ ...settings, ocrEnabled: val })}
              trackColor={{ false: theme.textSecondary, true: theme.primary }}
            />
          </View>

          <View style={styles.settingRow}>
            <Text style={[styles.settingLabel, { color: theme.textSecondary }]}>Emergency Protocols</Text>
            <Switch
              value={settings.emergencyMode}
              onValueChange={(val) => setSettings({ ...settings, emergencyMode: val })}
              trackColor={{ false: theme.textSecondary, true: theme.primary }}
            />
          </View>

          <View style={styles.settingRow}>
            <Text style={[styles.settingLabel, { color: theme.textSecondary }]}>
              Confidence: {(settings.confidence * 100).toFixed(0)}%
            </Text>
          </View>

          <View style={styles.settingRow}>
            <Text style={[styles.settingLabel, { color: theme.textSecondary }]}>
              Alert Frequency: {settings.alertFrequency}s
            </Text>
          </View>
        </View>

        {/* Platform Info */}
        <View style={[styles.card, { backgroundColor: theme.cardBg }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>📱 Platform Info</Text>
          <Text style={[styles.cardText, { color: theme.textSecondary }]}>
            Platform: {Platform.OS}{'\n'}
            {Platform.OS === 'web' && '📱 For full features, use Expo Go on your phone!'}
          </Text>
        </View>

        {/* About */}
        <View style={[styles.card, { backgroundColor: theme.cardBg }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>ℹ️ About</Text>
          <Text style={[styles.cardText, { color: theme.textSecondary }]}>
            SHOHOCHOR - AI-Powered Mobility Assistant{'\n'}
            Version 2.0{'\n\n'}
            Features:{'\n'}
            • Real-time Object Detection{'\n'}
            • Voice Guidance in Multiple Languages{'\n'}
            • Live Location & Mapping{'\n'}
            • Analytics Dashboard{'\n'}
            • 8 Premium Themes
          </Text>
        </View>
      </View>

      {/* Theme Selection Modal */}
      <Modal
        visible={showThemeModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowThemeModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: theme.cardBg }]}>
            <Text style={[styles.modalTitle, { color: theme.text }]}>Choose Theme</Text>
            <ScrollView style={styles.themeList}>
              {getThemeNames().map(themeName => (
                <TouchableOpacity
                  key={themeName}
                  onPress={() => {
                    setCurrentTheme(themeName);
                    setShowThemeModal(false);
                  }}
                  style={[styles.themeItem, {
                    backgroundColor: currentTheme === themeName ? theme.primary + '40' : 'transparent',
                    borderColor: THEMES[themeName].primary
                  }]}
                >
                  <View style={[styles.themeColorPreview, { backgroundColor: THEMES[themeName].primary }]} />
                  <Text style={[styles.themeItemText, { color: theme.text }]}>
                    {THEMES[themeName].name}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
            <TouchableOpacity
              onPress={() => setShowThemeModal(false)}
              style={[styles.closeButton, { backgroundColor: theme.error }]}
            >
              <Text style={[styles.buttonText, { color: '#fff' }]}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

// Helper Component: Metric Card
function MetricCard({ title, value, icon, theme }) {
  return (
    <View style={[styles.metricCard, { backgroundColor: theme.cardBg }]}>
      <Text style={[styles.metricIcon, { color: theme.primary }]}>{icon}</Text>
      <Text style={[styles.metricValue, { color: theme.text }]}>{value}</Text>
      <Text style={[styles.metricTitle, { color: theme.textSecondary }]}>{title}</Text>
    </View>
  );
}

// Dark Map Style
const mapDarkStyle = [
  { elementType: "geometry", stylers: [{ color: "#212121" }] },
  { elementType: "labels.icon", stylers: [{ visibility: "off" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#757575" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#212121" }] },
];

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  flex1: {
    flex: 1,
  },
  padding20: {
    padding: 20,
  },
  logoContainer: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    alignItems: 'center',
    zIndex: 10,
  },
  logo: {
    width: 150,
    height: 50,
  },
  statsBar: {
    position: 'absolute',
    top: 120,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 15,
    borderRadius: 15,
    zIndex: 10,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  statLabel: {
    fontSize: 12,
    marginTop: 5,
  },
  detectionOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  detectionBox: {
    padding: 10,
    margin: 5,
    borderRadius: 10,
  },
  detectionText: {
    fontWeight: 'bold',
    fontSize: 16,
  },
  alertBanner: {
    position: 'absolute',
    bottom: 150,
    left: 20,
    right: 20,
    padding: 20,
    borderRadius: 15,
    zIndex: 10,
  },
  alertText: {
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  controls: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: 20,
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
  },
  controlButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  controlButtonText: {
    fontSize: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  text: {
    fontSize: 16,
  },
  button: {
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    width: '48%',
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
    marginBottom: 15,
  },
  metricIcon: {
    fontSize: 32,
    marginBottom: 10,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  metricTitle: {
    fontSize: 12,
    textAlign: 'center',
  },
  card: {
    padding: 20,
    borderRadius: 15,
    marginBottom: 15,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  cardText: {
    fontSize: 14,
    lineHeight: 22,
  },
  markerDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  historyTime: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  historyBadges: {
    flexDirection: 'row',
    gap: 5,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    fontSize: 12,
    fontWeight: 'bold',
  },
  historyAlert: {
    fontSize: 14,
    marginBottom: 15,
  },
  historyActions: {
    flexDirection: 'row',
    gap: 10,
  },
  smallButton: {
    flex: 1,
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  smallButtonText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  settingLabel: {
    fontSize: 14,
  },
  languageButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  langButton: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 2,
  },
  langButtonText: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  themeButton: {
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    borderRadius: 20,
    padding: 20,
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  themeList: {
    maxHeight: 400,
  },
  themeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 2,
  },
  themeColorPreview: {
    width: 30,
    height: 30,
    borderRadius: 15,
    marginRight: 15,
  },
  themeItemText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  closeButton: {
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 20,
  },
});
