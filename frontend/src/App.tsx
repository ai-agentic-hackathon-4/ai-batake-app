import { useState } from 'react'
import './App.css'
import SeedGuide from './components/SeedGuide'

function App() {
    const [view, setView] = useState<'weather' | 'seed'>('seed');

    return (
        <>
            <div>
                <h1>AI Batake App</h1>
                <div style={{ marginBottom: '20px' }}>
                    <button onClick={() => setView('weather')} style={{ marginRight: '10px' }}>Weather Check</button>
                    <button onClick={() => setView('seed')}>Seed Guide (New)</button>
                </div>
            </div>

            {view === 'seed' && <SeedGuide />}

            {view === 'weather' && (
                <div className="card">
                    <h2>Weather Check</h2>
                    <p>Simple Weather Checker (ported from index.html)</p>
                    {/* Porting text logic if needed, but for now simple placeholder */}
                    <iframe
                        src="/legacy_weather_placeholder.html"
                        style={{ width: '100%', height: '300px', border: 'none' }}
                        title="weather"
                    />
                </div>
            )}
        </>
    )
}

export default App
