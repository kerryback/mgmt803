"""Revenue by customer country.

Reads the five Northwind spreadsheets in the parent folder, joins them, and
writes country_revenue.csv plus a summary to stdout.
"""

import pandas as pd

DATA = ".."

orders = pd.read_excel(f"{DATA}/northwind_orders.xlsx")
details = pd.read_excel(f"{DATA}/northwind_orderdetails.xlsx")
customers = pd.read_excel(f"{DATA}/northwind_customers.xlsx")
products = pd.read_excel(f"{DATA}/northwind_products.xlsx")

# Bring in the product record so the report can break out by category later.
lines = details.merge(products, on="ProductID")

# Attach the order and then the customer, so every line knows its country.
lines = lines.merge(orders, on="OrderID")
lines = lines.merge(customers, on="CustomerID")

lines["Revenue"] = lines["UnitPrice_y"] * lines["Quantity"]

by_country = (
    lines.groupby("Country")["Revenue"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
by_country["Share"] = by_country["Revenue"] / by_country["Revenue"].sum()

by_country.to_csv("country_revenue.csv", index=False)

n_orders = len(lines)
total = by_country["Revenue"].sum()

print(f"Orders analyzed:      {n_orders:,}")
print(f"Total revenue:        ${total:,.2f}")
print(f"Average order value:  ${total / n_orders:,.2f}")
print()
print(by_country.head(5).to_string(index=False))
