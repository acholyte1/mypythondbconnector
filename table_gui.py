# table_gui.py
import tkinter as tk  # Tkinter 기본 GUI 라이브러리

from db_logic import *  # DB 쿼리 실행 함수
from gui_utils import *

def create_table_selector(parent, conn, selected_table, on_select_callback, mode):
    print("create_table_selector")
    table_list = ""
    if mode == "select":
        table_list = get_table_names(conn)
    else:
        table_list = get_real_tables_only(conn)

    frame = tk.Frame(parent)
    frame.pack(pady=10)

    tk.Label(frame, text="테이블 선택").grid(row=0, column=0, sticky="w")
    entry_table = tk.Entry(frame, textvariable=selected_table)
    entry_table.grid(row=1, column=0, sticky="ew", padx=5)

    listbox_tables = tk.Listbox(frame, height=5, exportselection=False)
    listbox_tables.grid(row=2, column=0, sticky="nsew", padx=5)

    def update_table_list(*args):
        print("update_table_list")
        keyword = entry_table.get().lower()
        filtered = [t for t in table_list if keyword in t.lower()]
        listbox_tables.delete(0, tk.END)
        for t in filtered:
            listbox_tables.insert(tk.END, t)

    def on_table_select(event):
        print("on_table_select")
        selected = get_selected_listbox_item(listbox_tables)
        if selected:
            selected_table.set(selected)
            entry_table.delete(0, tk.END)
            entry_table.insert(0, selected)
            on_select_callback(selected)

    entry_table.bind("<KeyRelease>", update_table_list)
    listbox_tables.bind("<<ListboxSelect>>", on_table_select)

    update_table_list()  # 초기 목록 세팅

    return frame, entry_table, listbox_tables