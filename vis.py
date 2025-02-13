# vis.py

import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def visualiser():
    HISTORY_FILE = "history.json"

    if not os.path.exists(HISTORY_FILE):
        print(f"File '{HISTORY_FILE}' not found.")
        return

    with open(HISTORY_FILE, "r") as f:
        try:
            events = json.load(f)
        except json.JSONDecodeError:
            print("Error: The file is not valid JSON.")
            return

    if not events:
        print("No events found in history.")
        return

    # Sort events by timestamp.
    events.sort(key=lambda e: e.get("timestamp"))

    def parse_event(event):
        """Convert an event's timestamp to a datetime, fixing non-padded hour if necessary."""
        ts = event["timestamp"]
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            # If the hour is not zero-padded, fix it.
            try:
                date_part, time_part = ts.split("T")
                if len(time_part) > 0 and time_part[1] == ":":
                    time_part = "0" + time_part
                fixed_ts = f"{date_part}T{time_part}"
                return datetime.fromisoformat(fixed_ts)
            except Exception as e:
                print("Error parsing timestamp:", ts)
                raise e

    def day_end(dt):
        """Return midnight (the start of the next day) for the given datetime dt."""
        return datetime.combine(dt.date() + timedelta(days=1), datetime.min.time())

    # --- Build Sessions ---
    # Each session is built from one event (using its stored color) to the next.
    # The session tuple is (start, end, project, color).
    sessions = []
    for i in range(len(events) - 1):
        current = parse_event(events[i])
        next_event = parse_event(events[i+1])
        project = events[i].get("project", "Unknown")
        color = events[i].get("color", "#cccccc")
        if current.date() == next_event.date():
            end = next_event
        else:
            end = day_end(current)
        sessions.append((current, end, project, color))

    # For the final event overall, extend its session for just one hour,
    # unless its project name contains 'END_OF_DAY', in which case use zero duration.
    final_event = parse_event(events[-1])
    final_project = events[-1].get("project", "Unknown")
    final_color = events[-1].get("color", "#cccccc")
    if "END_OF_DAY" in final_project:
        final_end = final_event  # zero duration
    else:
        final_end = final_event + timedelta(hours=1)
    sessions.append((final_event, final_end, final_project, final_color))

    def split_session_by_day(start, end, project, color):
        """
        Splits a session into parts that do not span midnight.
        Returns a list of (start, end, project, color) tuples.
        """
        splits = []
        current = start
        while current.date() < end.date():
            next_midnight = datetime.combine(current.date() + timedelta(days=1), datetime.min.time())
            splits.append((current, next_midnight, project, color))
            current = next_midnight
        if current < end:
            splits.append((current, end, project, color))
        return splits

    # --- Split Sessions That Cross Midnight ---
    sessions_split = []
    for start, end, project, color in sessions:
        if start.date() == end.date():
            sessions_split.append((start, end, project, color))
        else:
            sessions_split.extend(split_session_by_day(start, end, project, color))

    # --- Group Sessions By Day ---
    sessions_by_day = {}
    for start, end, project, color in sessions_split:
        day_str = start.date().isoformat()
        sessions_by_day.setdefault(day_str, []).append((start, end, project, color))

    # Sorted list of days (each becomes a column).
    days = sorted(sessions_by_day.keys())

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(16, 10))

    for i, day in enumerate(days):
        for start, end, project, color in sessions_by_day[day]:
            # Compute the start time in hours from midnight.
            start_hour = start.hour + start.minute/60 + start.second/3600
            # If the session was extended past midnight, treat its end as 24.0.
            if end.date() != start.date():
                end_hour = 24.0
            else:
                end_hour = end.hour + end.minute/60 + end.second/3600
            duration = end_hour - start_hour
            rect = Rectangle((i - 0.4, start_hour), 0.8, duration,
                             facecolor=color, edgecolor="black", alpha=0.7)
            ax.add_patch(rect)
            # Add a label if the rectangle is tall enough.
            if duration >= 0.2:
                ax.text(i, start_hour + duration/2, project,
                        ha="center", va="center", fontsize=9, color="black")
            # If any portion of the booking extends past 7 PM (19.0), draw an outline on that part.
            if end_hour > 19:
                outline_start = max(start_hour, 19)
                outline_duration = end_hour - outline_start
                outline_rect = Rectangle((i - 0.4, outline_start), 0.8, outline_duration,
                                         facecolor="none", edgecolor="red", linewidth=2)
                ax.add_patch(outline_rect)

    # Configure x-axis (one column per day).
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(days, rotation=45, ha="right")
    ax.set_xlim(-0.5, len(days)-0.5)
    ax.set_xlabel("Day")

    # Configure y-axis (0 to 24 hours) and reverse the order.
    ax.set_ylim(24, 0)
    ax.set_ylabel("Time of Day")
    ax.set_title("Timesheet Visualisation")

    # Y-axis ticks every 30 minutes.
    y_ticks = [i/2 for i in range(0, 49)]
    def format_time(hour_float):
        total_minutes = int(round(hour_float * 60))
        if total_minutes >= 1440:
            return "12:00 AM"
        dt_temp = datetime(2000, 1, 1, total_minutes // 60, total_minutes % 60)
        return dt_temp.strftime("%I:%M %p").lstrip("0")
    y_labels = [format_time(t) for t in y_ticks]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)

    ax.grid(True, axis="y", linestyle="--", alpha=0.7)
    fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)

    plt.show()



