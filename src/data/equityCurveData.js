// Granular equity curve and underwater drawdown series for chart components
export const equityCurveAll = [
  { date: "2023-01-02", equity: 1000000.00, cash: 1000000.00, peak: 1000000.00, drawdown: 0.00, pnl: 0.00 },
  { date: "2023-01-16", equity: 1000000.00, cash: 1000000.00, peak: 1000000.00, drawdown: 0.00, pnl: 0.00 },
  { date: "2023-02-01", equity: 1000000.00, cash: 1000000.00, peak: 1000000.00, drawdown: 0.00, pnl: 0.00 },
  { date: "2023-02-20", equity: 1000000.00, cash: 1000000.00, peak: 1000000.00, drawdown: 0.00, pnl: 0.00 },
  { date: "2023-03-08", equity: 1000339.87, cash: 1000339.87, peak: 1000339.87, drawdown: 0.00, pnl: 339.87 },
  { date: "2023-03-15", equity: 1000210.40, cash: 1000210.40, peak: 1000339.87, drawdown: -0.013, pnl: 210.40 },
  { date: "2023-03-22", equity: 1000088.20, cash: 1000088.20, peak: 1000339.87, drawdown: -0.025, pnl: 88.20 },
  { date: "2023-03-24", equity: 999954.55, cash: 999954.55, peak: 1000339.87, drawdown: -0.038, pnl: -45.45 },
  { date: "2023-03-27", equity: 999936.20, cash: 999936.20, peak: 1000339.87, drawdown: -0.040, pnl: -63.80 },
  { date: "2023-03-28", equity: 999927.67, cash: 999927.67, peak: 1000339.87, drawdown: -0.041, pnl: -72.33 },
  { date: "2023-03-29", equity: 999812.85, cash: 999812.85, peak: 1000339.87, drawdown: -0.053, pnl: -187.15 },
  { date: "2023-03-30", equity: 999803.65, cash: 999803.65, peak: 1000339.87, drawdown: -0.054, pnl: -196.35 },
  { date: "2023-03-31", equity: 999909.56, cash: 999909.56, peak: 1000339.87, drawdown: -0.043, pnl: -90.44 },
  { date: "2023-04-03", equity: 999886.27, cash: 999886.27, peak: 1000339.87, drawdown: -0.045, pnl: -113.73 },
  { date: "2023-04-04", equity: 999858.54, cash: 999858.54, peak: 1000339.87, drawdown: -0.048, pnl: -141.46 },
  { date: "2023-04-05", equity: 999701.94, cash: 999701.94, peak: 1000339.87, drawdown: -4.990, pnl: -298.06 },
  { date: "2023-04-12", equity: 999840.10, cash: 999840.10, peak: 1000339.87, drawdown: -0.050, pnl: -159.90 },
  { date: "2023-04-18", equity: 999920.30, cash: 999920.30, peak: 1000339.87, drawdown: -0.042, pnl: -79.70 },
  { date: "2023-04-24", equity: 1000302.88, cash: 1000302.88, peak: 1000339.87, drawdown: -0.004, pnl: 302.88 },
  { date: "2023-05-02", equity: 1000537.18, cash: 1000537.18, peak: 1000537.18, drawdown: 0.00, pnl: 537.18 },
  { date: "2023-05-15", equity: 1000490.20, cash: 1000490.20, peak: 1000537.18, drawdown: -0.005, pnl: 490.20 },
  { date: "2023-06-01", equity: 1000330.26, cash: 1000330.26, peak: 1000537.18, drawdown: -0.021, pnl: 330.26 },
  { date: "2023-06-07", equity: 1000125.54, cash: 1000125.54, peak: 1000537.18, drawdown: -0.041, pnl: 125.54 },
  { date: "2023-06-15", equity: 1000320.10, cash: 1000320.10, peak: 1000537.18, drawdown: -0.022, pnl: 320.10 },
  { date: "2023-06-23", equity: 1000704.64, cash: 1000704.64, peak: 1000704.64, drawdown: 0.00, pnl: 704.64 },
  { date: "2023-07-05", equity: 1000926.77, cash: 1000926.77, peak: 1000926.77, drawdown: 0.00, pnl: 926.77 },
  { date: "2023-07-20", equity: 1000910.40, cash: 1000910.40, peak: 1000926.77, drawdown: -0.002, pnl: 910.40 },
  { date: "2023-08-07", equity: 1001144.91, cash: 1001144.91, peak: 1001144.91, drawdown: 0.00, pnl: 1144.91 },
  { date: "2023-08-25", equity: 1001144.91, cash: 1001144.91, peak: 1001144.91, drawdown: 0.00, pnl: 1144.91 }
];

export const equityTimeframeSlices = {
  '1D': [
    { time: "09:15", equity: 1000980.00, drawdown: 0.00, pnl: 980.00 },
    { time: "10:00", equity: 1001020.50, drawdown: 0.00, pnl: 1020.50 },
    { time: "11:00", equity: 1001090.20, drawdown: 0.00, pnl: 1090.20 },
    { time: "12:00", equity: 1001060.00, drawdown: -0.003, pnl: 1060.00 },
    { time: "13:00", equity: 1001085.40, drawdown: 0.00, pnl: 1085.40 },
    { time: "14:00", equity: 1001115.10, drawdown: 0.00, pnl: 1115.10 },
    { time: "15:00", equity: 1001144.91, drawdown: 0.00, pnl: 1144.91 },
    { time: "15:30", equity: 1001144.91, drawdown: 0.00, pnl: 1144.91 }
  ],
  '1W': [
    { time: "Mon", equity: 1000910.40, drawdown: -0.002, pnl: 910.40 },
    { time: "Tue", equity: 1000965.20, drawdown: 0.00, pnl: 965.20 },
    { time: "Wed", equity: 1001010.00, drawdown: 0.00, pnl: 1010.00 },
    { time: "Thu", equity: 1001080.30, drawdown: 0.00, pnl: 1080.30 },
    { time: "Fri", equity: 1001144.91, drawdown: 0.00, pnl: 1144.91 }
  ],
  '1M': [
    { time: "W1", equity: 1000720.00, drawdown: 0.00, pnl: 720.00 },
    { time: "W2", equity: 1000850.50, drawdown: 0.00, pnl: 850.50 },
    { time: "W3", equity: 1000926.77, drawdown: 0.00, pnl: 926.77 },
    { time: "W4", equity: 1001144.91, drawdown: 0.00, pnl: 1144.91 }
  ],
  'ALL': equityCurveAll
};
