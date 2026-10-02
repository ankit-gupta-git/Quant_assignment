import React, { useState, useEffect } from 'react';
import TopBar from './components/layout/TopBar';
import Sidebar from './components/layout/Sidebar';
import Footer from './components/layout/Footer';

// Terminal View Components
import OverviewPage from './components/pages/OverviewPage';
import BacktestPage from './components/pages/BacktestPage';
import WalkForwardPage from './components/pages/WalkForwardPage';
import StrategyPage from './components/pages/StrategyPage';
import RiskPage from './components/pages/RiskPage';
import OrdersPage from './components/pages/OrdersPage';
import TradesPage from './components/pages/TradesPage';
import ArchitecturePage from './components/pages/ArchitecturePage';
import LogsPage from './components/pages/LogsPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');

  // Quick navigation: 1-9 for instant view change
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;

      const keyMap = {
        '1': 'overview',
        '2': 'backtest',
        '3': 'walkforward',
        '4': 'strategy',
        '5': 'risk',
        '6': 'orders',
        '7': 'trades',
        '8': 'architecture',
        '9': 'logs'
      };

      if (keyMap[e.key]) {
        setActiveTab(keyMap[e.key]);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const renderActivePage = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewPage onNavigate={setActiveTab} />;
      case 'backtest':
        return <BacktestPage />;
      case 'walkforward':
        return <WalkForwardPage />;
      case 'strategy':
        return <StrategyPage />;
      case 'risk':
        return <RiskPage />;
      case 'orders':
        return <OrdersPage />;
      case 'trades':
        return <TradesPage />;
      case 'architecture':
        return <ArchitecturePage />;
      case 'logs':
        return <LogsPage />;
      default:
        return <OverviewPage onNavigate={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#07090e] text-[#e2e8f0] flex flex-col font-sans select-none">
      {/* Top Application Bar */}
      <TopBar />

      {/* Main Container with Sidebar + Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Compact Navigation Sidebar */}
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Dynamic Main Workspace Canvas */}
        <main className="flex-1 p-2 overflow-y-auto max-w-[1920px] mx-auto w-full">
          {renderActivePage()}
        </main>
      </div>

      {/* Minimal Engineering Terminal Footer */}
      <Footer />
    </div>
  );
}
