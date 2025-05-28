import React, { useState } from 'react';
import { stateService } from '../services/stateService';

export const StateExporter: React.FC = () => {
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importData, setImportData] = useState('');

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const stateData = await stateService.exportState();
      const dataStr = JSON.stringify(stateData, null, 2);
      
      // Create and trigger download
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `loop-learner-state-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export state:', error);
      // TODO: Add proper error handling
    } finally {
      setIsExporting(false);
    }
  };

  const handleImport = async () => {
    if (!importData.trim()) {
      alert('Please paste state data to import');
      return;
    }

    setIsImporting(true);
    try {
      const stateData = JSON.parse(importData);
      const success = await stateService.importState(stateData);
      
      if (success) {
        alert('State imported successfully');
        setImportData('');
      } else {
        alert('Failed to import state');
      }
    } catch (error) {
      console.error('Failed to import state:', error);
      alert('Invalid JSON data or import failed');
    } finally {
      setIsImporting(false);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setImportData(content);
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="state-exporter">
      <h3>State Management</h3>
      
      <div className="export-section">
        <h4>Export State</h4>
        <p>Download current system state, preferences, and snapshots</p>
        <button 
          onClick={handleExport} 
          disabled={isExporting}
          className="export-button"
        >
          {isExporting ? 'Exporting...' : 'Export State'}
        </button>
      </div>

      <div className="import-section">
        <h4>Import State</h4>
        <p>Load previously exported state data</p>
        
        <div className="file-upload">
          <input
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="file-input"
          />
          <span>Or paste JSON data below:</span>
        </div>

        <textarea
          value={importData}
          onChange={(e) => setImportData(e.target.value)}
          placeholder="Paste exported state JSON here..."
          className="import-textarea"
          rows={10}
        />

        <button 
          onClick={handleImport} 
          disabled={isImporting || !importData.trim()}
          className="import-button"
        >
          {isImporting ? 'Importing...' : 'Import State'}
        </button>
      </div>
    </div>
  );
};