import tkinter as tk

# 리스트박스에서 현재 선택한 거 가져오기
def get_selected_listbox_item(listbox, index=0):
    print("get_selected_listbox_item")
    selection = listbox.curselection()

    if not selection:
        return None  # 아무것도 선택 안 함

    # index가 유효한지 확인
    if not isinstance(index, int) or index < 0 or index >= len(selection):
        return None  # 인덱스가 음수거나 범위를 넘으면 None

    return listbox.get(selection[index])

# 리스트박스에서 선택한 거 모두 가져오기
def get_all_selected_listbox_items(listbox):
    selected = []
    for i in listbox.curselection():
        val = get_selected_listbox_item(listbox, i)
        if val is not None:
            selected.append(val)
    return selected

# 컬럼 입력 영역에서 키 입력될 때마다 필터링
def filter_columns(entry_column, where_column_listbox, column_list):
    print("filter_columns")
    # print("컬럼 목록 : ", column_list)
    keyword = entry_column.get().strip().lower()
    where_column_listbox.delete(0, tk.END)
    for col in column_list:
        if keyword in col.lower():
            where_column_listbox.insert(tk.END, col)

# 트리뷰에서 선택한 컬럼의 값을 가져오기            
def on_row_select(tree, state):
    print("on_row_select")
    tree_selected = tree.focus()
    if not tree_selected:
        return  None, None
    values = tree.item(tree_selected, "values")
    
    # values 없이 들어간 row 확인
    if not values:
        print("⚠ 선택한 row에 값이 없습니다.")
        return None, None
    
    for col in state["entry_columns"]:
        if col in state["full_columns"]:
            i = state["full_columns"].index(col)
            if i < len(values): # values가 full_columns보다 적으면 빈값
                state["entry_vars"][col].set(values[i])
            else:
                state["entry_vars"][col].set("")
        
    # ✅ 기존: values 인덱스로 처리 → 변경: 컬럼명-값 dict 매핑으로 처리
    columns = tree["columns"]
    row_dict = dict(zip(columns, values))  # 여기가 바뀌었다: 컬럼명 기반 안전 매핑

    # ✅ 기존: index 기반 set → 변경: 컬럼명 기반 set
    for col in state["entry_columns"]:
        val = row_dict.get(col, "")
        state["entry_vars"][col].set(val)

    # ✅ 기존: PK 인덱스로 값 추출 → 변경: 컬럼명 기반 안전 추출
    pk_val = None
    if not state["is_view"]:
        if state["primary_key"] and state["primary_key"] in row_dict:
            pk_val = row_dict[state["primary_key"]]
        else:
            print(f"⚠ PK 컬럼 {state['primary_key']}이 row에 없음")

    return pk_val, values if state["is_view"] else None

# 트리뷰에서 컬럼 선택 시 모든 컬럼의 내용을 보여주기 위해 기본키가 조회 조건에 없을 시 추가        
def ensure_pk_in_columns(selected_columns, pk_col):
    print("ensure_pk_in_columns")
    new_columns = selected_columns.copy()
    
    # 선택한 컬럼이 없으면 PK 추가 의미 없음 → 그대로 리턴
    if not selected_columns:
        print("ℹ 선택한 컬럼 없음 → PK 추가 생략")
        return selected_columns
    
    if pk_col is None:
        print("ℹ PK 없음 → 추가 생략")
        return new_columns
    
    if pk_col not in new_columns:
        print(f"✅ PK {pk_col} 자동 추가")
        new_columns.append(pk_col)
    return new_columns
