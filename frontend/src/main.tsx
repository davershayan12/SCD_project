import React from 'react';
import ReactDOM from 'react-dom/client';
import PlagiarismChecker from './features/plagiarism/PlagiarismChecker';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PlagiarismChecker />
  </React.StrictMode>,
);
