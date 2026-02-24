Tracking Journal

A simple full-stack trading journal application that allows users to record trades, track performance, and review historical results.

The focus of this project was implementing structured trade recording with backend validation and reliable profit/loss aggregation.

Tech Stack

Backend:

Python

(Flask / FastAPI – specify which)

SQLite (or your DB)

Frontend:

Basic UI for trade input and review

Core Functionality

Users can:

Add a trade (entry price, exit price, position size)

Automatically calculate profit or loss

View trade history

View aggregated total performance

All calculations are performed server-side.

Data Validation & Integrity

The backend enforces:

Entry and exit prices must be positive

Position size must be greater than zero

Profit/loss calculated from stored values

Trades persisted in SQL database

No manual editing of computed profit values

Aggregation logic (total P/L) is derived from stored trades rather than client input.

What This Project Demonstrates

SQL data persistence

Backend validation logic

Derived field calculation

Basic financial aggregation

Separation between UI and business logic

REST-based interaction (if applicable)

Example Edge Cases Considered

Negative prices

Zero position size

Extremely large trade values

Invalid numeric input

Empty database aggregation

Future Improvements

Risk/reward metrics

Performance visualization

Export functionality

Advanced analytics
