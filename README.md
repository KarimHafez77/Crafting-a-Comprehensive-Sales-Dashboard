# 📊Sales Performance Dashboard

A comprehensive data visualization tool for analyzing sales metrics, tracking KPIs, and generating actionable insights to drive revenue growth.

![Dashboard Preview](https://github.com/user-attachments/assets/279f3b1d-04bf-402b-9bf7-2924060f37de)


## 🚀 Features

- **Real-time KPI tracking**: Monitor key sales metrics at a glance
- **Interactive visualizations**: Explore data through intuitive charts and graphs
- **Dynamic filtering**: Slice data by multiple dimensions for deeper analysis
- **Performance benchmarking**: Identify top performers across products, regions, and sales reps
- **Actionable recommendations**: Data-driven suggestions to improve sales outcomes

## Dashboard Components

### 1. KPI Summary Section
- Total Sales
- Total Quantity Sold
- Total Profit
- Average Order Size
- Sales Growth Rate
- Return Rate

### 2. Top Performers Analysis
- Top 2 products by total sales
- Top 2 regions by total sales
- Top 2 customers by total sales

### 3. Time-Based Analytics
- Sales by day of the week (peak day identification)
- Sales by time segment (morning/afternoon/evening/night)
- Hourly sales distribution heatmap

### 4. Interactive Controls
- Product Category selector
- Region filter
- Sales Rep filter
- Date range (Year/Month) picker
- Time of Day slicer

### Metrics Calculations
```python
# Sample calculation - Sales Growth Rate
def calculate_growth(current_period, previous_period):
    return ((current_period - previous_period) / previous_period) * 100
