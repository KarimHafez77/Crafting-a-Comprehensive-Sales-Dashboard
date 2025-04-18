import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from datetime import datetime
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

# Load the data
def load_and_preprocess_data(file_path):
    """Load and preprocess sales data from CSV file"""
    df = pd.read_csv(file_path)
    
    # Convert date columns to datetime
    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
    
    # Define time of day categories
    time_of_day = {
        'Morning': (5, 11),    # 5:00 AM - 11:59 AM
        'Afternoon': (12, 16), # 12:00 PM - 4:59 PM
        'Evening': (17, 20),   # 5:00 PM - 8:59 PM
        'Night': (21, 4)       # 9:00 PM - 4:59 AM
    }
    
    # Add a time of day column
    def categorize_time_of_day(hour):
        if time_of_day['Morning'][0] <= hour <= time_of_day['Morning'][1]:
            return 'Morning'
        elif time_of_day['Afternoon'][0] <= hour <= time_of_day['Afternoon'][1]:
            return 'Afternoon'
        elif time_of_day['Evening'][0] <= hour <= time_of_day['Evening'][1]:
            return 'Evening'
        else:
            return 'Night'
            
    df['Time_of_Day'] = df['Hour'].apply(categorize_time_of_day)
    
    # Add month-year for easier grouping
    df['Month_Year'] = df['Order_Date'].dt.to_period('M')
    
    # Add a Month name column for readability
    df['Month_Name'] = df['Order_Date'].dt.month_name()
    
    # Add Quarter
    df['Quarter'] = df['Order_Date'].dt.quarter
    
    # Create a date key for YoY and MoM calculations
    df['Year_Month'] = df['Order_Date'].dt.strftime('%Y-%m')
    
    # Convert Return_Flag to boolean if it's not already
    if df['Return_Flag'].dtype != bool:
        df['Return_Flag'] = df['Return_Flag'].astype(bool)
    
    # Calculate profit margin
    df['Profit_Margin'] = (df['Profit'] / df['Total_Sales']) * 100
    
    # Calculate average order size
    df['Order_Size'] = df['Total_Sales'] / df['Quantity_Sold']
    
    return df

def calculate_advanced_metrics(df):
    """Calculate advanced metrics for the dashboard"""
    metrics = {}
    
    # Basic KPIs
    metrics['Total_Sales'] = df['Total_Sales'].sum()
    metrics['Total_Quantity'] = df['Quantity_Sold'].sum()
    metrics['Total_Profit'] = df['Profit'].sum()
    metrics['Avg_Order_Size'] = df['Total_Sales'].sum() / df['Quantity_Sold'].sum()
    metrics['Return_Rate'] = df['Return_Flag'].mean() * 100
    
    # Monthly sales for growth calculations
    monthly_sales = df.groupby('Year_Month')['Total_Sales'].sum().reset_index()
    
    # Calculate MoM growth rate (if we have at least 2 months of data)
    if len(monthly_sales) >= 2:
        current_month = monthly_sales.iloc[-1]['Total_Sales']
        previous_month = monthly_sales.iloc[-2]['Total_Sales']
        metrics['MoM_Growth'] = ((current_month - previous_month) / previous_month) * 100
    else:
        metrics['MoM_Growth'] = 0
    
    # Calculate YoY growth rate (if we have at least 13 months of data)
    if len(monthly_sales) >= 13:
        current_month = monthly_sales.iloc[-1]['Total_Sales']
        year_ago_month = monthly_sales.iloc[-13]['Total_Sales']
        metrics['YoY_Growth'] = ((current_month - year_ago_month) / year_ago_month) * 100
    else:
        metrics['YoY_Growth'] = 0
    
    return metrics

def plot_monthly_sales_trend(df):
    """Plot monthly sales trend"""
    # Group by year and month
    monthly_sales = df.groupby(['Year', 'Month_Name', 'Month'])['Total_Sales'].sum().reset_index()
    
    # Sort by year and month for proper time series
    monthly_sales['Month_Num'] = monthly_sales['Month']
    monthly_sales = monthly_sales.sort_values(['Year', 'Month_Num'])
    
    # Create a date label for the x-axis
    monthly_sales['Date_Label'] = monthly_sales['Month_Name'] + ' ' + monthly_sales['Year'].astype(str)
    
    # Create the plot
    fig = px.line(monthly_sales, x='Date_Label', y='Total_Sales', 
                  title='Monthly Sales Trend',
                  markers=True)
    
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Total Sales',
        template='plotly_white'
    )
    
    return fig

