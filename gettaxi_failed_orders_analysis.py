
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import h3
import folium
import branca.colormap as cm

# Load data
orders = pd.read_csv("data_orders.csv")
offers = pd.read_csv("data_offers.csv")

# Basic preparation
orders["hour"] = pd.to_datetime(orders["order_datetime"], format="%H:%M:%S").dt.hour

orders["failure_category"] = np.where(
    orders["order_status_key"] == 4,
    np.where(
        orders["is_driver_assigned_key"] == 1,
        "Cancelled by client after driver assignment",
        "Cancelled by client before driver assignment",
    ),
    "Rejected by system",
)

# 1) Distribution of failed orders
category_counts = orders["failure_category"].value_counts()
print("\nFailed orders by category:")
print(category_counts)

# 2) Hourly distribution
hourly_counts = (
    orders.groupby(["hour", "failure_category"])
    .size()
    .unstack(fill_value=0)
)

hourly_props = hourly_counts.div(hourly_counts.sum(axis=1), axis=0)

# 3) Average cancellation time by hour
cancelled = orders[orders["order_status_key"] == 4].copy()
cancelled["assigned_label"] = cancelled["is_driver_assigned_key"].map(
    {1: "With driver assigned", 0: "Without driver assigned"}
)

q1 = cancelled["cancellations_time_in_seconds"].quantile(0.25)
q3 = cancelled["cancellations_time_in_seconds"].quantile(0.75)
iqr = q3 - q1
upper_bound = q3 + 1.5 * iqr

cancelled_clean = cancelled[
    cancelled["cancellations_time_in_seconds"].between(0, upper_bound)
]

avg_cancel = (
    cancelled_clean.groupby(["hour", "assigned_label"])["cancellations_time_in_seconds"]
    .mean()
    .unstack()
)

# 4) Average ETA by hour
eta_by_hour = orders.groupby("hour")["m_order_eta"].mean()

# Plot 1
plt.figure(figsize=(8, 5))
category_counts.loc[
    [
        "Cancelled by client before driver assignment",
        "Cancelled by client after driver assignment",
        "Rejected by system",
    ]
].plot(kind="bar")
plt.title("Failed Orders by Failure Category")
plt.xlabel("")
plt.ylabel("Number of failed orders")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig("01_failure_categories.png", dpi=180)
plt.close()

# Plot 2
hourly_counts[
    [
        "Cancelled by client before driver assignment",
        "Cancelled by client after driver assignment",
        "Rejected by system",
    ]
].plot(kind="bar", stacked=True, figsize=(11, 5))
plt.title("Failed Orders by Hour and Failure Category")
plt.xlabel("Hour of day")
plt.ylabel("Number of failed orders")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("02_hourly_failed_orders_stacked.png", dpi=180)
plt.close()

# Plot 3
hourly_props[
    [
        "Cancelled by client before driver assignment",
        "Cancelled by client after driver assignment",
        "Rejected by system",
    ]
].plot(kind="bar", stacked=True, figsize=(11, 5))
plt.title("Hourly Mix of Failure Categories")
plt.xlabel("Hour of day")
plt.ylabel("Share of failed orders")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("03_hourly_failure_mix.png", dpi=180)
plt.close()

# Plot 4
avg_cancel[["Without driver assigned", "With driver assigned"]].plot(
    figsize=(10, 5), marker="o"
)
plt.title("Average Time to Cancellation by Hour (Outliers Removed)")
plt.xlabel("Hour of day")
plt.ylabel("Average cancellation time (seconds)")
plt.xticks(range(24))
plt.grid(True, alpha=0.25)
plt.tight_layout()
plt.savefig("04_avg_cancellation_time.png", dpi=180)
plt.close()

# Plot 5
plt.figure(figsize=(10, 5))
eta_by_hour.plot(marker="o")
plt.title("Average ETA by Hour")
plt.xlabel("Hour of day")
plt.ylabel("Average ETA (seconds)")
plt.xticks(range(24))
plt.grid(True, alpha=0.25)
plt.tight_layout()
plt.savefig("05_avg_eta_by_hour.png", dpi=180)
plt.close()

# BONUS: H3 hexagons
geo = orders[["origin_latitude", "origin_longitude"]].dropna().copy()
geo["hex8"] = geo.apply(
    lambda row: h3.latlng_to_cell(row["origin_latitude"], row["origin_longitude"], 8),
    axis=1,
)

hex_counts = geo["hex8"].value_counts().rename_axis("hex8").reset_index(name="order_count")
hex_counts["cum_share"] = hex_counts["order_count"].cumsum() / hex_counts["order_count"].sum()

hexes_needed = (hex_counts["cum_share"] < 0.8).sum() + 1
top_hexes = hex_counts.iloc[:hexes_needed]

center = [geo["origin_latitude"].mean(), geo["origin_longitude"].mean()]
m = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")
color_scale = cm.linear.YlOrRd_09.scale(top_hexes["order_count"].min(), top_hexes["order_count"].max())
color_scale.caption = "Failed orders per H3 hex (resolution 8)"

for _, row in top_hexes.iterrows():
    boundary = h3.cell_to_boundary(row["hex8"])
    folium.Polygon(
        locations=[(lat, lng) for lat, lng in boundary],
        color="#444444",
        weight=1,
        fill=True,
        fill_color=color_scale(row["order_count"]),
        fill_opacity=0.65,
        tooltip=f"Hex: {row['hex8']}<br>Failed orders: {row['order_count']}",
    ).add_to(m)

color_scale.add_to(m)
m.save("bonus_hex_map.html")

print(f"\nH3 bonus: {hexes_needed} hexes contain about {top_hexes['order_count'].sum() / len(geo) * 100:.1f}% of all failed orders.")
print("\nDone.")
