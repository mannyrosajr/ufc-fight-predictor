import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Pie Chart Component
const PieChart = ({ prediction }) => {
  if (!prediction || !prediction.Confidence) return null;
  const confidenceValue = parseFloat(prediction.Confidence.replace('%', ''));
  const winnerIsRed = prediction.PredictedWinner === prediction.RedFighter;
  const redPercent = winnerIsRed ? confidenceValue : 100 - confidenceValue;
  const bluePercent = 100 - redPercent;
  const chartStyle = { background: `conic-gradient(#d9534f ${redPercent}%, #428bca 0)` };
  return (
    <div className="chart-container">
      <div className="pie-chart" style={chartStyle}></div>
      <div className="legend">
        <div className="legend-item"><span className="legend-color red"></span><span>{prediction.RedFighter}: {redPercent.toFixed(2)}%</span></div>
        <div className="legend-item"><span className="legend-color blue"></span><span>{prediction.BlueFighter}: {bluePercent.toFixed(2)}%</span></div>
      </div>
    </div>
  );
};

// Searchable Dropdown Component
const SearchableDropdown = ({ options, selectedValue, setSelectedValue, label }) => {
  const [inputValue, setInputValue] = useState(selectedValue || '');
  const [filteredOptions, setFilteredOptions] = useState([]);
  const [isDropdownVisible, setIsDropdownVisible] = useState(false);
  const wrapperRef = useRef(null);
  useEffect(() => { setInputValue(selectedValue); }, [selectedValue]);
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) { setIsDropdownVisible(false); }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => { document.removeEventListener("mousedown", handleClickOutside); };
  }, [wrapperRef]);
  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);
    if (value) {
      const lowercasedValue = value.toLowerCase();
      setFilteredOptions(options.filter(option => option.toLowerCase().includes(lowercasedValue)));
      setIsDropdownVisible(true);
    } else { setFilteredOptions([]); setIsDropdownVisible(false); }
  };
  const handleOptionClick = (option) => { setSelectedValue(option); setInputValue(option); setIsDropdownVisible(false); };
  return (
    <div className="fighter-selector" ref={wrapperRef}>
      <label htmlFor={label}>{label}</label>
      <input id={label} type="text" value={inputValue} onChange={handleInputChange} onClick={() => setIsDropdownVisible(true)} placeholder="Type to search..." />
      {isDropdownVisible && (
        <ul className="dropdown-list">
          {filteredOptions.length > 0 ? filteredOptions.map((option, index) => (
            <li key={index} onClick={() => handleOptionClick(option)}>{option}</li>
          )) : <li className="no-results">No matches found</li>}
        </ul>
      )}
    </div>
  );
};