def plot_hourly_sales_heatmap(df):
    """Create a heatmap of sales by hour and day of week"""
    # Group by day of week and hour
    hourly_data = df.groupby(['Day_of_Week', 'Hour'])['Total_Sales'].sum().reset_index()
    
    # Create a pivot table
    pivot_data = hourly_data.pivot(index='Day_of_Week', columns='Hour', values='Total_Sales')
    
    # Create the heatmap
    fig = px.imshow(pivot_data, 
                    labels=dict(x="Hour of Day", y="Day of Week", color="Sales"),
                    title="Sales Heatmap by Hour and Day",
                    color_continuous_scale='Viridis')
    
    fig.update_layout(template='plotly_white')
    
    return fig

def plot_sales_by_time_of_day(df):
    """Plot sales distribution by time of day"""
    tod_sales = df.groupby('Time_of_Day')['Total_Sales'].sum().reset_index()
    
    # Sort in chronological order
    time_order = ['Morning', 'Afternoon', 'Evening', 'Night']
    tod_sales['Time_of_Day'] = pd.Categorical(tod_sales['Time_of_Day'], categories=time_order, ordered=True)
    tod_sales = tod_sales.sort_values('Time_of_Day')
    
    # Create the plot
    fig = px.bar(tod_sales, x='Time_of_Day', y='Total_Sales',
                 title='Sales by Time of Day',
                 color='Time_of_Day')
    
    fig.update_layout(
        xaxis_title='Time of Day',
        yaxis_title='Total Sales',
        template='plotly_white'
    )
    
    return fig

def plot_product_sales_share(df):
    """Create a pie chart showing sales distribution by product"""
    product_sales = df.groupby('Product_ID')['Total_Sales'].sum().reset_index()
    
    # Sort and get the top 5, group others
    top_products = product_sales.sort_values('Total_Sales', ascending=False).head(5)
    other_products = pd.DataFrame({
        'Product_ID': ['Others'],
        'Total_Sales': [product_sales['Total_Sales'].sum() - top_products['Total_Sales'].sum()]
    })
    
    plot_data = pd.concat([top_products, other_products])
    
    # Create the pie chart
    fig = px.pie(plot_data, values='Total_Sales', names='Product_ID',
                 title='Sales Share by Product (Top 5)')
    
    fig.update_layout(template='plotly_white')
    
    return fig

def plot_sales_vs_returns(df):
    """Create a comparison of sales vs returns by region"""
    # Group by region
    region_data = df.groupby('Region_ID').agg({
        'Total_Sales': 'sum',
        'Return_Flag': lambda x: (x == True).sum()  # Count returns
    }).reset_index()
    
    region_data.rename(columns={'Return_Flag': 'Returns'}, inplace=True)
    
    # Sort by total sales
    region_data = region_data.sort_values('Total_Sales', ascending=False)
    
    # Create the bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=region_data['Region_ID'],
        y=region_data['Total_Sales'],
        name='Total Sales',
        marker_color='royalblue'
    ))
    
    fig.add_trace(go.Bar(
        x=region_data['Region_ID'],
        y=region_data['Returns'],
        name='Returns',
        marker_color='red'
    ))
    
    fig.update_layout(
        title='Sales vs Returns by Region',
        xaxis_title='Region',
        yaxis_title='Count',
        barmode='group',
        template='plotly_white'
    )
    
    return fig

def plot_profit_margin_trend(df):
    """Plot profit margin trend over time"""
    # Group by month
    monthly_margin = df.groupby('Month_Year')['Profit_Margin'].mean().reset_index()
    
    # Convert Period to string
    monthly_margin['Month_Year'] = monthly_margin['Month_Year'].astype(str)
    
    # Sort by month
    monthly_margin = monthly_margin.sort_values('Month_Year')
    
    # Create the line chart
    fig = px.line(monthly_margin, x='Month_Year', y='Profit_Margin',
                  title='Average Profit Margin Trend',
                  markers=True)
    
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Profit Margin (%)',
        template='plotly_white'
    )
    
    return fig

