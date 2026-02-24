import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime
import calendar

# -----------------------------
# Database connection
# -----------------------------
DB_URL = "postgresql://tracker_user:tracker_pass@localhost:5432/trading_tracker"

def get_conn():
    return psycopg2.connect(DB_URL)

# -----------------------------
# Helpers
# -----------------------------
def get_month_matrix(year, month):
    cal = calendar.Calendar(firstweekday=0)  # Monday
    return cal.monthdatescalendar(year, month)

def get_trades_by_date(day):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT *
        FROM tracker.trades
        WHERE trade_date::date = %s
        ORDER BY trade_date ASC
        """,
        (day,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def insert_trade(trade_date, symbol, direction, setup, entry_price, notes):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tracker.trades
        (trade_date, symbol, direction, setup, entry_price, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (trade_date, symbol, direction, setup, entry_price, notes)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_day_outcomes_for_month(year, month):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT
            trade_date::date AS day,
            COUNT(*) FILTER (WHERE outcome = 'WIN') AS wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') AS losses
        FROM tracker.trades
        WHERE EXTRACT(YEAR FROM trade_date) = %s
          AND EXTRACT(MONTH FROM trade_date) = %s
        GROUP BY trade_date::date
        """,
        (year, month)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = {}
    for r in rows:
        if r["wins"] > r["losses"]:
            result[r["day"]] = "green"
        elif r["losses"] > r["wins"]:
            result[r["day"]] = "red"
        else:
            result[r["day"]] = "gray"

    return result

