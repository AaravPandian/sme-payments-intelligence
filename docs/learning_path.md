# Learn the project later — beginner path

You can publish the complete code now and learn to rebuild it later. Understanding and independently extending the project will help you explain it credibly to recruiters.

## Lesson 1 — Learn the business vocabulary

Understand an attempted payment, successful payment, refund, processing fee, payout, and pending settlement. Read the README's KPI formulas and the data dictionary. Ask yourself: why are payment *attempts* not equal to successfully processed value?

## Lesson 2 — Open the CSV files with Pandas

Start with `data/payments.csv`. Practise `pd.read_csv`, `.head()`, `.shape`, filtering `payment_status == 'succeeded'`, `.sum()`, `.groupby('payment_method')`, and calculating a success rate.

**Challenge:** Calculate successful GBP processing value without looking at `src/analytics.py`.

## Lesson 3 — Learn relational SQL

Read `sql/schema.sql`. Learn primary keys, foreign keys, `JOIN`, `LEFT JOIN`, `GROUP BY`, `CASE WHEN`, `ORDER BY`, and `HAVING`. Start with `sql/queries/02_payment_method_success.sql` and work through the remaining six queries.

**Challenge:** Return the three merchants with the most successful payments (not necessarily highest value).

## Lesson 4 — Build a data pipeline

Study `src/generate_data.py`, then `src/database.py` and `scripts/build_project.py`. Learn reproducible random seeds, saving CSVs, and constructing an SQLite DB from tabular data.

**Challenge:** Change the seed in `src/config.py`, rebuild, and compare the KPI results. Restore the default seed for the original portfolio statistics.

## Lesson 5 — Write unit tests

Read `tests/test_analytics.py` and `tests/test_pipeline.py`. Learn why good analytical code tests basic financial maths and one-to-one joins.

**Challenge:** Write a test proving failed payment amounts never count as successful gross volume.

## Lesson 6 — Add Plotly visualisations

Look at each `px.bar`, `px.line`, `px.scatter`, and `px.pie` in `app.py` and understand what passes as `x`, `y`, `color` and `size`.

**Challenge:** Add a chart of gross volume by city.

## Lesson 7 — Understand Streamlit and GitHub

Learn `st.metric`, `st.sidebar`, `st.multiselect`, `st.tabs`, `st.dataframe`, and `st.download_button`. Practise Git `status`, `add`, `commit`, and `push`; watch the Actions tab run your tests.

**Challenge:** Add a new SQL query that computes average successful payment value per industry, and explain the difference between average amount and total processed value.

## Interview walkthrough (2 minutes)

1. **Business problem:** SMEs need clear visibility into payment approvals, refund value and expected payouts.
2. **Data model:** I generated a fictional portfolio with four related tables and validated the joins.
3. **Analysis:** I used SQL and Pandas to create KPIs for volume, approval, fees, refund rates and payouts.
4. **Presentation:** I built a Streamlit dashboard with filters, Plotly charts, a SQL Lab and CSV exports.
5. **Limitations:** The data is synthetic, refunds are attributed to original payments, and this is not a complete reconciliation ledger.
6. **Next step:** Add a proper event-based ledger and daily payout reconciliation.

For interviews, be clear that this is an **educational portfolio project** and what you have personally learned or modified so far.