def create_sales_rep_performance_chart(df):
    """Create a horizontal bar chart of sales rep performance"""
    # Get sales rep performance
    rep_data = df.groupby('Sales_Rep_ID').agg({
        'Total_Sales': 'sum',
        'Profit': 'sum'
    }).reset_index()
    
    # Sort and get top 10
    top_reps = rep_data.sort_values('Total_Sales', ascending=False).head(10)
    
    # Create the horizontal bar chart
    fig = px.bar(top_reps, y='Sales_Rep_ID', x='Total_Sales',
                 title='Top 10 Sales Representatives by Total Sales',
                 orientation='h',
                 color='Profit')
    
    fig.update_layout(
        yaxis_title='Sales Rep ID',
        xaxis_title='Total Sales',
        template='plotly_white'
    )
    
    return fig

def generate_insights_and_recommendations(df):
    """Generate insights and recommendations based on the data analysis"""
    insights = []
    recommendations = []
    
    # Insight 1: Peak Sales Time
    tod_sales = df.groupby('Time_of_Day')['Total_Sales'].sum().reset_index()
    peak_time = tod_sales.loc[tod_sales['Total_Sales'].idxmax()]['Time_of_Day']
    peak_sales_percentage = (tod_sales.loc[tod_sales['Time_of_Day'] == peak_time, 'Total_Sales'].values[0] / df['Total_Sales'].sum()) * 100
    insights.append(f"Peak sales occur during {peak_time}, accounting for {peak_sales_percentage:.1f}% of total sales")
    
    # Insight 2: Best Performing Product
    product_sales = df.groupby('Product_ID')['Total_Sales'].sum().reset_index()
    top_product = product_sales.loc[product_sales['Total_Sales'].idxmax()]
    product_contribution = (top_product['Total_Sales'] / df['Total_Sales'].sum()) * 100
    insights.append(f"Product {top_product['Product_ID']} is the best performer, generating ${top_product['Total_Sales']:,.2f} in sales ({product_contribution:.1f}% of total sales)")
    
    # Insight 3: Best Performing Region
    region_sales = df.groupby('Region_ID')['Total_Sales'].sum().reset_index()
    top_region = region_sales.loc[region_sales['Total_Sales'].idxmax()]
    region_contribution = (top_region['Total_Sales'] / df['Total_Sales'].sum()) * 100
    insights.append(f"Region {top_region['Region_ID']} is the best performing region, generating ${top_region['Total_Sales']:,.2f} in sales ({region_contribution:.1f}% of total sales)")
    
    # Recommendation 1: Based on time analysis
    recommendations.append(f"Increase marketing and sales efforts during {peak_time} to maximize sales")
    
    # Recommendation 2: Based on product performance
    product_profit = df.groupby('Product_ID')['Profit'].sum().reset_index()
    high_margin_product = product_profit.loc[product_profit['Profit'].idxmax()]
    recommendations.append(f"Focus on Product {high_margin_product['Product_ID']} which generates the highest profit margin (${high_margin_product['Profit']:,.2f})")
    
    return insights, recommendations

