import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import CurationPage from './pages/CurationPage';
import SourcesPage from './pages/SourcesPage';
import SettingsPage from './pages/SettingsPage';
import FavoritesPage from './pages/FavoritesPage';
import PromptDialog from './components/common/PromptDialog';
import { useAppStore } from './store';

function App() {
  const createDefaultPromptsIfNeeded = useAppStore(state => state.createDefaultPromptsIfNeeded);
  const loadDefaultSettings = useAppStore(state => state.loadDefaultSettings);
  
  useEffect(() => {
    // Check if any prompts exist and show dialog if needed
    createDefaultPromptsIfNeeded();
    
    // Load default prompts for filter and summary
    loadDefaultSettings();
  }, [createDefaultPromptsIfNeeded, loadDefaultSettings]);
  
  return (
    <Router>
      <PromptDialog />
      <Layout>
        <Routes>
          <Route path="/" element={<CurationPage />} />
          <Route path="/sources" element={<SourcesPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;