function App() {
  const [allFighters, setAllFighters] = useState([]);
  const [filteredFighters, setFilteredFighters] = useState([]);
  const [weightClasses, setWeightClasses] = useState({});
  const [selectedWeightClass, setSelectedWeightClass] = useState('All');
  const [redFighter, setRedFighter] = useState('');
  const [blueFighter, setBlueFighter] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [modelWeights, setModelWeights] = useState([]);
  const [showWeights, setShowWeights] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch('/fighters.json').then(res => res.json()),
      fetch('http://localhost:8000/weightclasses').then(res => res.json())
    ]).then(([fightersData, wcData]) => {
      setAllFighters(fightersData);
      setFilteredFighters(fightersData);
      setWeightClasses(wcData);
      if (fightersData.length > 1) {
        setRedFighter(fightersData.find(f => f === 'Jon Jones') || fightersData[0]);
        setBlueFighter(fightersData.find(f => f === 'Stipe Miocic') || fightersData[1]);
      }
    }).catch(error => console.error('Error fetching initial data:', error));
  }, []);

  useEffect(() => {
    if (selectedWeightClass === 'All') { setFilteredFighters(allFighters); }
    else {
      const fightersInClass = weightClasses[selectedWeightClass] || [];
      setFilteredFighters(fightersInClass);
      if (fightersInClass.length > 1) { setRedFighter(fightersInClass[0]); setBlueFighter(fightersInClass[1]); }
      else { setRedFighter(''); setBlueFighter(''); }
    }
    setPrediction(null);
  }, [selectedWeightClass, allFighters, weightClasses]);

  const handlePredict = () => {
    if (!redFighter || !blueFighter) { alert('Please select both fighters.'); return; }
    if (redFighter === blueFighter) { alert('Please select two different fighters.'); return; }
    setIsLoading(true); setPrediction(null);
    fetch('http://localhost:8000/predict', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ red_fighter: redFighter, blue_fighter: blueFighter }),
    })
    .then(response => response.json()).then(data => { console.log('Raw server response:', data); setPrediction(data); setIsLoading(false); })
    .catch(error => { console.error('Error:', error); setIsLoading(false); });
  };

  const handleShowWeights = () => {
    if (modelWeights.length > 0) { setShowWeights(!showWeights); }
    else {
      fetch('http://localhost:8000/model_weights').then(res => res.json())
        .then(data => {
          const sortedWeights = Object.entries(data).sort(([, a], [, b]) => Math.abs(b) - Math.abs(a));
          setModelWeights(sortedWeights);
          setShowWeights(true);
        }).catch(error => console.error('Error fetching weights:', error));
    }
  };

  return (
    <div className="App">
      <header className="App-header"><h1>UFC Fight Predictor</h1></header>
      <main className="main-content">
        <div className="filter-container">
          <label htmlFor="weightclass-filter">Filter by Weight Class</label>
          <select id="weightclass-filter" value={selectedWeightClass} onChange={(e) => setSelectedWeightClass(e.target.value)}>
            <option value="All">All Weight Classes</option>
            {Object.keys(weightClasses).sort().map(wc => (<option key={wc} value={wc}>{wc}</option>))}
          </select>
        </div>
        <div className="predictor-controls">
          <SearchableDropdown options={filteredFighters} selectedValue={redFighter} setSelectedValue={setRedFighter} label="Red Corner" />
          <div className="vs-interactive">VS</div>
          <SearchableDropdown options={filteredFighters} selectedValue={blueFighter} setSelectedValue={setBlueFighter} label="Blue Corner" />
        </div>
        <button onClick={handlePredict} disabled={isLoading} className="predict-button">{isLoading ? 'Predicting...' : 'Predict Winner'}</button>
        {prediction && (
          <div className="prediction-result">
            <h3>Prediction</h3>
            {prediction.error ? <p className="error">{prediction.error}</p> : (
              <div className="prediction-content">
                <div className="prediction-text">
                  <p className="winner"><strong>Winner:</strong> {prediction.PredictedWinner}</p>
                  <p><strong>Confidence:</strong> {prediction.Confidence}</p>
                  {prediction.explanation && (
                    <div className="explanation">
                      <p><strong>Expert Analysis:</strong> {prediction.explanation.main_point}</p>
                      <ul className="explanation-details">
                        {prediction.explanation.details && prediction.explanation.details.map((detail, i) => <li key={i}>{detail}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
                <PieChart prediction={prediction} />
              </div>
            )}
          </div>
        )}
        <div className="insights-container">
          <button onClick={handleShowWeights} className="insights-button">{showWeights ? 'Hide' : 'Show'} Model Insights</button>
          {showWeights && (
            <div className="weights-container">
              <h3>Model Feature Importance</h3>
              <p>How much the model 'cares' about each feature. A positive weight favors the Red corner, negative favors the Blue.</p>
              <table className="weights-table">
                <thead><tr><th>Feature</th><th>Learned Weight</th></tr></thead>
                <tbody>
                  {modelWeights.map(([feature, weight]) => (
                    <tr key={feature}><td>{feature}</td><td className={weight > 0 ? 'positive' : 'negative'}>{weight.toFixed(4)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;