#!/usr/bin/env python3

import tkinter as tk
import json
import hashlib
import os
from datetime import datetime, date
from tkinter import simpledialog, messagebox

APP_FOLDER = os.path.join(os.path.expanduser("~"), ".local", "share", "taskmaster")
TASKS_FILE = os.path.join(APP_FOLDER, "tasks.json")
os.makedirs(APP_FOLDER, exist_ok=True)

tasks = []
completed_tasks = 0
drag_start_index = None
SALT_SIZE = 16
MASTER_PASSWORD = "generic_password"

def add_task_notes(description):
    window = tk.Toplevel(root)
    window.title("Task Details")
    window.geometry("400x320")

    window.transient(root)
    window.grab_set()
    window.focus_set()

    tk.Label(window, text="Date:", font=("Arial", 12)).grid(row=0, column=0, sticky="e", padx=10, pady=8)
    date_entry = tk.Entry(window, font=("Arial", 12))
    date_entry.grid(row=0, column=1, padx=10, pady=8)
    date_entry.focus_set()

    tk.Label(window, text="Time:", font=("Arial", 12)).grid(row=1, column=0, sticky="e", padx=10, pady=8)
    time_entry = tk.Entry(window, font=("Arial", 12))
    time_entry.grid(row=1, column=1, padx=10, pady=8)

    tk.Label(window, text="Notes:", font=("Arial", 12)).grid(row=2, column=0, sticky="ne", padx=10, pady=8)

    notes_frame = tk.Frame(window)
    notes_frame.grid(row=2, column=1, padx=10, pady=8)

    notes_text = tk.Text(notes_frame, font=("Arial", 12), width=25, height=5)
    notes_text.pack(side="left", fill="both", expand=True)

    notes_scrollbar = tk.Scrollbar(notes_frame, command=notes_text.yview)
    notes_scrollbar.pack(side="right", fill="y")

    notes_text.config(yscrollcommand=notes_scrollbar.set)

    def submit(event=None):
        date_text = date_entry.get().strip()
        time_text = time_entry.get().strip()

        if date_text == "":
            due_date_text = ""
        else:
            try:
                due_date = datetime.strptime(date_text, "%m-%d-%Y").date()
                due_date_text = due_date.isoformat()

            except ValueError:
                messagebox.showerror(
                    "Invalid Date",
                    "Please enter the date in this format:\n\n"
                    "Date: MM-DD-YYYY\n"
                    "Example: 05-11-2026",
                    parent=window
                )
                return

        if time_text == "":
            due_time_text = ""
        else:
            try:
                due_time = datetime.strptime(time_text, "%I:%M %p").time()
                due_time_text = due_time.isoformat()

            except ValueError:
                messagebox.showerror(
                    "Invalid Time",
                    "Please enter the time in this format:\n\n"
                    "Time: HH:MM AM/PM\n"
                    "Example: 04:30 PM",
                    parent=window
                )
                return

        task = {
            "description": description,
            "date": due_date_text,
            "time": due_time_text,
            "notes": notes_text.get("1.0", tk.END).strip()
        }

        tasks.append(task)
        task_listbox.insert(tk.END, description)
        save_tasks()
        task_entry.delete(0, tk.END)
        window.destroy()

    submit_button = tk.Button(window, text="Create Task", font=("Arial", 12), command=submit)
    submit_button.grid(row=3, column=1, pady=15)

    window.bind("<Return>", submit)

def add_task(event=None):
    description = task_entry.get()

    if description == "":
        return

    add_task_notes(description)

def create_key(password, salt):
    password_bytes = password.encode()
    combined = password_bytes + salt
    key = hashlib.sha256(combined).digest()

    return key

def delete_task(event=None):
    selected = task_listbox.curselection()

    if selected == ():
        return

    index = selected[0]

    task_listbox.delete(index)
    tasks.pop(index)
    save_tasks()

def drag_task(event):
    global drag_start_index

    new_index = task_listbox.nearest(event.y)

    if drag_start_index is None:
        return

    if new_index == drag_start_index:
        return

    task = tasks.pop(drag_start_index)
    tasks.insert(new_index, task)

    refresh_listbox()
    task_listbox.selection_set(new_index)

    drag_start_index = new_index

def format_time_12_hour(task_time):
    if task_time == "":
        return ""

    try:
        time_object = datetime.strptime(task_time, "%H:%M")
    except ValueError:
        time_object = datetime.strptime(task_time, "%H:%M:%S")

    return time_object.strftime("%I:%M %p").lstrip("0")

def load_encrypted_data(filename, password):
    with open(filename, "rb") as file:
        file_data = file.read()

    salt = file_data[:SALT_SIZE]
    encrypted_bytes = file_data[SALT_SIZE:]

    key = create_key(password, salt)

    decrypted_bytes = xor_data(encrypted_bytes, key)
    json_text = decrypted_bytes.decode()

    data = json.loads(json_text)

    return data

