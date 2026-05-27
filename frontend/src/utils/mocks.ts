export const MOCK_METRICS = [
  { label: '10Y Treasury', value: 4.250, change: -0.030, unit: '%' },
  { label: '2Y Treasury', value: 4.450, change: 0.050, unit: '%' },
  { label: 'Fed Funds Rate', value: 5.330, change: 0, unit: '%' },
  { label: 'SOFR', value: 5.310, change: -0.010, unit: '%' },
  { label: 'CPI YoY', value: 3.200, change: -0.100, unit: '%' },
];

export const MOCK_CURVE = [
  { maturity: '1M', yield: 5.35 }, { maturity: '3M', yield: 5.30 }, { maturity: '6M', yield: 5.22 },
  { maturity: '1Y', yield: 5.00 }, { maturity: '2Y', yield: 4.45 }, { maturity: '3Y', yield: 4.30 },
  { maturity: '5Y', yield: 4.18 }, { maturity: '7Y', yield: 4.22 }, { maturity: '10Y', yield: 4.25 },
  { maturity: '20Y', yield: 4.48 }, { maturity: '30Y', yield: 4.52 },
];

export const MOCK_SPREADS = [
  { name: 'IG Spread', value: 98, change: -2 },
  { name: 'HY Spread', value: 358, change: 5 },
  { name: '10Y-2Y', value: -0.20, change: -0.05 },
  { name: '10Y-3M', value: -1.05, change: 0.02 },
];

export const MOCK_RATES = [
  { name: '10Y Treasury', current: 4.250, d1: -0.030, w1: -0.080, m1: 0.120 },
  { name: '2Y Treasury', current: 4.450, d1: 0.050, w1: 0.020, m1: -0.150 },
  { name: '30Y Treasury', current: 4.520, d1: -0.020, w1: -0.050, m1: 0.100 },
  { name: '5Y Treasury', current: 4.180, d1: 0.010, w1: -0.030, m1: 0.050 },
  { name: 'Fed Funds', current: 5.330, d1: 0, w1: 0, m1: 0 },
  { name: 'SOFR', current: 5.310, d1: -0.010, w1: -0.010, m1: -0.020 },
  { name: '30Y Mortgage', current: 6.890, d1: -0.020, w1: -0.050, m1: -0.120 },
];

export const MOCK_AUCTIONS = [
  { desc: '4-Week Bill', type: 'Bill', date: '2026-06-02', rate: '5.28%' },
  { desc: '13-Week Bill', type: 'Bill', date: '2026-06-03', rate: '5.22%' },
  { desc: '2-Year Note', type: 'Note', date: '2026-06-05', rate: '4.45%' },
  { desc: '5-Year Note', type: 'Note', date: '2026-06-08', rate: '4.18%' },
  { desc: '10-Year Note', type: 'Note', date: '2026-06-10', rate: '4.25%' },
  { desc: '30-Year Bond', type: 'Bond', date: '2026-06-15', rate: '4.52%' },
];
