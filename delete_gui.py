import tkinter as tk
import json
import os
from tkinter import ttk, messagebox, simpledialog

from db_logic import *
from encryption_util import get_admin_password
from form_gui import *
from where_gui import *
from table_gui import * 
from gui_utils import *
from treeview_gui import *
from permissions import can

def launch_delete_gui(conn, parent, state):
    print("launch_update_gui")
    # 메인 윈도우
    window = parent
    where_condition_frame_list = [] # 조건절 frame 목록
    
    table_list = get_table_names(conn) # 테이블 목록 가져오기
    selected_table = tk.StringVar() # 선택한 테이블
        
    # 테이블 선택
    def on_table_selected(event):
        print("on_table_select")
            
        selected = get_selected_listbox_item(listbox_tables)
        if selected:
            selected_table.set(selected)
            entry_table.delete(0, tk.END)
            entry_table.insert(0, selected)
            
            # ② 기존 조건 프레임 비우고 새로 생성
            for child in where_condition_frame.winfo_children():
                child.destroy()

            # ✅ 프레임 리스트도 같이 초기화해야 함
            where_condition_frame_list.clear()
            
        table = selected_table.get()
        if not table:
            return
            
        # 출력 상세 필드 초기화
        for field in output_frame.winfo_children():
            field.destroy()
            
        state["entry_columns"] = get_full_columns(conn, table) # 읽기 전용이므로 get_full_columns() 사용
        state["entry_vars"].clear()
        state["entry_vars"].update(init_entry_vars(state["entry_columns"]))
        generate_input_fields(output_frame, state["entry_columns"], state["entry_vars"], per_row=6, readonly=True)
        
        try:
            pk = get_primary_key(conn, table)
            if not pk:
                result, err = run_custom_select(conn, table, "*", order_clause="", limit_clause="50") # 속도 이슈로 50개만 가져오게 하드 코딩
            else:
                result, err = run_custom_select(conn, table, "*", order_clause=f"{pk} DESC", limit_clause="50") # 속도 이슈로 50개만 가져오게 하드 코딩
            if err:
                messagebox.showerror("오류", err)
                return# TreeView 컬럼 재설정
                
            state["full_columns"] = [desc[0] for desc in result["columns"]]
                
            clear_treeview(tree)
            add_condition_row(where_condition_frame, where_condition_frame_list, state["full_columns"], default=True)
            update_treeview(tree, result["rows"], state["entry_columns"])
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def on_search():
        print("on_search")
        table = selected_table.get()
        if not table:
            return

        where_clause = build_where_clause(where_condition_frame_list)
        pk = get_primary_key(conn, table)
        if not pk:
            result, err = run_custom_select(conn, table, "*", where_clause=where_clause, order_clause="", limit_clause="50") # 속도 이슈로 50개만 가져오게 하드 코딩
        else:
            result, err = run_custom_select(conn, table, "*", where_clause=where_clause, order_clause=f"{pk} DESC", limit_clause="50") # 속도 이슈로 50개만 가져오게 하드 코딩
        if err:
            messagebox.showerror("검색 실패", err)
            return

        # 트리뷰 초기화
        clear_treeview(tree)
        columns = [desc[0] for desc in result["columns"]]
        # 트리뷰 업데이트
        update_treeview(tree, result["rows"], columns)

    
    def on_delete():
        print("on_delete")
        table = selected_table.get()
        if not can(conn, table, "DELETE"):
            messagebox.showwarning("권한 없음", f"{table} DELETE 권한이 없습니다.")
            return
        if not table:
            messagebox.showwarning("선택 오류", "테이블을 선택하세요.")
            return
            
        where_clause = build_where_clause(where_condition_frame_list)
        if not where_clause:
            messagebox.showwarning("입력 오류", "WHERE 조건을 입력하세요.")
            return

        if has_is_deleted_column(conn, table):
            # 소프트 삭제
            delete_soft_where(conn, table, where_clause)
            messagebox.showinfo("완료", "소프트 삭제가 완료되었습니다.")
        else:
            # 관리자 비밀번호 입력받아서 하드 삭제
            admin_pw = simpledialog.askstring("관리자 인증", "관리자 암호를 입력하세요:", show="*")
            if admin_pw == get_admin_password():  # config 등에서 불러오기
                delete_hard_where(conn, table, where_clause)
                messagebox.showinfo("완료", "하드 삭제가 완료되었습니다.")
            else:
                messagebox.showwarning("실패", "관리자 암호가 틀렸습니다. 삭제가 취소되었습니다.")
        
        on_search()  # 새로고침
        
    # GUI 구성
    selection_frame, entry_table, listbox_tables = create_table_selector(window, conn, selected_table, on_table_selected, mode="delete")
    
    output_container = tk.Frame(window)
    output_container.pack(fill="x", padx=10, pady=5)
    
    # 여기에만 스크롤 영역 넣기
    output_frame = create_scrollable_input_frame(output_container)  # 높이 제한 가능

    where_frame = tk.Frame(window)
    where_frame.pack(pady=10)
    tk.Label(where_frame, text="WHERE 조건들").pack(anchor="w")

    where_condition_frame = tk.Frame(window)
    where_condition_frame.pack(pady=5)
    
    tk.Button(window, text="조건 추가", command=lambda: add_condition_row(where_condition_frame, where_condition_frame_list, state["full_columns"])).pack()

    # 버튼 프레임
    button_frame = tk.Frame(window)
    button_frame.pack(pady=10)
   
    tk.Button(button_frame, text="검색", command=on_search).grid(row=0, column=1, padx=5)
    tk.Button(button_frame, text="삭제", command=on_delete).grid(row=0, column=2, padx=5)
    
    tree, tree_frame = create_treeview_frame(window, state["full_columns"])
    tree_frame.pack(fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", lambda event: on_row_select(tree, state))