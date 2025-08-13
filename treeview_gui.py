import tkinter as tk
from tkinter import ttk  # 메시지 박스 (경고/에러 등 창), 테마 위젯 모듈

def create_treeview_frame(parent, columns):
    print("create_treeview_frame")
    window = parent
    # 1. 프레임 준비
    frame = tk.Frame(window)
    frame.pack(fill="both", expand=True)
    frame.pack_propagate(False)
    
    # 1. 새로운 스타일 정의
    style = ttk.Style()
    style.configure("Custom.Treeview.Heading", background="lightgray", foreground="black", font=("Arial", 10, "bold"))
    style.configure("Custom.Treeview", rowheight=25)

    # 2. 스크롤바 먼저 만들고
    scrollbar_x = tk.Scrollbar(frame, orient="horizontal")
    scrollbar_y = tk.Scrollbar(frame, orient="vertical")
    
    # 3. 트리뷰 생성 (스크롤바와 연결)
    tree = ttk.Treeview(frame, 
        columns=columns,
        xscrollcommand=scrollbar_x.set, 
        yscrollcommand=scrollbar_y.set, 
        style="Custom.Treeview", 
        show="headings"
    )

    # 4. 스크롤바 연결
    scrollbar_x.config(command=tree.xview)
    scrollbar_y.config(command=tree.yview)
    
    # 5. 배치 순서 중요!
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")

    # 6. grid weight 설정
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    
    # 태그별 배경색 정의
    tree.tag_configure("evenrow", background="#f9f9f9")  # 짝수행
    tree.tag_configure("oddrow", background="#ffffff")   # 홀수행
    
    return tree, frame
    
def update_treeview(tree, data, selected_columns):
    print("update_treeview")
    tree.delete(*tree.get_children())
	
    tree["show"] = "headings"
    tree["columns"] = selected_columns
    for col in selected_columns:
        tree.heading(col, text=col)
        tree.column(col, width=180, stretch=False)  # 컬럼 너비 넉넉하게
    
    for i, row in enumerate(data):
        tag = "evenrow" if i % 2 == 0 else "oddrow"
        # print(row)
        tree.insert("", "end", values=row, tags=(tag,))
        
def clear_treeview(tree):
    print("clear_treeview")
    tree.delete(*tree.get_children()) 