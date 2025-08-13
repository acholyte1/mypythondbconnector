import tkinter as tk
from tkinter import ttk, messagebox
from db_logic import *  # DB 쿼리 실행 함수
from form_gui import *
from table_gui import *
from gui_utils import *
from treeview_gui import *
from permissions import can

def launch_insert_gui(conn, parent, state):
    print("launch_insert_gui")
    # 메인 윈도우
    window = parent
    
    table_list = get_table_names(conn) # 테이블 목록 가져오기
    selected_table = tk.StringVar() # 선택한 테이블
    
    # 테이블 및 컬럼 정보 불러오기
    try:
        table_columns, tables = fetch_table_columns(conn)
    except Exception as e:
        messagebox.showerror("DB 오류", f"테이블 목록 조회 실패: {e}")

    # 테이블 선택
    def on_table_selected(event):
        print("on_table_select")
        
        # ① 기존 입력 필드 초기화
        for widget in input_frame.winfo_children():
            widget.destroy()

        # ② 새 필드 구성
        table = selected_table.get()
        state["entry_columns"] = get_insertable_columns(conn, table)
            
        # 선택한 컬럼에 맞게 값 설정
        state["entry_vars"].clear()
        state["entry_vars"].update(init_entry_vars(state["entry_columns"]))
        generate_input_fields(input_frame, state["entry_columns"], state["entry_vars"], per_row=6, readonly=False)
        refresh_treeview()

    def refresh_treeview():
        print("refresh_treeview")
        table = selected_table.get()
        pk = get_primary_key(conn, table)
        if not pk:
            result, err = run_custom_select(conn, table, "*", order_clause="", limit_clause="50") # 속도 이슈로 50개만 가져오게 하드 코딩
        else:
            result, err = run_custom_select(conn, table, "*", order_clause=f"{pk} DESC", limit_clause="50") # 속도 이슈로 50개만 가져오게 하드 코딩
        if err:
            messagebox.showerror("조회 오류", err)
            return
        
        state["full_columns"] = [desc[0] for desc in result["columns"]]
        rows = result["rows"]

        # 트리뷰 초기화
        clear_treeview(tree)
        # 트리뷰 업데이트
        update_treeview(tree, result["rows"], state["full_columns"])
        return
    
    def on_insert():
        print("on_insert")
        
        table = selected_table.get()
        if not can(conn, table, "INSERT"):
            messagebox.showwarning("권한 없음", f"{table} INSERT 권한이 없습니다.")
            return
        if not table:
            messagebox.showerror("오류", "테이블을 선택하세요.")
            return
            
        # ✅ 반드시 state["entry_columns"]를 사용
        if not state["entry_columns"]:
            messagebox.showerror("오류", "컬럼 정보가 없습니다.")
            return
        
        values = collect_entry_values(state["entry_columns"], state["entry_vars"])    
        # 디버그 출력
        print("✅ INSERT 실행:", table)
        print("🔸 컬럼:", state["entry_columns"])
        print("🔸 값:", values)
        success, msg = insert_data(conn, table, state["entry_columns"], values)

        if success:
            messagebox.showinfo("성공", msg)
            for var in state["entry_vars"].values():
                var.set("")
                refresh_treeview()
        else:
            messagebox.showerror("DB 오류", msg)
    
    selection_frame, entry_table, listbox_tables = create_table_selector(window, conn, selected_table, on_table_selected, mode="insert")

    input_container = tk.Frame(window)
    input_container.pack(fill="x", padx=10, pady=5)
    
    # 여기에만 스크롤 영역 넣기
    input_frame = create_scrollable_input_frame(input_container)  # 높이 제한 가능

    # 컬럼명에 해당하는 변수 생성
    for t in tables:
        for col in table_columns.get(t, []):
            state["entry_vars"][col] = tk.StringVar()

    btn_insert = tk.Button(window, text="추가", command=lambda: on_insert())
    btn_insert.pack(pady=20)
    
    tree, tree_frame = create_treeview_frame(window, state["full_columns"])
    tree_frame.pack(fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", lambda event: on_row_select(tree, state))

