import argparse
import psycopg2
from pathlib import Path

DB_CONFIG = {
    "dbname": "trading_tracker",
    "user": "tracker_user",
    "password": "tracker_pass",
    "host": "localhost",
    "port": 5432
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def add_trade():
    symbol = input("Symbol (e.g. EURUSD): ").upper().strip()

    direction = input("Direction (LONG / SHORT): ").upper().strip()
    if direction not in ("LONG", "SHORT"):
        raise ValueError("Direction must be LONG or SHORT")

    setup = input("Setup type (A / B / C): ").upper().strip()
    if setup not in ("A", "B", "C"):
        raise ValueError("Setup must be A, B, or C")

    notes = input("Notes (optional): ").strip()

    screenshot = input("Screenshot path (optional): ").strip()
    screenshot_path = None
    if screenshot:
        p = Path(screenshot)
        if not p.exists():
            raise FileNotFoundError("Screenshot file does not exist")
        screenshot_path = str(p.resolve())

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tracker.trades
        (symbol, direction, setup, notes, screenshot_path)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        symbol,
        direction,
        setup,
        notes if notes else None,
        screenshot_path
    ))

    trade_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()

    print(f"\n✅ Trade recorded with ID: {trade_id}")


def close_trade():
    trade_id = input("Trade ID to close: ").strip()
    if not trade_id.isdigit():
        raise ValueError("Trade ID must be a number")

    outcome = input("Outcome (WIN / LOSS / BREAKEVEN): ").upper().strip()
    if outcome not in ("WIN", "LOSS", "BREAKEVEN"):
        raise ValueError("Invalid outcome")

    exit_price = input("Exit price (optional): ").strip()
    exit_price_val = float(exit_price) if exit_price else None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE tracker.trades
        SET outcome = %s,
            exit_price = %s
        WHERE id = %s;
    """, (outcome, exit_price_val, trade_id))

    if cur.rowcount == 0:
        raise ValueError("Trade ID not found")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n✅ Trade {trade_id} closed as {outcome}")

def show_stats():
    conn = get_connection()
    cur = conn.cursor()

    print("\n=== Win Rate by Setup ===")
    cur.execute("""
        SELECT
            setup,
            COUNT(*) AS trades,
            COUNT(*) FILTER (WHERE outcome = 'WIN') AS wins,
            ROUND(
                COUNT(*) FILTER (WHERE outcome = 'WIN')::numeric
                / NULLIF(COUNT(*) FILTER (WHERE outcome IS NOT NULL), 0),
                2
            ) AS win_rate
        FROM tracker.trades
        WHERE outcome IS NOT NULL
        GROUP BY setup
        ORDER BY setup;
    """)
    for row in cur.fetchall():
        print(row)

    print("\n=== Win Rate by Direction ===")
    cur.execute("""
        SELECT
            direction,
            COUNT(*) AS trades,
            COUNT(*) FILTER (WHERE outcome = 'WIN') AS wins,
            ROUND(
                COUNT(*) FILTER (WHERE outcome = 'WIN')::numeric
                / NULLIF(COUNT(*) FILTER (WHERE outcome IS NOT NULL), 0),
                2
            ) AS win_rate
        FROM tracker.trades
        WHERE outcome IS NOT NULL
        GROUP BY direction;
    """)
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="PnF Trading Journal")
    parser.add_argument("cmd", choices=["add", "close", "stats"])

    args = parser.parse_args()

    if args.cmd == "add":
        add_trade()
    elif args.cmd == "close":
        close_trade()
    elif args.cmd == "stats":
        show_stats()


if __name__ == "__main__":
    main()

