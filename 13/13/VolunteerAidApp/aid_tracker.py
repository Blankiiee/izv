import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from tkinter import Tk, ttk, StringVar, IntVar, Text, END, messagebox, filedialog
from tkinter import Canvas, Frame, Label, Entry, Button, Scrollbar

DB_PATH = Path(__file__).with_name("aid_tasks.db")


class AidTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AidFlow — Dashboard гуманітарної підтримки")
        self.root.geometry("1200x760")
        self.root.minsize(1000, 620)
        self.root.configure(bg="#0f172a")

        self.editing_id = None
        self.categories = [
            "Медична допомога",
            "Продукти харчування",
            "Транспорт",
            "Психологічна підтримка",
            "Інформаційна допомога",
            "Інше",
        ]

        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_db()

        self.build_ui()
        self.refresh_tasks()

    def init_db(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                due_date TEXT,
                status TEXT NOT NULL DEFAULT 'Планується',
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def build_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=2)
        self.root.grid_rowconfigure(0, weight=1)

        main = Frame(self.root, bg="#0f172a")
        main.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=18, pady=18)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=2)

        left = Frame(main, bg="#111827", padx=18, pady=18)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_rowconfigure(6, weight=1)

        right = Frame(main, bg="#111827", padx=18, pady=18)
        right.grid(row=0, column=1, sticky="nsew", padx=(18, 0))
        right.grid_rowconfigure(1, weight=1)

        header = Frame(left, bg="#111827")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        label_title = Label(
            header,
            text="Новий запит допомоги",
            fg="#f8fafc",
            bg="#111827",
            font=("Segoe UI", 18, "bold"),
        )
        label_title.pack(anchor="w")

        self.title_var = StringVar()
        self.category_var = StringVar(value=self.categories[0])
        self.priority_var = StringVar(value="Середній")
        self.due_var = StringVar()

        form_labels = [
            ("Заголовок", self.title_var, 0),
            ("Категорія", self.category_var, 1),
            ("Пріоритет", self.priority_var, 2),
            ("Термін", self.due_var, 3),
        ]

        for idx, (label_text, var, row_idx) in enumerate(form_labels):
            label = Label(left, text=label_text, fg="#dbeafe", bg="#111827", font=("Segoe UI", 10, "bold"))
            label.grid(row=row_idx + 1, column=0, sticky="w", pady=(0, 6))
            if row_idx == 1:
                widget = ttk.Combobox(left, textvariable=var, values=self.categories, state="readonly", width=30)
                widget.grid(row=row_idx + 1, column=1, sticky="ew", pady=(0, 12))
            elif row_idx == 2:
                widget = ttk.Combobox(left, textvariable=var, values=["Низький", "Середній", "Високий"], state="readonly", width=30)
                widget.grid(row=row_idx + 1, column=1, sticky="ew", pady=(0, 12))
            elif row_idx == 3:
                widget = Entry(left, textvariable=var, width=32, bg="#0b1220", fg="#e2e8f0", insertbackground="#e2e8f0")
                widget.grid(row=row_idx + 1, column=1, sticky="ew", pady=(0, 12))
                var.set(datetime.now().strftime("%Y-%m-%d"))
            else:
                widget = Entry(left, textvariable=var, width=32, bg="#0b1220", fg="#e2e8f0", insertbackground="#e2e8f0")
                widget.grid(row=row_idx + 1, column=1, sticky="ew", pady=(0, 12))

        notes_label = Label(left, text="Коментар", fg="#dbeafe", bg="#111827", font=("Segoe UI", 10, "bold"))
        notes_label.grid(row=5, column=0, sticky="nw", pady=(0, 6))
        self.notes_box = Text(left, width=32, height=7, bg="#0b1220", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.notes_box.grid(row=5, column=1, sticky="nsew")

        buttons = Frame(left, bg="#111827")
        buttons.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)
        buttons.grid_columnconfigure(2, weight=1)
        buttons.grid_columnconfigure(3, weight=1)

        self.save_button = Button(buttons, text="Зберегти", bg="#14b8a6", fg="#ffffff", command=self.save_or_update_task, font=("Segoe UI", 10, "bold"))
        self.save_button.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.clear_button = Button(buttons, text="Очистити", bg="#475569", fg="#ffffff", command=self.clear_form, font=("Segoe UI", 10, "bold"))
        self.clear_button.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        self.toggle_button = Button(buttons, text="Статус", bg="#f59e0b", fg="#ffffff", command=self.toggle_task_status, font=("Segoe UI", 10, "bold"))
        self.toggle_button.grid(row=0, column=2, sticky="ew", padx=(0, 10))

        self.delete_button = Button(buttons, text="Видалити", bg="#ef4444", fg="#ffffff", command=self.delete_selected, font=("Segoe UI", 10, "bold"))
        self.delete_button.grid(row=0, column=3, sticky="ew")

        search_wrap = Frame(right, bg="#111827")
        search_wrap.grid(row=0, column=0, sticky="ew")
        search_wrap.grid_columnconfigure(0, weight=1)
        search_wrap.grid_columnconfigure(1, weight=1)

        self.search_var = StringVar()
        search_label = Label(search_wrap, text="Пошук / фільтр", fg="#dbeafe", bg="#111827", font=("Segoe UI", 10, "bold"))
        search_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        search_entry = Entry(search_wrap, textvariable=self.search_var, bg="#0b1220", fg="#e2e8f0", insertbackground="#e2e8f0")
        search_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        search_entry.bind("<KeyRelease>", lambda event: self.refresh_tasks())

        sort_options = ["За датою", "За пріоритетом", "За категорією", "За статусом"]
        self.sort_var = StringVar(value=sort_options[0])
        sort_combo = ttk.Combobox(search_wrap, textvariable=self.sort_var, values=sort_options, state="readonly", width=25)
        sort_combo.grid(row=1, column=1, sticky="ew")
        sort_combo.bind("<<ComboboxSelected>>", lambda event: self.refresh_tasks())

        self.table_frame = Frame(right, bg="#111827")
        self.table_frame.grid(row=1, column=0, sticky="nsew", pady=(18, 0))
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        columns = ("#1", "title", "category", "priority", "due", "status", "notes")
        self.tree = ttk.Treeview(self.table_frame, columns=("title", "category", "priority", "due", "status", "notes"), show="headings", height=18)
        self.tree.heading("title", text="Назва")
        self.tree.heading("category", text="Категорія")
        self.tree.heading("priority", text="Пріоритет")
        self.tree.heading("due", text="Термін")
        self.tree.heading("status", text="Статус")
        self.tree.heading("notes", text="Коментар")

        self.tree.column("title", width=180, anchor="w")
        self.tree.column("category", width=150, anchor="w")
        self.tree.column("priority", width=110, anchor="center")
        self.tree.column("due", width=100, anchor="center")
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("notes", width=250, anchor="w")

        self.tree.tag_configure("done", background="#1f2937", foreground="#86efac")
        self.tree.tag_configure("active", background="#1f2937", foreground="#f8fafc")
        self.tree.bind("<<TreeviewSelect>>", self.on_select_row)
        self.tree.bind("<Double-Button-1>", self.load_row_for_edit)

        y_scroll = Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        stats_panel = Frame(right, bg="#111827")
        stats_panel.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        stats_panel.grid_columnconfigure(0, weight=1)
        stats_panel.grid_columnconfigure(1, weight=1)
        stats_panel.grid_columnconfigure(2, weight=1)

        self.stats_labels = []
        for idx, text in enumerate(["Усього", "Завершено", "Активні"]):
            box = Frame(stats_panel, bg="#0f172a", padx=12, pady=10)
            box.grid(row=0, column=idx, sticky="ew", padx=(0, 12))
            label_main = Label(box, text=text, fg="#cbd5e1", bg="#0f172a", font=("Segoe UI", 9, "bold"))
            label_main.pack(anchor="w")
            value_label = Label(box, text="0", fg="#f8fafc", bg="#0f172a", font=("Segoe UI", 18, "bold"))
            value_label.pack(anchor="w")
            self.stats_labels.append(value_label)

        chart_title = Label(right, text="Статистика по категоріях", fg="#dbeafe", bg="#111827", font=("Segoe UI", 11, "bold"))
        chart_title.grid(row=3, column=0, sticky="w", pady=(18, 10))

        self.chart_canvas = Canvas(right, width=700, height=180, bg="#111827", highlightthickness=0)
        self.chart_canvas.grid(row=4, column=0, sticky="ew")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_select_row(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item["values"]
        self.editing_id = int(selection[0].replace("task_", ""))
        self.title_var.set(values[0])
        self.category_var.set(values[1])
        self.priority_var.set(values[2])
        self.due_var.set(values[3])
        self.notes_box.delete("1.0", END)
        self.notes_box.insert(END, values[5])

    def load_row_for_edit(self, event=None):
        self.on_select_row(event)

    def clear_form(self):
        self.editing_id = None
        self.title_var.set("")
        self.category_var.set(self.categories[0])
        self.priority_var.set("Середній")
        self.due_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.notes_box.delete("1.0", END)

    def save_or_update_task(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Попередження", "Введіть назву запиту або задачі.")
            return

        category = self.category_var.get()
        priority = self.priority_var.get()
        due_date = self.due_var.get().strip() or datetime.now().strftime("%Y-%m-%d")
        notes = self.notes_box.get("1.0", END).strip()

        if self.editing_id is None:
            self.conn.execute(
                "INSERT INTO tasks (title, category, priority, due_date, status, notes, created_at) VALUES (?, ?, ?, ?, 'Планується', ?, ?)",
                (title, category, priority, due_date, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            self.conn.commit()
            messagebox.showinfo("Готово", "Задача успішно додана.")
        else:
            self.conn.execute(
                "UPDATE tasks SET title=?, category=?, priority=?, due_date=?, notes=? WHERE id=?",
                (title, category, priority, due_date, notes, self.editing_id),
            )
            self.conn.commit()
            messagebox.showinfo("Готово", "Задача оновлена.")

        self.clear_form()
        self.refresh_tasks()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Попередження", "Спочатку виберіть рядок.")
            return

        task_id = int(selected[0].replace("task_", ""))
        if messagebox.askyesno("Підтвердження", "Видалити вибрану задачу?"):
            self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.conn.commit()
            self.clear_form()
            self.refresh_tasks()

    def toggle_task_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Попередження", "Спочатку виберіть рядок.")
            return

        task_id = int(selected[0].replace("task_", ""))
        current_status = self.tree.item(selected[0], "values")[4]
        new_status = "Завершено" if current_status != "Завершено" else "Планується"
        self.conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
        self.conn.commit()
        self.refresh_tasks()

    def refresh_tasks(self):
        query = "SELECT id, title, category, priority, due_date, status, notes FROM tasks"
        conditions = []
        params = []
        search_text = self.search_var.get().strip().lower()
        if search_text:
            conditions.append("LOWER(title) LIKE ? OR LOWER(category) LIKE ? OR LOWER(notes) LIKE ?")
            pattern = f"%{search_text}%"
            params.extend([pattern, pattern, pattern])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        sort_mode = self.sort_var.get()
        if sort_mode == "За датою":
            query += " ORDER BY due_date ASC, priority DESC"
        elif sort_mode == "За пріоритетом":
            query += " ORDER BY CASE priority WHEN 'Високий' THEN 3 WHEN 'Середній' THEN 2 WHEN 'Низький' THEN 1 ELSE 0 END DESC, due_date ASC"
        elif sort_mode == "За категорією":
            query += " ORDER BY category ASC, due_date ASC"
        else:
            query += " ORDER BY CASE status WHEN 'Завершено' THEN 1 ELSE 0 END ASC, due_date ASC"

        rows = self.conn.execute(query, params).fetchall()
        self.tree.delete(*self.tree.get_children())

        for row in rows:
            task_id, title, category, priority, due_date, status, notes = row
            tags = ("done",) if status == "Завершено" else ("active",)
            self.tree.insert("", "end", iid=f"task_{task_id}", values=(title, category, priority, due_date, status, notes), tags=tags)

        self.update_stats()
        self.draw_category_chart()

    def update_stats(self):
        totals = self.conn.execute("SELECT COUNT(*), SUM(CASE WHEN status='Завершено' THEN 1 ELSE 0 END), SUM(CASE WHEN status!='Завершено' THEN 1 ELSE 0 END) FROM tasks").fetchone()
        total, done, active = totals
        values = [total or 0, done or 0, active or 0]
        for value_label, value in zip(self.stats_labels, values):
            value_label.config(text=str(value))

    def draw_category_chart(self):
        rows = self.conn.execute("SELECT category, COUNT(*) FROM tasks GROUP BY category ORDER BY COUNT(*) DESC").fetchall()
        self.chart_canvas.delete("all")
        if not rows:
            self.chart_canvas.create_text(350, 90, text="Немає даних", fill="#cbd5e1", font=("Segoe UI", 14, "bold"))
            return

        max_count = max(count for _, count in rows)
        canvas_w = 700
        canvas_h = 180
        bar_area_w = canvas_w - 120
        x_start = 60
        bar_w = 70
        gap = 20
        for idx, (category, count) in enumerate(rows):
            x = x_start + idx * (bar_w + gap)
            bar_h = (count / max_count) * 100 if max_count else 0
            y = canvas_h - 30 - bar_h
            self.chart_canvas.create_rectangle(x, y, x + bar_w, canvas_h - 30, fill="#22c55e", outline="#86efac")
            self.chart_canvas.create_text(x + bar_w / 2, canvas_h - 10, text=category[:10], fill="#e2e8f0", font=("Segoe UI", 8))
            self.chart_canvas.create_text(x + bar_w / 2, y - 8, text=str(count), fill="#f8fafc", font=("Segoe UI", 8, "bold"))

    def on_close(self):
        self.conn.close()
        self.root.destroy()


def export_tasks_csv():
    # placeholder if needed for future usage, not bound to app
    pass


def main():
    root = Tk()
    app = AidTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
