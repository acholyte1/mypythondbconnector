import tkinter as tk  # Tkinter 기본 GUI 라이브러리
from tkinter import messagebox, ttk  # 메시지 박스 (경고/에러 등 창), 테마 위젯 모듈

from db_logic import *  # DB 쿼리 실행 함수
from result_exporter import save_result_to_csv
from gui_utils import *
from form_gui import *
from where_gui import *
from table_gui import * 
from treeview_gui import *
from permissions import can

# GUI 전체를 실행하는 함수
def launch_select_gui(conn, parent, state):    
    print("launch_select_gui")
    # 메인 윈도우
    window = parent
    where_condition_frame_list = []   # 다중 조건 한 줄씩 저장하는 리스트
    order_condition_data = {}      # order 컬럼
    last_result = None # 검색 결과 저장

    table_list = get_table_names(conn) # 테이블명 가져오기
    selected_table = tk.StringVar() # 선택한 테이블

    # 테이블 선택, where과 order 조건 초기화
    def on_table_selected(event):
        print("on_table_select")
        nonlocal tree, tree_frame
            
        selected = get_selected_listbox_item(listbox_tables)
        if selected:
            selected_table.set(selected)
            entry_table.delete(0, tk.END)
            entry_table.insert(0, selected)
            table = selected_table.get()
    
            # 뷰 테이블 여부 확인, 뷰면 기본키 없으므로 작업 안 함
            if is_table_view(conn, table):
                state["is_view"] = True
                state["primary_key"] = None
            else:
                state["is_view"] = False
                state["primary_key"] = get_primary_key(conn, table)
            
            # 출력 상세 필드 초기화
            for field in output_frame.winfo_children():
                field.destroy()
            
            # ① 컬럼 목록 업데이트
            update_column_list(conn, selected, all_columns_listbox, state["full_columns"])
            
            # 선택한 컬럼 목록 초기화
            state["entry_columns"].clear()
            update_selected_column_listbox(selected_column_listbox, state["entry_columns"])
            state["entry_vars"].clear()
            state["entry_vars"].update(init_entry_vars(state["entry_columns"])) 
            generate_input_fields(output_frame, state["entry_columns"], state["entry_vars"], per_row=6, readonly=True) 
            
            # ② 기존 조건 프레임 비우고 새로 생성
            for child in where_condition_frame.winfo_children():
                child.destroy()

            # ✅ 프레임 리스트도 같이 초기화해야 함
            where_condition_frame_list.clear()
            
            # ③ 조건 입력 행 추가
            add_condition_row(where_condition_frame, where_condition_frame_list, state["full_columns"], default=True)
            
            # 정렬 프레임 초기화
            for widget in order_condition_frame.winfo_children():
                widget.destroy()

            # 정렬 GUI 재구성
            add_order_by_widgets(order_condition_frame)
            
    # 선택한 테이블의 컬럼명 저장 
    def update_column_list(conn, table_name, all_columns_listbox, column_list, columns=None):
        print("update_column_list")
        
        # 컬럼 이름 저장    
        if columns is None:
            columns = get_column_names(conn, table_name)
        column_list.clear()
        column_list.extend(columns)
        all_columns_listbox.delete(0, tk.END)
        # listbox에 넣기
        for col in columns:
            all_columns_listbox.insert(tk.END, col)
    
    # 조회할 컬럼 추가
    def add_selected_column():
        print("add_selected_column")
        
        value = get_selected_listbox_item(all_columns_listbox)
        print("선택한 value : " , value)
        if value not in state["entry_columns"]:
            state["entry_columns"].append(value)
            update_selected_column_list(state["entry_columns"])
            update_selected_column_listbox(selected_column_listbox, state["entry_columns"])

    # 조회할 컬럼 삭제
    def remove_selected_column():
        print("remove_selected_column")
        
        value = get_selected_listbox_item(selected_column_listbox)
        state["entry_columns"].remove(value)
        update_selected_column_list(state["entry_columns"])
        update_selected_column_listbox(selected_column_listbox, state["entry_columns"])

    def update_selected_column_list(new_list):
        print("remove_selected_column")
        state["entry_columns"] = new_list
        print("조회할 컬럼 : " , state["entry_columns"])
    
    # 조회할 컬럼 리스트박스에 업데이트
    def update_selected_column_listbox(selected_column_listbox, selected_columns):
        print("update_selected_column_listbox")
        selected_column_listbox.delete(0, tk.END)
        for col in selected_columns:
            selected_column_listbox.insert(tk.END, col)
    
    # 선택한 컬럼
    def on_column_select(event):
        print("on_column_select") 
                
        selected_values = get_all_selected_listbox_items(all_columns_listbox)
        print("selected_values: ", selected_values)
        print("entry_columns: ", state["entry_columns"])
        
        # 중복 없이 selected_columns에 추가
        for val in selected_values:
            if val not in state["entry_columns"]:
                state["entry_columns"].append(val)
                
        # 선택 리스트 갱신
        update_selected_column_list(state["entry_columns"])  # 내부 변수
        update_selected_column_listbox(selected_column_listbox, state["entry_columns"])  # UI

        # print("갱신 후 state["entry_columns"]:", state["entry_columns"])       
    
    # order 조건 입력 추가
    def add_order_by_widgets(parent):
        print("add_order_by_widgets")
        
        # 내부 정렬용 프레임
        frame = tk.Frame(parent)
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # 열 너비 비율 설정
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        # 정렬 컬럼 선택 라벨
        tk.Label(frame, text="정렬 컬럼").grid(row=0, column=0, sticky="w")

        order_column = tk.StringVar()
        order_dir = tk.StringVar(value="ASC")

        # 정렬 컬럼 검색 입력
        order_col_entry = tk.Entry(frame, textvariable=order_column)
        order_col_entry.grid(row=1, column=0, sticky="ew")

        # 컬럼 리스트박스
        order_col_listbox = tk.Listbox(frame, height=5, exportselection=False)
        order_col_listbox.grid(row=3, column=0, sticky="nsew")

        order_col_entry.bind("<KeyRelease>", lambda e: filter_columns(order_col_entry, order_col_listbox, state["full_columns"]))
        order_col_listbox.bind(
            "<<ListboxSelect>>",
            lambda e: order_column.set(get_selected_listbox_item(order_col_listbox) or "")
        )

        # 정렬 방향 설정
        tk.Label(frame, text="방향").grid(row=0, column=1, sticky="w")
        radio_asc = tk.Radiobutton(frame, text="오름차순", variable=order_dir, value="ASC")
        radio_desc = tk.Radiobutton(frame, text="내림차순", variable=order_dir, value="DESC")

        radio_asc.grid(row=1, column=1, sticky="w")
        radio_desc.grid(row=2, column=1, sticky="w")

        # 결과 저장
        order_condition_data["order_column"] = order_column
        order_condition_data["order_dir"] = order_dir
        
        # LIMIT 입력
        tk.Label(frame, text="출력 개수 (LIMIT)").grid(row=0, column=2, sticky="w")
        limit = tk.StringVar()
        tk.Entry(frame, textvariable=limit).grid(row=1, column=2, sticky="ew")
        
        # OFFSET 입력
        tk.Label(frame, text="시작 행 (OFFSET)").grid(row=0, column=3, sticky="w")
        offset = tk.StringVar()
        tk.Entry(frame, textvariable=offset).grid(row=1, column=3, sticky="ew")

        # 저장
        order_condition_data["limit"] = limit
        order_condition_data["offset"] = offset
   
    # 로우 선택 시 실행할 함수
    def handle_row_select(tree, conn, state, output_frame):
        print("handle_row_select")
        table = selected_table.get()
        pk_val, row_values = on_row_select(tree, state)
        print("pk_val: ", pk_val)
        
        if state["is_view"]:
            if not row_values:
                print("⚠ VIEW row 값 없음")
                return
            # ✅ 기존: entry_columns 사용 → 변경: 트리뷰 컬럼명 기준
            columns = tree["columns"]
        else:
            if not pk_val:
                print("⚠ PK 값 없음")
                return

            # TABLE: PK 기반 SELECT *
            row, columns = get_row_by_pk(conn, table, state["primary_key"], pk_val)
            if not row:
                print("⚠ PK 기반 상세 조회 실패")
                return
            row_values = row

        # Entry 초기화 및 세팅
        state["full_vars"].clear()
        state["full_vars"].update(init_entry_vars(columns))

        # ✅ 기존: zip(entry_columns, row_values) → 변경: zip(columns, row_values)
        for col, val in zip(columns, row_values):
            state["full_vars"][col].set(val)

        # Entry UI 갱신
        for child in output_frame.winfo_children():
            child.destroy()
        generate_input_fields(output_frame, columns, state["full_vars"], per_row=6, readonly=True)
    
    # 검색 버튼 클릭 시 실행될 함수
    def on_search(conn, selected_table, all_columns_listbox, tree):
        print("on_search")
        # 입력창에서 SELECT 테이블 텍스트 가져오기
        table = selected_table.get()
        if not can(conn, table, "SELECT"):
            messagebox.showwarning("권한 없음", f"{table} SELECT 권한이 없습니다.")
            return
        print("before: ", state["entry_vars"])

        # 입력창에서 SELECT 컬럼 텍스트 가져오기
        print("entry_columns: ", state["entry_columns"])
        selected_columns = ensure_pk_in_columns(state["entry_columns"], state["primary_key"]) # 로우 선택 시 모든 값을 조회해서 가져오기 위해 기본키 추가
        
        print("selected_columns: ", selected_columns)
        if selected_columns:
            select_fields = ", ".join(selected_columns)
        else:
            select_fields = "*"  # 또는 기본 값

        if not select_fields:
            print("⚠ SELECT 필드 없음")
            return

        # 입력창에서 WHERE 조건 처리
        selected_indices = all_columns_listbox.curselection()
        state["entry_columns"] = get_all_selected_listbox_items(all_columns_listbox)
        where_clause = build_where_clause(where_condition_frame_list)
        
        # ORDER BY 처리
        order_clause = build_order_clause(order_condition_data)
        
        # LIMIT 처리
        limit_clause = build_limit_clause(order_condition_data)

        # DB 로직 실행 (쿼리 결과 or 에러)
        result, error = run_custom_select(conn, table, select_fields, where_clause, order_clause, limit_clause) # 트리뷰

        # 기존 결과 제거
        clear_treeview(tree)

        if error:
            # 쿼리 오류가 있을 경우 팝업으로 에러 표시
            messagebox.showerror("쿼리 오류", error)
        elif result:
            # 🔥 컬럼명 표시
            state["entry_columns"] = [desc[0] for desc in result["columns"]]
            print("entry_column", state["entry_columns"])
            state["entry_vars"].clear()
            state["entry_vars"].update(init_entry_vars(state["entry_columns"]))
            state["full_vars"].clear()
            state["full_vars"].update(init_entry_vars(state["full_columns"]))
            # generate_input_fields(output_frame, state["entry_columns"], state["entry_vars"], per_row=6, readonly=True)
            
            update_treeview(tree, result["rows"], state["entry_columns"])    
            last_result = result

        else:
            # 결과 없음 메시지
            tree.insert(tk.END, "❌ 결과 없음")
    
    # 저장 시 실행되는 함수
    def handle_save():
        print("handle_save")
        nonlocal last_result
        if last_result is None:
            messagebox.showwarning("경고", "먼저 검색을 실행해 주세요.")
            return

        if not last_result["rows"]:
            messagebox.showinfo("정보", "검색 결과가 없어서 저장할 데이터가 없습니다.")
            return
            
        save_result_to_csv(last_result)    
    
    # 테이블 목록 가져오기
    if not table_list:
        messagebox.showerror("DB 오류", "테이블 목록을 가져오지 못했습니다.")
        return
        
    # --- 위젯 구성 ---
    # 상위 프레임
    # # 테이블 선택 (왼쪽 열)
    top_frame = tk.Frame(window)
    top_frame.pack(fill="x")
    
    selection_frame, entry_table, listbox_tables = create_table_selector(top_frame, conn, selected_table, on_table_selected, mode="select")

    # 컬럼 선택 (가운데 열)
    tk.Label(selection_frame, text="컬럼 선택").grid(row=0, column=1, sticky="w")
    
    entry_column = tk.Entry(selection_frame)
    entry_column.grid(row=1, column=1, sticky="ew", padx=5)
    
    all_columns_listbox = tk.Listbox(selection_frame, height=5, exportselection=False)
    all_columns_listbox.grid(row=2, column=1, padx=10)

    entry_column.bind("<KeyRelease>", lambda e: filter_columns(entry_column, all_columns_listbox, state["full_columns"]))
    all_columns_listbox.bind("<<ListboxSelect>>", lambda e: add_selected_column())
    
    # 선택한 컬럼 (오른쪽 열)
    tk.Label(selection_frame, text="선택한 컬럼").grid(row=0, column=2, sticky="w")
    
    selected_column_listbox = tk.Listbox(selection_frame, height=5, exportselection=False)
    selected_column_listbox.grid(row=2, column=2, padx=10)
    selected_column_listbox.bind("<<ListboxSelect>>", lambda e: remove_selected_column())
    
    output_container = tk.Frame(top_frame)
    output_container.pack(fill="x", padx=10, pady=5)
    
    # 여기에만 스크롤 영역 넣기
    output_frame = create_scrollable_input_frame(output_container)  # 높이 제한 가능
    
    # 조건 및 정렬 프레임
    condition_frame = tk.Frame(top_frame)
    condition_frame.pack(pady=10, fill="x")
    
    # WHERE 조건 입력 행을 담을 프레임
    where_frame = tk.Frame(condition_frame)
    where_frame.grid(row=0, column=0, pady=10, sticky="nw", padx=10)
    tk.Label(where_frame, text="WHERE 조건들").pack(anchor="w")

    # WHERE 조건 추가
    where_condition_frame = tk.Frame(where_frame)
    where_condition_frame.pack(pady=10)
    
    tk.Button(where_frame, text="조건 추가", command=lambda: add_condition_row(where_condition_frame, where_condition_frame_list, state["full_columns"])).pack()
    
    # 정렬 프레임 (하단에 추가)
    order_frame = tk.Frame(condition_frame)
    order_frame.grid(row=0, column=1, pady=10, sticky="ne", padx=10)
    tk.Label(order_frame, text="정렬 기준 컬럼").pack(anchor="w")
    
    # order 조건 추가
    order_condition_frame = tk.Frame(order_frame)
    order_condition_frame.pack(pady=10)

    # 하단 버튼 프레임
    button_frame = tk.Frame(top_frame)
    button_frame.pack(pady=10)
    
    # 검색 버튼
    btn_search = tk.Button(button_frame, text="검색", command=lambda: on_search(conn, selected_table, all_columns_listbox, tree))
    btn_search.grid(row=0, column=0, padx=5)
    
    # 결과 저장 버튼
    btn_save = tk.Button(button_frame, text="결과 저장", command=lambda: handle_save())
    btn_save.grid(row=0, column=1, padx=5)
    
    tree, tree_frame = create_treeview_frame(window, state["entry_columns"])
    tree_frame.pack(fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", lambda event: handle_row_select(tree, conn, state, output_frame))