def get_day_stats(day):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE outcome = 'WIN') AS wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') AS losses
        FROM tracker.trades
        WHERE trade_date::date = %s
        """,
        (day,)
    )

    stats = cur.fetchone()
    cur.close()
    conn.close()

    return stats

def get_stats_by_setup(start_date, end_date):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT
            setup,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE outcome = 'WIN') AS wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') AS losses
        FROM tracker.trades
        WHERE trade_date::date BETWEEN %s AND %s
          AND outcome IS NOT NULL
        GROUP BY setup
        ORDER BY setup
        """,
        (start_date, end_date)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_stats_by_direction(start_date, end_date):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT
            direction,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE outcome = 'WIN') AS wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') AS losses
        FROM tracker.trades
        WHERE trade_date::date BETWEEN %s AND %s
          AND outcome IS NOT NULL
        GROUP BY direction
        ORDER BY direction
        """,
        (start_date, end_date)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def close_trade(trade_id, outcome, exit_price):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tracker.trades
        SET outcome = %s,
            exit_price = %s
        WHERE id = %s
        """,
        (outcome, exit_price if exit_price > 0 else None, trade_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def update_trade(trade_id, entry_price, exit_price, outcome, notes):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tracker.trades
        SET entry_price = %s,
            exit_price = %s,
            outcome = %s,
            notes = %s
        WHERE id = %s
        """,
        (
            entry_price,
            exit_price if exit_price > 0 else None,
            outcome,
            notes,
            trade_id
        )
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_trade(trade_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM tracker.trades WHERE id = %s",
        (trade_id,)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_stats_for_setups(start_date, end_date, setups):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE outcome = 'WIN') AS wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') AS losses
        FROM tracker.trades
        WHERE trade_date::date BETWEEN %s AND %s
          AND outcome IS NOT NULL
          AND setup = ANY(%s::setup_type[])
        """,
        (start_date, end_date, setups)
    )

    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_direction_stats_for_setups(start_date, end_date, setups):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT
            direction,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE outcome = 'WIN') AS wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') AS losses
        FROM tracker.trades
        WHERE trade_date::date BETWEEN %s AND %s
          AND outcome IS NOT NULL
          AND setup = ANY(%s::setup_type[])
        GROUP BY direction
        ORDER BY direction
        """,
        (start_date, end_date, setups)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows




# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Trading Journal", layout="wide")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("📓 Trading Journal")
page = st.sidebar.radio("Navigation", ["Journal", "Statistics"])

# -----------------------------
# Journal Page
# -----------------------------
if page == "Journal":
    st.header("📝 Trading Journal")

    # ---- Session state init ----
    today = date.today()

    if "selected_date" not in st.session_state:
        st.session_state.selected_date = today

    if "cal_year" not in st.session_state:
        st.session_state.cal_year = today.year
    if "cal_month" not in st.session_state:
        st.session_state.cal_month = today.month

    st.subheader("📅 Monthly Overview")

    # ---- Month navigation ----
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("◀ Prev", key="prev_month"):
            if st.session_state.cal_month == 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            else:
                st.session_state.cal_month -= 1
            st.rerun()

    with col2:
        month_name = datetime(
            st.session_state.cal_year,
            st.session_state.cal_month,
            1
        ).strftime("%B %Y")
        st.markdown(f"<h4 style='text-align:center'>{month_name}</h4>", unsafe_allow_html=True)

    with col3:
        if st.button("Next ▶", key="next_month"):
            if st.session_state.cal_month == 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.rerun()

    # ---- Load month outcomes AFTER nav ----
    day_outcomes = get_day_outcomes_for_month(st.session_state.cal_year, st.session_state.cal_month)

    # ---- Calendar grid ----
    month_matrix = get_month_matrix(st.session_state.cal_year, st.session_state.cal_month)

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, wd in enumerate(weekdays):
        header_cols[i].markdown(f"**{wd}**")

    for week in month_matrix:
        cols = st.columns(7)
        for i, day in enumerate(week):
            is_current_month = (day.month == st.session_state.cal_month)
            is_selected = (day == st.session_state.selected_date)

            outcome = day_outcomes.get(day)

            bg_color = "#2b2b2b"     # base dark for "not current month"
            txt_color = "#777777"

            if is_current_month:
                bg_color = "#3a3a3a"  # neutral current-month day
                txt_color = "#ffffff"

                if outcome == "green":
                    bg_color = "#1f7a3f"
                elif outcome == "red":
                    bg_color = "#8a2d2d"
                elif outcome == "gray":
                    bg_color = "#555555"

            if is_selected:
                border = "2px solid #1f77ff"
            else:
                border = "1px solid #444"

            # Day button (no extra "select" buttons)
            with cols[i]:
                label = str(day.day)
                if is_selected:
                    label = f"🔵 {label}"

                st.markdown(
                    f"""
                    <div style="
                        background-color:{bg_color};
                        color:{txt_color};
                        border:{border};
                        border-radius:8px;
                        padding:10px;
                        text-align:center;
                        font-weight:600;
                        margin-bottom:6px;
                    ">
                        {label}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(
                    "Open",
                    key=f"open_{day.isoformat()}",
                    disabled=not is_current_month
                ):
                    st.session_state.selected_date = day
                    st.rerun()

    st.divider()

    # ---- Day journal ----
    st.subheader(f"📅 Journal for {st.session_state.selected_date}")
    
    stats = get_day_stats(st.session_state.selected_date)

    if stats["total"] > 0:
        win_rate = (stats["wins"] / stats["total"]) * 100 if stats["total"] else 0

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Trades", stats["total"])
        c2.metric("Wins", stats["wins"])
        c3.metric("Losses", stats["losses"])
        c4.metric("Win Rate", f"{win_rate:.1f}%")
    else:
        st.info("No stats for this day yet.")

 
    trades = get_trades_by_date(st.session_state.selected_date)

    open_trades = [t for t in trades if t["outcome"] is None]
    closed_trades = [t for t in trades if t["outcome"] is not None]

    if open_trades:
        st.markdown("### 🔓 Open Trades")
        for t in open_trades:
            with st.container(border=True):
                st.markdown(
                    f"""
                    **{t['symbol']} | {t['direction']} | Setup {t['setup']}**  
                    Entry: `{t['entry_price']}`  
                    Notes: {t['notes'] or '_none_'}
                    """
                )
                c1, c2, c3 = st.columns(3)

                with c1:
                    outcome = st.selectbox(
                        "Outcome",
                        ["WIN", "LOSS", "BREAKEVEN"],
                        key=f"outcome_{t['id']}"
                    )

                with c2:
                    exit_price = st.number_input(
                        "Exit Price",
                        step=0.0001,
                        key=f"exit_{t['id']}"
                    )

                with c3:
                    if st.button(
                        "🔒 Close Trade",
                        key=f"close_{t['id']}"
                    ):
                        close_trade(t["id"], outcome, exit_price)
                        st.success(f"Trade #{t['id']} closed as {outcome}")
                        st.rerun()

    if closed_trades:
        st.markdown("### 🔒 Closed Trades")
        for t in closed_trades:
            with st.container(border=True):
                st.markdown(
                    f"""
                    **{t['symbol']} | {t['direction']} | Setup {t['setup']}**  
                    Entry: `{t['entry_price']}`  
                    Exit: `{t['exit_price'] or '-'}`
                    Outcome: `{t['outcome']}`  
                    """
                )

                with st.expander("✏️ Edit / Delete"):
                    entry_price = st.number_input(
                        "Entry Price",
                        value=float(t["entry_price"]) if t["entry_price"] is not None else 0.0,
                        step=0.0001,
                        key=f"edit_entry_{t['id']}"
                    )

                    exit_price = st.number_input(
                        "Exit Price",
                        value=float(t["exit_price"] or 0),
                        step=0.0001,
                        key=f"edit_exit_{t['id']}"
                    )

                    outcome = st.selectbox(
                        "Outcome",
                        ["WIN", "LOSS", "BREAKEVEN"],
                        index=["WIN", "LOSS", "BREAKEVEN"].index(t["outcome"]),
                        key=f"edit_outcome_{t['id']}"
                    )

                    notes = st.text_area(
                        "Notes",
                        value=t["notes"] or "",
                        key=f"edit_notes_{t['id']}"
                    )

                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button(
                            "💾 Save Changes",
                            key=f"save_{t['id']}"
                        ):
                            update_trade(
                                t["id"],
                                entry_price,
                                exit_price,
                                outcome,
                                notes
                            )
                            st.success("Trade updated")
                            st.rerun()

                    with c2:
                        if st.button(
                            "🗑 Delete Trade",
                            key=f"delete_{t['id']}"
                        ):
                            st.session_state[f"confirm_delete_{t['id']}"] = True

                    if st.session_state.get(f"confirm_delete_{t['id']}"):
                        st.warning("⚠️ Confirm delete?")
                        if st.button(
                            "YES, DELETE",
                            key=f"confirm_yes_{t['id']}"
                        ):
                            delete_trade(t["id"])
                            st.success("Trade deleted")
                            st.rerun()
                    

    if not trades:
        st.info("No trades for this day.")

    st.divider()

    # ---- Add trade ----
    st.subheader("➕ Add Trade")

    with st.form("add_trade"):
        symbol = st.text_input("Symbol", value="EURUSD")
        direction = st.selectbox("Direction", ["LONG", "SHORT"])
        setup = st.selectbox("Setup", ["A", "B", "C"])
        entry_price = st.number_input("Entry Price", step=0.0001, format="%.5f")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Trade")

        if submitted:
            insert_trade(
                trade_date=st.session_state.selected_date,
                symbol=symbol,
                direction=direction,
                setup=setup,
                entry_price=entry_price,
                notes=notes
            )
            st.success("Trade added ✅")
            st.rerun()