def load_tasks():
    global tasks
    global completed_tasks

    try:
        data = load_encrypted_data(TASKS_FILE, MASTER_PASSWORD)

        tasks = data.get("tasks", [])
        completed_tasks = data.get("completed_tasks", 0)

        for task in tasks:
            task_listbox.insert(tk.END, task.get("description", ""))

    except FileNotFoundError:
        tasks = []
        completed_tasks = 0

    except UnicodeDecodeError:
        tasks = []
        completed_tasks = 0
        print("Could not decrypt file. Wrong password or corrupted file.")

    except json.JSONDecodeError:
        tasks = []
        completed_tasks = 0
        print("Could not load JSON. Wrong password or corrupted file.")

def mark_completed():
    global completed_tasks

    selected = task_listbox.curselection()

    if selected == ():
        return

    index = selected[0]

    task_listbox.delete(index)
    tasks.pop(index)

    completed_tasks += 1

    save_tasks()
    update_counter()

def open_task_notes(event=None):
    selected = task_listbox.curselection()

    if selected == ():
        return

    index = selected[0]
    task = tasks[index]

    window = tk.Toplevel(root)
    window.title("Edit Task Notes")
    window.geometry("430x360")

    window.transient(root)
    window.wait_visibility()
    window.focus_set()
    window.grab_set()

    tk.Label(window, text="Task:", font=("Arial", 12)).grid(
        row=0, column=0, sticky="e", padx=10, pady=8
    )

    description_entry = tk.Entry(window, font=("Arial", 12), width=28)
    description_entry.grid(row=0, column=1, padx=10, pady=8)
    description_entry.insert(0, task.get("description", ""))

    tk.Label(window, text="Date:", font=("Arial", 12)).grid(
        row=1, column=0, sticky="e", padx=10, pady=8
    )

    date_entry = tk.Entry(window, font=("Arial", 12), width=28)
    date_entry.grid(row=1, column=1, padx=10, pady=8)

    tk.Label(window, text="Time:", font=("Arial", 12)).grid(
        row=2, column=0, sticky="e", padx=10, pady=8
    )

    time_entry = tk.Entry(window, font=("Arial", 12), width=28)
    time_entry.grid(row=2, column=1, padx=10, pady=8)

    date_text = task.get("date", "")
    time_text = task.get("time", "")

    if date_text != "":
        due_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        date_entry.insert(0, due_date.strftime("%m-%d-%Y"))

    if time_text != "":
        due_time = datetime.strptime(time_text, "%H:%M:%S").time()
        time_entry.insert(0, due_time.strftime("%I:%M %p"))

    tk.Label(window, text="Notes:", font=("Arial", 12)).grid(
        row=3, column=0, sticky="ne", padx=10, pady=8
    )

    notes_frame = tk.Frame(window)
    notes_frame.grid(row=3, column=1, padx=10, pady=8)

    notes_text = tk.Text(notes_frame, font=("Arial", 12), width=25, height=6)
    notes_text.pack(side="left", fill="both", expand=True)

    notes_scrollbar = tk.Scrollbar(notes_frame, command=notes_text.yview)
    notes_scrollbar.pack(side="right", fill="y")

    notes_text.config(yscrollcommand=notes_scrollbar.set)
    notes_text.insert("1.0", task.get("notes", ""))

    def save_changes(event=None):
        date_text = date_entry.get().strip()
        time_text = time_entry.get().strip()

        if date_text == "":
            due_date_text = ""
        else:
            try:
                due_date = datetime.strptime(date_text, "%m-%d-%Y").date()
                due_date_text = due_date.isoformat()

            except ValueError:
                messagebox.showerror(
                    "Invalid Date",
                    "Please enter the date in this format:\n\n"
                    "Date: MM-DD-YYYY\n"
                    "Example: 05-11-2026",
                    parent=window
                )
                return

        if time_text == "":
            due_time_text = ""
        else:
            try:
                due_time = datetime.strptime(time_text, "%I:%M %p").time()
                due_time_text = due_time.isoformat()

            except ValueError:
                messagebox.showerror(
                    "Invalid Time",
                    "Please enter the time in this format:\n\n"
                    "Time: HH:MM AM/PM\n"
                    "Example: 04:30 PM",
                    parent=window
                )
                return

        task["description"] = description_entry.get()
        task["date"] = due_date_text
        task["time"] = due_time_text
        task["notes"] = notes_text.get("1.0", tk.END).strip()

        refresh_listbox()
        task_listbox.selection_set(index)

        save_tasks()
        window.destroy()

    save_button = tk.Button(
        window,
        text="Save Changes",
        font=("Arial", 12),
        command=save_changes
    )
    save_button.grid(row=4, column=1, pady=15)

    window.bind("<Return>", save_changes)

