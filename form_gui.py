import tkinter as tk  # Tkinter 기본 GUI 라이브러리

# 입력 필드 생성
def generate_input_fields(parent, columns, entry_vars, per_row=5, readonly=False):
    print("generate_input_fields")
    for i, col in enumerate(columns):
        row = i // per_row
        col_index = (i % per_row) * 2 # label + entry = 2칸 차지
        tk.Label(parent, text=col).grid(row=row, column=col_index, padx=5, pady=2, sticky='e')
        
        state = "readonly" if readonly else "normal"
        entry = tk.Entry(parent, textvariable=entry_vars[col], state=state)
        entry.grid(row=row, column=col_index + 1, padx=5, pady=2)

# 입력 필드 스크롤바        
def create_scrollable_input_frame(parent):
    print("create_scrollable_input_frame")
    canvas = tk.Canvas(parent, height=250)
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return scrollable_frame        
        
# 입력 필드 초기화 (Entry 변수 초기화)
def init_entry_vars(columns):
    print("init_entry_vars")
    return {col: tk.StringVar() for col in columns}

# 입력 필드 값 가져오기 (Entry 값 수집)
def collect_entry_values(columns, entry_vars):
    print("collect_entry_values")
    return [entry_vars[col].get() or None for col in columns]