# -----------------------------
# Statistics Page
# -----------------------------
else:
    st.header("📊 Statistics")

    # ---- Date range ----
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start date",
            value=date.today().replace(day=1)
        )

    with col2:
        end_date = st.date_input(
            "End date",
            value=date.today()
        )

    st.divider()

    # ---- Setup selector ----
    selected_setups = st.multiselect(
        "Select setups",
        options=["A", "B", "C"],
        default=["A", "B", "C"]
    )

    if not selected_setups:
        st.info("Select at least one setup.")
        st.stop()

    # ---- Overall stats for selected setups ----
    stats = get_stats_for_setups(start_date, end_date, selected_setups)

    if not stats or stats["total"] == 0:
        st.info("No closed trades for this selection.")
        st.stop()

    win_rate = (stats["wins"] / stats["total"]) * 100 if stats["total"] else 0

    st.subheader("📈 Overall Performance")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Setups", ", ".join(selected_setups))
    c2.metric("Trades", stats["total"])
    c3.metric("Wins", stats["wins"])
    c4.metric("Win Rate", f"{win_rate:.1f}%")

    st.divider()

    # ---- Direction breakdown (filtered by setups) ----
    st.subheader("📐 Direction Breakdown")

    direction_stats = get_direction_stats_for_setups(
        start_date,
        end_date,
        selected_setups
    )

    for row in direction_stats:
        dir_win_rate = (
            (row["wins"] / row["total"]) * 100
            if row["total"] else 0
        )

        with st.container(border=True):
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Direction", row["direction"])
            d2.metric("Trades", row["total"])
            d3.metric("Wins", row["wins"])
            d4.metric("Win Rate", f"{dir_win_rate:.1f}%")