def refresh_listbox():
    task_listbox.delete(0, tk.END)

    for task in tasks:
        task_listbox.insert(tk.END, task["description"])

def save_encrypted_data(data, filename, password):
    json_text = json.dumps(data)
    json_bytes = json_text.encode()

    salt = os.urandom(SALT_SIZE)
    key = create_key(password, salt)

    encrypted_bytes = xor_data(json_bytes, key)

    with open(filename, "wb") as file:
        file.write(salt + encrypted_bytes)

def save_tasks():
    data = {
        "completed_tasks": completed_tasks,
        "tasks": tasks
    }

    save_encrypted_data(data, TASKS_FILE, MASTER_PASSWORD)

def show_tasks_due_today():
    today = date.today().isoformat()

    due_today = []

    for task in tasks:
        task_date = task.get("date", "")

        if task_date == today:
            due_today.append(task)

    if not due_today:
        return

    message = "Tasks due today:\n\n"

    for task in due_today:
        description = task.get("description", "")
        task_time = task.get("time", "")

        if task_time == "":
            message += f"- {description}\n"
        else:
            formatted_time = format_time_12_hour(task_time)
            message += f"- {description} at {formatted_time}\n"

    messagebox.showinfo("Tasks Due Today", message, parent=root)

def show_tasks_due_today_after_root_loads():
    if not root.winfo_viewable():
        root.after(50, show_tasks_due_today_after_root_loads)
        return

    root.lift()
    root.focus_force()
    show_tasks_due_today()

def start_drag(event):
    global drag_start_index

    drag_start_index = task_listbox.nearest(event.y)

def stop_drag(event):
    save_tasks()

def update_counter():
    counter_label.config(text=f"Tasks Completed: {completed_tasks}")

def update_counter_manual():
    global completed_tasks

    new_total = simpledialog.askinteger(
        "Update Completed Tasks",
        "Enter the number you want the running total to be:",
        parent=root
    )

    if new_total is None:
        return

    completed_tasks = new_total

    save_tasks()
    update_counter()

def xor_data(data, key):
    result = bytearray()

    for i in range(len(data)):
        key_index = i % len(key)
        new_byte = data[i] ^ key[key_index]
        result.append(new_byte)

    return bytes(result)

def main():
    global root
    global listbox_frame
    global task_listbox
    global task_scrollbar
    global entry_frame
    global task_entry
    global add_button
    global button_frame
    global delete_button
    global mark_button
    global counter_frame
    global counter_label
    global update_counter_button

    root = tk.Tk()
    root.title("Task Master")
    root.geometry("500x450")
    root.resizable(False, False)

    listbox_frame = tk.Frame(root)
    listbox_frame.pack(pady=10)

    task_listbox = tk.Listbox(listbox_frame, font=("Arial", 14), width=40, height=10)
    task_listbox.pack(side="left", fill="both", expand=True)

    task_scrollbar = tk.Scrollbar(listbox_frame, command=task_listbox.yview)
    task_scrollbar.pack(side="right", fill="y")

    task_listbox.config(yscrollcommand=task_scrollbar.set)
    task_listbox.bind("<Button-1>", start_drag)
    task_listbox.bind("<B1-Motion>", drag_task)
    task_listbox.bind("<ButtonRelease-1>", stop_drag)
    task_listbox.bind("<Double-Button-1>", open_task_notes)
    task_listbox.bind("d", delete_task)

    load_tasks()
    root.after(100, show_tasks_due_today)

    entry_frame = tk.Frame(root)
    entry_frame.pack(pady=10)

    task_entry = tk.Entry(entry_frame, font=("Arial", 14))
    task_entry.pack(side="left", padx=5)

    add_button = tk.Button(entry_frame, text="Add Task", font=("Arial", 12), command=add_task)
    add_button.pack(side="left", padx=5)

    task_entry.bind("<Return>", add_task)
    task_entry.focus_set()

    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)

    delete_button = tk.Button(button_frame, text="Delete Task", font=("Arial", 12), command=delete_task)
    delete_button.pack(side="left", padx=5)

    mark_button = tk.Button(button_frame, text="Mark Completed", font=("Arial", 12), command=mark_completed)
    mark_button.pack(side="left", padx=5)

    counter_frame = tk.Frame(root)
    counter_frame.pack(pady=10)

    counter_label = tk.Label(counter_frame, text=f"Tasks Completed: {completed_tasks}", font=("Arial", 14))
    counter_label.pack(side="left", padx=5)

    update_counter_button = tk.Button(counter_frame, text="Update", font=("Arial", 12), command=update_counter_manual)
    update_counter_button.pack(side="left", padx=5)

    show_tasks_due_today_after_root_loads()

    root.mainloop()

if __name__ == "__main__":
    main()
