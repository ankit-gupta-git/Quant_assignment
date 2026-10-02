// Macro regime analysis and indicator values from app/macro/regime.py & data/macro.csv
export const currentMacroSnapshot = {
  regime: "RISK_OFF / HIGH_VOLATILITY",
  compositeScore: 0.72, // Scale: 0 (Ultra Bullish) to 1.0 (Extreme Risk-Off)
  indiaVix: {
    value: 18.52,
    change: "+0.84",
    thresholds: { normal: 15.0, elevated: 20.0, high: 25.0, extreme: 35.0 },
    status: "ELEVATED",
    score: 0.65
  },
  usdinr: {
    value: 83.18,
    change: "+0.08",
    status: "RANGEBOUND_WEAK",
    score: 0.68
  },
  brentCrude: {
    value: 84.00,
    unit: "$/bbl",
    change: "-1.20",
    status: "STABLE",
    score: 0.55
  },
  tenYearYield: {
    value: 7.112,
    unit: "%",
    change: "-0.015",
    status: "NORMAL_SLOPE",
    score: 0.48
  },
  policyAdjustments: {
    gridMultiplier: "1.5x",
    normalGridMultiplier: "1.0x",
    positionSizing: "50%",
    maxPositionsAllowed: 6,
    defaultMaxPositions: 10,
    circuitBreakerStatus: "ARMED_NORMAL",
    vixThresholdHigh: 25.0,
    vixThresholdExtreme: 35.0
  },
  historicalRegimeTrend: [
    { date: "2023-01", vix: 18.52, usdinr: 83.18, crude: 84.0, yield: 7.112, regime: "SIDEWAYS" },
    { date: "2023-02", vix: 17.92, usdinr: 82.93, crude: 85.9, yield: 7.043, regime: "SIDEWAYS" },
    { date: "2023-03", vix: 18.22, usdinr: 83.38, crude: 81.42, yield: 6.998, regime: "RISK_OFF" },
    { date: "2023-04", vix: 17.36, usdinr: 82.47, crude: 77.63, yield: 7.147, regime: "SIDEWAYS" },
    { date: "2023-05", vix: 17.39, usdinr: 82.21, crude: 77.47, yield: 7.239, regime: "BULL" },
    { date: "2023-06", vix: 18.96, usdinr: 82.40, crude: 75.71, yield: 7.245, regime: "SIDEWAYS" },
    { date: "2023-07", vix: 16.80, usdinr: 82.15, crude: 79.20, yield: 7.180, regime: "BULL" },
    { date: "2023-08", vix: 18.52, usdinr: 83.18, crude: 84.00, yield: 7.112, regime: "HIGH_VOLATILITY" }
  ]
};
