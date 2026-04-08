# GetTaxi Failed Orders Analysis

This project analyzes failed taxi orders using two datasets: `data_orders` and `data_offers`.

## Objective
The goal was to investigate why customer orders failed and identify patterns by:
- failure reason
- hour of day
- cancellation timing
- average ETA
- geographic concentration of failed orders using H3 hexagons

## Files
- `gettaxi_failed_orders_analysis.py` — main analysis script
- `GetTaxi_Failed_Orders_Analysis.docx` — written business-style report
- `bonus_hex_map.html` — interactive map for the bonus task

## Key Findings
- The largest failure category was **client cancellations before driver assignment**
- The highest failed-order volume appeared around **08:00** and **21:00–23:00**
- Overnight hours showed a relatively higher share of **system rejections**
- Orders cancelled after driver assignment usually took longer to cancel
- ETA peaked during high-demand hours, especially in the morning
- A small number of H3 hexes contained most failed orders

## Tools Used
- Python
- pandas
- matplotlib
- h3
- folium

## Business Takeaway
The results suggest that failure patterns are strongly linked to driver availability and demand spikes. Improving supply coverage during peak hours and in high-fail zones could reduce unsuccessful orders.