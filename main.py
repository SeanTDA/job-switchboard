import tkinter as tk
from tkinter import colorchooser
import json
import os
from datetime import datetime
import hashlib, colorsys
import math

# --- Unique Color Generation ---
project_color_cache = {}

def get_color(project_name):
    """
    Generate a unique color for each project based on its name.
    Uses MD5 to compute a hash, then converts a portion of the hash into an HSV color.
    """
    if project_name in project_color_cache:
        return project_color_cache[project_name]
    hash_val = int(hashlib.md5(project_name.encode()).hexdigest(), 16)
    hue = (hash_val % 360) / 360.0
    saturation = 0.6
    value = 0.9
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    project_color_cache[project_name] = (r, g, b)
    return (r, g, b)

def rgb_to_hex(rgb):
    """Convert an (r, g, b) tuple to a hex color string."""
    return '#{0:02x}{1:02x}{2:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

def get_contrasting_text_color(bg_hex):
    """Return white or black text depending on the brightness of the background color."""
    r = int(bg_hex[1:3], 16)
    g = int(bg_hex[3:5], 16)
    b = int(bg_hex[5:7], 16)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "white" if brightness < 128 else "black"

# --- History Logging Setup ---
LOG_FILE = "history.json"
if os.path.exists(LOG_FILE):
    try:
        with open(LOG_FILE, "r") as f:
            history = json.load(f)
    except json.JSONDecodeError:
        history = []
else:
    history = []

def save_history():
    """Save the switch history to a JSON file."""
    with open(LOG_FILE, "w") as f:
        json.dump(history, f, indent=4)

# --- Project Switching ---
current_project = None
project_start_time = None  # Records the time when the current project was started

def switch_project(project, color_override=None):
    """Switch projects and log the switch event if it's a change."""
    global current_project, project_start_time
    if project == current_project:
        return
    current_project = project
    project_start_time = datetime.now()  # Record the start time for this project

    if project == "END_OF_DAY":
        color = "#ff6666"  # a slightly brighter red for visibility on dark bg
    elif color_override:
        color = color_override
    else:
        color = rgb_to_hex(get_color(project))
    event = {
        "timestamp": datetime.now().isoformat(),
        "project": project,
        "color": color
    }
    history.append(event)
    save_history()
    status_label.config(text=f"Current project: {project}")

def end_day():
    """Log the END_OF_DAY event and quit the application."""
    switch_project("END_OF_DAY")
    root.destroy()

# --- Jobs File Setup ---
JOBS_FILE = "jobs.json"

def load_jobs():
    default_job_list = [{"name": "Job1", "color": rgb_to_hex(get_color("Job1"))},
                        {"name": "Job2", "color": rgb_to_hex(get_color("Job2"))}]
    """
    Load the list of jobs from jobs.json.
    Each job is a dict with keys "name" and "color".
    If the file is missing or invalid, return a default list.
    """
    if os.path.exists(JOBS_FILE):
        try:
            jobs = json.load(open(JOBS_FILE))
            new_jobs = []
            for j in jobs:
                if isinstance(j, dict) and "name" in j and "color" in j:
                    new_jobs.append(j)
                elif isinstance(j, str):
                    new_jobs.append({"name": j, "color": rgb_to_hex(get_color(j))})
            return new_jobs if new_jobs else default_job_list
        except json.JSONDecodeError:
            return default_job_list
    else:
        return default_job_list

def save_jobs(jobs):
    """Save the list of job dictionaries to jobs.json."""
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=4)

def update_job_buttons():
    """Clear and repopulate the grid of job buttons based on the current jobs list."""
    for widget in job_frame.winfo_children():
        widget.destroy()
    jobs = load_jobs()
    num_jobs = len(jobs)
    
    # Determine the number of columns based on the square root of the number of jobs.
    cols = math.ceil(math.sqrt(num_jobs)) if num_jobs > 0 else 1
    rows_count = math.ceil(num_jobs / cols)
    
    # Configure grid weights so buttons expand equally.
    for r in range(rows_count):
        job_frame.rowconfigure(r, weight=1)
    for c in range(cols):
        job_frame.columnconfigure(c, weight=1)
    
    for i, job in enumerate(jobs):
        row = i // cols
        col = i % cols
        fg_color = get_contrasting_text_color(job["color"])
        btn = tk.Button(job_frame, text=job["name"], font=("Helvetica", 16),
                        bg=job["color"], fg=fg_color,
                        command=lambda j=job: switch_project(j["name"], j["color"]))
        btn.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