def create_dash_app(file_path):
    """Create an interactive Dash web app for the dashboard"""
    # Load and process data
    df = load_and_preprocess_data(file_path)
    metrics = calculate_advanced_metrics(df)
    insights, recommendations = generate_insights_and_recommendations(df)
    
    # Create Dash app
    app = Dash(__name__)
    
    # Define the layout
    app.layout = html.Div([
        # Title
        html.H1("Comprehensive Sales Dashboard", style={'textAlign': 'center'}),
        
        # Filters Section
        html.Div([
            html.H3("Filters", style={'marginBottom': '10px'}),
            html.Div([
                # Region Filter
                html.Div([
                    html.Label("Region:"),
                    dcc.Dropdown(
                        id='region-filter',
                        options=[{'label': f"Region {r}", 'value': r} for r in df['Region_ID'].unique()],
                        multi=True,
                        placeholder="Select Region(s)"
                    ),
                ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
                
                # Time of Day Filter
                html.Div([
                    html.Label("Time of Day:"),
                    dcc.Dropdown(
                        id='time-filter',
                        options=[{'label': t, 'value': t} for t in ['Morning', 'Afternoon', 'Evening', 'Night']],
                        multi=True,
                        placeholder="Select Time(s) of Day"
                    ),
                ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
                
                # Year Filter
                html.Div([
                    html.Label("Year:"),
                    dcc.Dropdown(
                        id='year-filter',
                        options=[{'label': str(y), 'value': y} for y in df['Year'].unique()],
                        multi=False,
                        placeholder="Select Year"
                    ),
                ], style={'width': '30%', 'display': 'inline-block'}),
            ], style={'marginBottom': '20px'})
        ], style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'marginBottom': '20px', 'borderRadius': '5px'}),
        
        # KPI Section
        html.Div([
            html.H3("Key Performance Indicators", style={'marginBottom': '10px'}),
            html.Div([
                # Total Sales
                html.Div([
                    html.H5("Total Sales"),
                    html.H3(id='total-sales', children=f"${metrics['Total_Sales']:,.2f}")
                ], style={'width': '16%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#e6f2ff', 'padding': '10px', 'borderRadius': '5px'}),
                
                # Total Quantity
                html.Div([
                    html.H5("Quantity Sold"),
                    html.H3(id='total-quantity', children=f"{metrics['Total_Quantity']:,}")
                ], style={'width': '16%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#e6f2ff', 'padding': '10px', 'borderRadius': '5px', 'marginLeft': '5px'}),
                
                # Total Profit
                html.Div([
                    html.H5("Total Profit"),
                    html.H3(id='total-profit', children=f"${metrics['Total_Profit']:,.2f}")
                ], style={'width': '16%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#e6f2ff', 'padding': '10px', 'borderRadius': '5px', 'marginLeft': '5px'}),
                
                # Average Order Size
                html.Div([
                    html.H5("Avg Order Size"),
                    html.H3(id='avg-order-size', children=f"${metrics['Avg_Order_Size']:,.2f}")
                ], style={'width': '16%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#e6f2ff', 'padding': '10px', 'borderRadius': '5px', 'marginLeft': '5px'}),
                
                # MoM Growth
                html.Div([
                    html.H5("MoM Growth"),
                    html.H3(id='mom-growth', children=f"{metrics['MoM_Growth']:.2f}%")
                ], style={'width': '16%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#e6f2ff', 'padding': '10px', 'borderRadius': '5px', 'marginLeft': '5px'}),
                
                # Return Rate
                html.Div([
                    html.H5("Return Rate"),
                    html.H3(id='return-rate', children=f"{metrics['Return_Rate']:.2f}%")
                ], style={'width': '16%', 'display': 'inline-block', 'textAlign': 'center', 'backgroundColor': '#e6f2ff', 'padding': '10px', 'borderRadius': '5px', 'marginLeft': '5px'}),
            ])
        ], style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'marginBottom': '20px', 'borderRadius': '5px'}),
        
        # Monthly Trend and Time of Day
        html.Div([
            # Monthly Sales Trend
            html.Div([
                html.H3("Monthly Sales Trend"),
                dcc.Graph(id='monthly-trend', figure=plot_monthly_sales_trend(df))
            ], style={'width': '48%', 'display': 'inline-block'}),
            
            # Sales by Time of Day
            html.Div([
                html.H3("Sales by Time of Day"),
                dcc.Graph(id='time-of-day', figure=plot_sales_by_time_of_day(df))
            ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '20px'}),
        
        # Hourly Heatmap and Product Share
        html.Div([
            # Hourly Sales Heatmap
            html.Div([
                html.H3("Sales Heatmap by Hour and Day"),
                dcc.Graph(id='hourly-heatmap', figure=plot_hourly_sales_heatmap(df))
            ], style={'width': '48%', 'display': 'inline-block'}),
            
            # Product Sales Share
            html.Div([
                html.H3("Sales Share by Product"),
                dcc.Graph(id='product-share', figure=plot_product_sales_share(df))
            ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '20px'}),
        
        # Sales vs Returns and Profit Margin
        html.Div([
            # Sales vs Returns
            html.Div([
                html.H3("Sales vs Returns by Region"),
                dcc.Graph(id='sales-vs-returns', figure=plot_sales_vs_returns(df))
            ], style={'width': '48%', 'display': 'inline-block'}),
            
            # Profit Margin Trend
            html.Div([
                html.H3("Profit Margin Trend"),
                dcc.Graph(id='profit-margin', figure=plot_profit_margin_trend(df))
            ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '20px'}),
        
        # Sales Rep Performance
        html.Div([
            html.H3("Top Sales Representatives"),
            dcc.Graph(id='sales-rep', figure=create_sales_rep_performance_chart(df))
        ], style={'marginBottom': '20px'}),
        
        # Insights and Recommendations Section
        html.Div([
            # Insights
            html.Div([
                html.H3("Key Insights", style={'marginBottom': '10px'}),
                html.Ul(id='insights-list', children=[html.Li(insight) for insight in insights])
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            # Recommendations
            html.Div([
                html.H3("Recommendations", style={'marginBottom': '10px'}),
                html.Ul(id='recommendations-list', children=[html.Li(recommendation) for recommendation in recommendations])
            ], style={'width': '48%', 'display': 'inline-block', 'float': 'right', 'verticalAlign': 'top'})
        ], style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'marginBottom': '20px', 'borderRadius': '5px'}),
    ])

    # Callbacks for interactive filtering
    @app.callback(
        [Output('monthly-trend', 'figure'),
         Output('time-of-day', 'figure'),
         Output('hourly-heatmap', 'figure'),
         Output('product-share', 'figure'),
         Output('sales-vs-returns', 'figure'),
         Output('profit-margin', 'figure'),
         Output('sales-rep', 'figure'),
         Output('total-sales', 'children'),
         Output('total-quantity', 'children'),
         Output('total-profit', 'children'),
         Output('avg-order-size', 'children'),
         Output('mom-growth', 'children'),
         Output('return-rate', 'children'),
         Output('insights-list', 'children'),
         Output('recommendations-list', 'children')],
        [Input('region-filter', 'value'),
         Input('time-filter', 'value'),
         Input('year-filter', 'value')]
    )
    def update_dashboard(selected_regions, selected_times, selected_year):
        # Create a copy of the dataframe for filtering
        filtered_df = df.copy()
        
        # Apply filters
        if selected_regions:
            filtered_df = filtered_df[filtered_df['Region_ID'].isin(selected_regions)]
        if selected_times:
            filtered_df = filtered_df[filtered_df['Time_of_Day'].isin(selected_times)]
        if selected_year:
            filtered_df = filtered_df[filtered_df['Year'] == selected_year]
        
        # Recalculate metrics
        metrics = calculate_advanced_metrics(filtered_df)
        
        # Update visualizations
        monthly_trend_fig = plot_monthly_sales_trend(filtered_df)
        time_of_day_fig = plot_sales_by_time_of_day(filtered_df)
        hourly_heatmap_fig = plot_hourly_sales_heatmap(filtered_df)
        product_share_fig = plot_product_sales_share(filtered_df)
        sales_vs_returns_fig = plot_sales_vs_returns(filtered_df)
        profit_margin_fig = plot_profit_margin_trend(filtered_df)
        sales_rep_fig = create_sales_rep_performance_chart(filtered_df)
        
        # Update KPI values
        total_sales = f"${metrics['Total_Sales']:,.2f}"
        total_quantity = f"{metrics['Total_Quantity']:,}"
        total_profit = f"${metrics['Total_Profit']:,.2f}"
        avg_order_size = f"${metrics['Avg_Order_Size']:,.2f}"
        mom_growth = f"{metrics['MoM_Growth']:.2f}%"
        return_rate = f"{metrics['Return_Rate']:.2f}%"
        
        # Generate new insights and recommendations
        new_insights, new_recommendations = generate_insights_and_recommendations(filtered_df)
        
        # Create lists for insights and recommendations
        insights_list = html.Ul([html.Li(insight) for insight in new_insights])
        recommendations_list = html.Ul([html.Li(recommendation) for recommendation in new_recommendations])
        
        return (monthly_trend_fig, time_of_day_fig, hourly_heatmap_fig,
                product_share_fig, sales_vs_returns_fig, profit_margin_fig,
                sales_rep_fig, total_sales, total_quantity, total_profit,
                avg_order_size, mom_growth, return_rate,
                insights_list, recommendations_list)

    return app

if __name__ == '__main__':
    # Example usage
    file_path = "E:/bing.bong/Data - Orders.csv"  
    app = create_dash_app(file_path)
    app.run(debug=True, port=8052)