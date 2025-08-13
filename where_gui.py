import tkinter as tk  # Tkinter 기본 GUI 라이브러리
from tkinter import messagebox, ttk  # 메시지 박스 (경고/에러 등 창), 테마 위젯 모듈

from gui_utils import *

# where 리스트박스 컬럼 업데이트
def update_selected_where_column(var, listbox):
	print("update_selected_where_column")
	selection = listbox.curselection()
	if selection:
		selected = listbox.get(selection[0])
		var.set(selected)        

# where 조건 입력 영역 추가
def add_condition_row(parent, where_condition_frame_list, column_list, default=False):
	print("add_condition_row")
	frame = tk.Frame(parent)
	
	col = tk.StringVar() # 컬럼명
	
	if default:
		tk.Label(frame, text="컬럼명").grid(row=0, column=0, sticky="w")
		tk.Label(frame, text="연산자").grid(row=0, column=1, sticky="w")
		tk.Label(frame, text="컬럼값").grid(row=0, column=2, sticky="w")
		tk.Label(frame, text="논리연산자").grid(row=0, column=3, sticky="w")
	
	# 컬럼 검색
	col_entry = tk.Entry(frame, textvariable=col)
	col_entry.grid(row=1, column=0, sticky="w")

	col_listbox = tk.Listbox(frame, height=5, exportselection=False)
	col_listbox.grid(row=2, column=0, sticky="w")

	# 필터링 함수 연결
	col_entry.bind("<KeyRelease>", lambda e: filter_columns(col_entry, col_listbox, column_list))
	col_listbox.bind("<<ListboxSelect>>", lambda e: update_selected_where_column(col, col_listbox))
	
	op = tk.StringVar(value="=") # 연산자
	val = tk.Entry(frame) # 컬럼값
	logic = tk.StringVar(value="AND") # 조건 추가 연산자
	
	operator_menu = tk.OptionMenu(frame, op, "=", "!=", "<", ">", "<=", ">=", "LIKE", "NOT LIKE", "IN", "NOT IN", "IS NULL", "IS NOT NULL", "BETWEEN", "NOT BETWEEN")
	logic_menu = tk.OptionMenu(frame, logic, "AND", "OR")
	
	operator_menu.grid(row=1, column=1, sticky="w")
	val.grid(row=1, column=2, sticky="w")
	if not default:
		logic_menu.grid(row=1, column=3, sticky="w")
	else:
		logic.set("")  # 첫 조건은 논리연산자 제외
	
	# 첫번째는 삭제 버튼 없음
	if not default:        
		# 🟥 삭제 버튼
		btn_delete = tk.Button(frame, text="❌", command=lambda: remove_condition_row(frame, where_condition_frame_list))
		btn_delete.grid(row=1, column=4, sticky="w")            

	next_row = parent.grid_size()[1]
	frame.grid(row=next_row, column=0, sticky="w", pady=2)

	where_condition_frame_list.append({
		"frame": frame,
		"col": col,
		"op": op,
		"val": val,
		"logic": logic,
	})

# where 조건 입력 영역 삭제
def remove_condition_row(frame, where_condition_frame_list):
	print("remove_condition_row")
	# where_condition_frame_list에서 해당 frame 제거
	for cond in where_condition_frame_list:
		if cond["frame"] == frame:
			where_condition_frame_list.remove(cond)
			break
	frame.destroy()