# --- Edit Jobs Window with Color Chooser, Add & Remove ---
def edit_jobs():
    """Open a window to add, remove, and edit jobs (name and color)."""
    jobs = load_jobs()
    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Jobs")
    edit_window.attributes("-topmost", True)
    edit_window.configure(bg="#2e2e2e")
    
    rows = []  # Each row is a dict with keys: "frame", "name_entry", "color_button"
    
    # Create a dedicated frame for the job rows.
    rows_frame = tk.Frame(edit_window, bg="#2e2e2e")
    rows_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def add_job_row(job_name="", job_color=""):
        # Add rows to the rows_frame.
        row_frame = tk.Frame(rows_frame, bg="#2e2e2e")
        name_entry = tk.Entry(row_frame, font=("Helvetica", 12), bg="#555555", fg="white", insertbackground="white")
        name_entry.insert(0, job_name)
        name_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        
        # If no color provided, assign a default dynamic color.
        if not job_color:
            job_color = rgb_to_hex(get_color(job_name)) if job_name else "#777777"
        
        # Create a color button.
        color_button = tk.Button(row_frame, text="Color", font=("Helvetica", 10),
                                 bg=job_color, fg=get_contrasting_text_color(job_color), width=6,
                                 command=lambda: choose_color(color_button))
        color_button.pack(side="left", padx=5)
        
        remove_button = tk.Button(row_frame, text="Remove", font=("Helvetica", 10),
                                  bg="#aa2222", fg="white",
                                  command=lambda: remove_job_row(row_frame))
        remove_button.pack(side="left", padx=5)
        
        row_frame.pack(fill="x", pady=2)
        rows.append({"frame": row_frame, "name_entry": name_entry, "color_button": color_button})
    
    def choose_color(btn):
        """Open the color chooser with edit_window as parent and update the button's background."""
        chosen = colorchooser.askcolor(initialcolor=btn.cget("bg"), title="Choose Color", parent=edit_window)
        if chosen[1] is not None:
            btn.config(bg=chosen[1], fg=get_contrasting_text_color(chosen[1]))
    
    def remove_job_row(frame):
        for i, row in enumerate(rows):
            if row["frame"] == frame:
                row["frame"].destroy()
                rows.pop(i)
                break
    
    # Create a row for each current job.
    for job in jobs:
        add_job_row(job["name"], job["color"])
    
    # Create a frame for the buttons so they always stay below the job rows.
    buttons_frame = tk.Frame(edit_window, bg="#2e2e2e")
    buttons_frame.pack(pady=10)
    
    add_button = tk.Button(buttons_frame, text="Add Job", font=("Helvetica", 12),
                           bg="#444444", fg="white", 
                           command=lambda: add_job_row("New Job", rgb_to_hex(get_color("New Job"))))
    add_button.pack(pady=(0, 10))  # Adds spacing below the Add Job button
    
    def save_edits():
        new_jobs = []
        for row in rows:
            name = row["name_entry"].get().strip()
            # Get the color from the color button's background.
            color = row["color_button"].cget("bg")
            if name:
                new_jobs.append({"name": name, "color": color})
        if not new_jobs:
            new_jobs = [{"name": "Falcon", "color": rgb_to_hex(get_color("Falcon"))},
                        {"name": "Toyota", "color": rgb_to_hex(get_color("Toyota"))}]
        save_jobs(new_jobs)
        update_job_buttons()
        edit_window.destroy()
    
    save_button = tk.Button(buttons_frame, text="Save", font=("Helvetica", 12), 
                            bg="green", fg="white", command=save_edits)
    save_button.pack()

# --- Set up the Main Window with a Grid Layout ---
root = tk.Tk()
root.title("Project Dashboard")
root.geometry("600x400")
root.configure(bg="#2e2e2e")

# Create a main container frame that fills the window.
main_frame = tk.Frame(root, bg="#2e2e2e")
main_frame.pack(expand=True, fill="both")

# Configure the grid: three rows (header, jobs, controls) and one column.
main_frame.rowconfigure(0, weight=0)  # Header (does not expand vertically)
main_frame.rowconfigure(1, weight=1)  # Jobs area (expands)
main_frame.rowconfigure(2, weight=0)  # Control row (buttons)
main_frame.columnconfigure(0, weight=1)

# Header Frame for status and details
header_frame = tk.Frame(main_frame, bg="#2e2e2e")
header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
header_frame.columnconfigure(0, weight=1)

status_label = tk.Label(header_frame, text="No project selected", font=("Helvetica", 16),
                        bg="#2e2e2e", fg="white")
status_label.grid(row=0, column=0, sticky="w")

details_label = tk.Label(header_frame, text="", font=("Helvetica", 12),
                         bg="#2e2e2e", fg="white")
details_label.grid(row=1, column=0, sticky="w")

# Job Frame for the grid of job buttons
job_frame = tk.Frame(main_frame, bg="#2e2e2e")
job_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

update_job_buttons()

# Control Frame for the bottom buttons
control_frame = tk.Frame(main_frame, bg="#2e2e2e")
control_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
control_frame.columnconfigure(0, weight=1)
control_frame.columnconfigure(1, weight=1)

edit_button = tk.Button(control_frame, text="Edit", font=("Helvetica", 10),
                        bg="#444444", fg="white", command=edit_jobs)
edit_button.grid(row=0, column=0, sticky="w")

end_day_button = tk.Button(control_frame, text="End Day", font=("Helvetica", 10),
                           bg="#aa2222", fg="white", command=end_day)
end_day_button.grid(row=0, column=1, sticky="e")

# --- Check history on startup and restore the last project if not "END_OF_DAY" ---
if history and history[-1]["project"] != "END_OF_DAY":
    last_event = history[-1]
    current_project = last_event["project"]
    try:
        project_start_time = datetime.fromisoformat(last_event["timestamp"])
    except ValueError:
        project_start_time = datetime.now()
    status_label.config(text=f"Current project: {current_project}")

# Function to update the start time and duration label in real time.
def update_details():
    if current_project and project_start_time and current_project != "END_OF_DAY":
        start_time_str = project_start_time.strftime("%I:%M%p").lower()
        delta = datetime.now() - project_start_time
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        details = f"Start Time: {start_time_str}\nDuration: {hours}hrs {minutes}mins"
    else:
        details = ""
    details_label.config(text=details)
    root.after(1000, update_details)

# Start updating the details label.
update_details()

# Start the Tkinter event loop.
root.mainloop()
