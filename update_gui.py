import tkinter as tk
from tkinter import ttk, messagebox

from db_logic import *
from form_gui import *
from where_gui import *
from table_gui import * 
from gui_utils import *
from treeview_gui import *
from permissions import can

def launch_update_gui(conn, parent, state):
    print("launch_update_gui")
    # 메인 윈도우
    window = parent
    where_condition_frame_list = [] # 조건절 frame 목록
    
    table_list = get_table_names(conn) # 테이블 목록 가져오기
    selected_table = tk.StringVar() # 선택한 테이블
        
    # 테이블 선택
    def on_table_selected(event):
        print("on_table_selected")
            
        selected = get_selected_listbox_item(listbox_tables)
        if selected:
            selected_table.set(selected)
            entry_table.delete(0, tk.END)
            entry_table.insert(0, selected)
            
            table = selected_table.get()
            if not table:
                return

            for widget in input_frame.winfo_children():
                widget.destroy()
            
            state["entry_columns"] = get_insertable_columns(conn, table)
            state["entry_vars"].clear()
            state["entry_vars"].update(init_entry_vars(state["entry_columns"]))
            generate_input_fields(input_frame, state["entry_columns"], state["entry_vars"], per_row=6, readonly=False)

            # 전체 데이터 가져오기
            pk = get_primary_key(conn, table)
            if not pk:
                result, err = run_custom_select(conn, table, "*", order_clause="", limit_clause="50") # 속도 이슈로 50개만 가져오게 하드 코딩
            else:
                result, err = run_custom_select(conn, table, "*", order_clause=f"{pk} DESC", limit_clause="50") # 속도 이슈로 50개만 가져오게 하드 코딩
            if err:
                messagebox.showerror("에러", err)
                return

            # TreeView 컬럼 재설정
            state["full_columns"] = [desc[0] for desc in result["columns"]]

            # 트리뷰 초기화
            clear_treeview(tree)
            # 트리뷰 업데이트
            update_treeview(tree, result["rows"], state["full_columns"])
            
            # ② 기존 조건 프레임 비우고 새로 생성
            for child in where_condition_frame.winfo_children():
                child.destroy()

            # ✅ 프레임 리스트도 같이 초기화해야 함
            where_condition_frame_list.clear()
            
            # ③ 조건 입력 행 추가
            add_condition_row(where_condition_frame, where_condition_frame_list, state["full_columns"], default=True)
    
    def get_changed_columns(entry_columns, entry_vars, full_row, full_columns):
        print("get_changed_columns")
        changed_cols = [] # 변경한 컬럼
        changed_vals = [] # 변경한 컬럼값

        for col in entry_columns:
            i = full_columns.index(col)
            old_val = str(full_row[i]) if full_row[i] is not None else ""
            new_val = entry_vars[col].get()

            if new_val != old_val:
                changed_cols.append(col)
                changed_vals.append(new_val if new_val != "" else None)

        return changed_cols, changed_vals

    def on_search():
        print("on_search")
        # nonlocal current_columns

        table = selected_table.get()
        if not table:
            return

        # 조건절 구성
        where_clause = build_where_clause(where_condition_frame_list)

        pk = get_primary_key(conn, table)
        result, err = run_custom_select(conn, table, "*", where_clause = where_clause, order_clause=f"{pk} DESC")
        if err:
            messagebox.showerror("검색 실패", err)
            return

        clear_treeview(tree)
        state["full_columns"].clear()
        state["full_columns"].extend([desc[0] for desc in result["columns"]])
        
        update_treeview(tree, result["rows"], state["full_columns"])

    def on_update():
        print("on_update")
        table = selected_table.get()
        if not can(conn, table, "UPDATE"):
            messagebox.showwarning("권한 없음", f"{table} UPDATE 권한이 없습니다.")
            return
        selected_item = tree.focus()

        if not table or not selected_item:
            messagebox.showwarning("선택 오류", "테이블과 행을 선택하세요.")
            return

        selected_row = tree.item(selected_item, "values")
        
        pk_col = get_primary_key(conn, table)  # ✅ 실제 PK 컬럼 확인
        pk_val = selected_row[state["full_columns"].index(pk_col)]  # 정확한 위치에서 추출
        
        changed_cols, changed_vals = get_changed_columns(state["entry_columns"], state["entry_vars"], selected_row, state["full_columns"])
        success, msg = update_changed_columns(conn, table, changed_cols, changed_vals, pk_col, pk_val)
    
        if success:
            messagebox.showinfo("성공", msg)
            on_table_selected(None)  # 새로고침
        else:
            messagebox.showerror("실패", msg)
    
    selection_frame, entry_table, listbox_tables = create_table_selector(window, conn, selected_table, on_table_selected, mode="update")
    
    input_container = tk.Frame(window)
    input_container.pack(fill="x", padx=10, pady=5)
    
    # 여기에만 스크롤 영역 넣기
    input_frame = create_scrollable_input_frame(input_container)  # 높이 제한 가능

    where_frame = tk.Frame(window)
    where_frame.pack(pady=10)
    tk.Label(where_frame, text="WHERE 조건들").pack(anchor="w")

    where_condition_frame = tk.Frame(window)
    where_condition_frame.pack(pady=5)

    tk.Button(window, text="조건 추가", command=lambda: add_condition_row(where_condition_frame, where_condition_frame_list, state["full_columns"])).pack()

    # 하단 버튼 프레임
    button_frame = tk.Frame(window)
    button_frame.pack(pady=10)
    
    # 검색 버튼
    tk.Button(button_frame, text="검색", command=on_search).grid(row=0, column=0, padx=5)
    
    # 수정 버튼
    btn_update = tk.Button(button_frame, text="수정", command=on_update).grid(row=0, column=1, padx=5)
    
    tree, tree_frame = create_treeview_frame(window, state["full_columns"])
    tree_frame.pack(fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", lambda event: on_row_select(tree, state))
