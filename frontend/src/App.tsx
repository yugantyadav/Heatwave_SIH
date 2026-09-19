import React from 'react'
import { MapContainer, TileLayer, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function WardMap() {
  const [wards, setWards] = React.useState([])

  React.useEffect(() => {
    axios.get(`${API_BASE}/api/wards`).then(res => setWards(res.data.wards || []))
  }, [])

  const riskColors = { low: '#4CAF50', moderate: '#FFC107', high: '#FF9800', severe: '#F44336' }

  return (
    <MapContainer center={[19.076, 72.877]} zoom={12} style={{ height: '100vh', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {wards.map((w: any) => (
        <React.Fragment key={w.ward_code}>
          <div style={{ position: 'absolute', left: `${19.0 + (parseInt(w.ward_code) - 1) * 0.01}%`, top: '40%', color: riskColors[w.risk_category] || '#333' }}>
            {w.ward_name}
          </div>
        </React.Fragment>
      ))}
    </MapContainer>
  )
}

export default function App() {
  return (
    <div>
      <h1>Heatwave EWS</h1>
      <WardMap />
    </div>
  )
}