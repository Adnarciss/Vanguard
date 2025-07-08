import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide"
)

# --- CONFIGURATION ---
CURRENCY = "₹" # <--- CHANGED: Set currency to Indian Rupee

# --- DATA PERSISTENCE ---
# Define file paths for storing data
INCOME_FILE = 'income_data.csv'
EXPENSES_FILE = 'expenses_data.csv'

# Function to load data or create an empty DataFrame if file doesn't exist
def load_data(file_path, columns):
    """
    Loads data from a CSV file. If the file doesn't exist,
    it creates an empty DataFrame with the specified columns.
    """
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)

    # Ensure date columns are in datetime format
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])

    return df

# Function to save data to a CSV file
def save_data(df, file_path):
    """Saves a DataFrame to a CSV file."""
    df.to_csv(file_path, index=False)

# --- APP ---

# --- HEADER ---
st.title("💰 Personal Finance Tracker")
st.markdown("Welcome! Log your income and expenses to get a clear view of your financial health.")

# --- DATA LOADING ---
# Define columns for our dataframes
income_cols = ['Date', 'Source', 'Amount']
expense_cols = ['Date', 'Category', 'Item', 'Amount']

# Pre-defined expense categories
expense_categories = [
    "🏠 Housing", "🍔 Food", "🚗 Transportation", "🎭 Entertainment",
    "💊 Health", "🛒 Shopping", "Utilities", "💸 Debt",
    "🎓 Education", "🎁 Gifts/Donations", "📈 Investments", "Other"
]

# Load existing data
income_df = load_data(INCOME_FILE, income_cols)
expenses_df = load_data(EXPENSES_FILE, expense_cols)

# --- SIDEBAR FOR DATA ENTRY ---
st.sidebar.header("📊 Add a Transaction")

# Form for adding new transactions
with st.sidebar.form("transaction_form", clear_on_submit=True):
    transaction_type = st.radio("Select Transaction Type:", ('Income', 'Expense'))
    date = st.date_input("Date", datetime.now())
    amount = st.number_input("Amount", min_value=0.01, format="%.2f")

    if transaction_type == 'Income':
        source = st.text_input("Source (e.g., Salary, Freelance)")
        submitted = st.form_submit_button("Add Income")
        if submitted:
            if not source:
                st.sidebar.error("Please enter an income source.")
            else:
                new_income = pd.DataFrame([{'Date': date, 'Source': source, 'Amount': amount}])
                income_df = pd.concat([income_df, new_income], ignore_index=True)
                save_data(income_df, INCOME_FILE)
                st.sidebar.success("Income added successfully!")

    else: # Expense
        category = st.selectbox("Category", expense_categories)
        item = st.text_input("Item or Description (e.g., Groceries, Netflix)")
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            if not item:
                st.sidebar.error("Please enter an item or description.")
            else:
                new_expense = pd.DataFrame([{'Date': date, 'Category': category, 'Item': item, 'Amount': amount}])
                expenses_df = pd.concat([expenses_df, new_expense], ignore_index=True)
                save_data(expenses_df, EXPENSES_FILE)
                st.sidebar.success("Expense added successfully!")

# --- MAIN PAGE LAYOUT ---
# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Detailed Data", "ℹ️ About"])

with tab1:
    st.header("Financial Dashboard")

    # --- SUMMARY METRICS ---
    total_income = income_df['Amount'].sum()
    total_expenses = expenses_df['Amount'].sum()
    balance = total_income - total_expenses

    col1, col2, col3 = st.columns(3)
    # --- CHANGED: Using the CURRENCY variable in f-strings ---
    col1.metric("Total Income", f"{CURRENCY}{total_income:,.2f}", delta_color="normal")
    col2.metric("Total Expenses", f"{CURRENCY}{total_expenses:,.2f}", delta_color="inverse")
    
    balance_delta_text = ""
    if total_income > 0:
        balance_delta_text = f"{(balance/total_income):.2%}"

    # --- CHANGED: Using the CURRENCY variable in f-strings ---
    col3.metric("Balance", f"{CURRENCY}{balance:,.2f}", f"{balance_delta_text} of Income", delta_color="normal" if balance >= 0 else "inverse")

    st.markdown("---")

    # --- VISUALIZATIONS ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Expenses by Category")
        if not expenses_df.empty:
            category_expenses = expenses_df.groupby('Category')['Amount'].sum().reset_index()
            fig_pie = px.pie(category_expenses,
                             names='Category',
                             values='Amount',
                             title='Expense Distribution',
                             hole=.3)
            # --- CHANGED: Add currency to hover data in the pie chart ---
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', hovertemplate='<b>%{label}</b><br>Amount: ' + CURRENCY + '%{value:,.2f}<br>Percentage: %{percent}')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense data to display.")

    with col2:
        st.subheader("Income vs. Expenses Over Time")
        if not income_df.empty or not expenses_df.empty:
            # Combine and resample data by month
            income_monthly = income_df.set_index('Date').resample('M')['Amount'].sum().rename('Income')
            expense_monthly = expenses_df.set_index('Date').resample('M')['Amount'].sum().rename('Expense')
            
            monthly_summary = pd.concat([income_monthly, expense_monthly], axis=1).fillna(0).reset_index()
            monthly_summary['Date'] = monthly_summary['Date'].dt.strftime('%Y-%b')

            fig_bar = px.bar(monthly_summary,
                             x='Date',
                             y=['Income', 'Expense'],
                             title='Monthly Income vs. Expense',
                             barmode='group',
                             color_discrete_map={'Income': 'green', 'Expense': 'red'})
            # --- CHANGED: Add currency to hover data in the bar chart ---
            fig_bar.update_traces(hovertemplate='<b>%{x}</b><br>%{data.name}: ' + CURRENCY + '%{y:,.2f}<extra></extra>')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No income or expense data to display.")

with tab2:
    st.header("Detailed Transaction Data")

    st.subheader("Income History")
    if not income_df.empty:
        # --- CHANGED: Format the 'Amount' column with the currency ---
        st.dataframe(income_df.sort_values(by='Date', ascending=False).style.format({"Amount": "{}{:,.2f}".format(CURRENCY)}), use_container_width=True)
    else:
        st.info("No income records yet.")

    st.subheader("Expense History")
    if not expenses_df.empty:
        # --- CHANGED: Format the 'Amount' column with the currency ---
        st.dataframe(expenses_df.sort_values(by='Date', ascending=False).style.format({"Amount": "{}{:,.2f}".format(CURRENCY)}), use_container_width=True)
    else:
        st.info("No expense records yet.")
        
with tab3:
    st.header("About This App")
    st.info(
        """
        **Personal Finance Tracker** is a simple yet powerful tool built with Streamlit to help you
        manage your budget effectively.

        **How to use it?**
        1.  Use the sidebar on the left to add your income and expenses.
        2.  Navigate to the **Dashboard** tab to see a visual summary of your finances.
        3.  Visit the **Detailed Data** tab to review all your past transactions.

        All data you enter is saved locally in your project folder as `income_data.csv` and `expenses_data.csv`.
        
        Enjoy managing your finances!
        """
    )
