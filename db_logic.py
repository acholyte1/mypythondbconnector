from db_connector import *

# 전체 테이블 명 가져오기
def get_table_names(conn):
    print("get_table_names")
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        result = cursor.fetchall()
        cursor.close()

        return [row[0] for row in result]
    except Exception as e:
        print("f[❌ 예외 발생] : ", e)
        return []

# 뷰 테이블 제외한 테이블 가져오기
def get_real_tables_only(conn):
    print("get_real_tables_only")
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'""")
        result = cursor.fetchall()
        cursor.close()

        return [row[0] for row in result]
    except Exception as e:
        print("f[❌ 예외 발생] : ", e)
        return []

# 현재 선택한 테이블이 뷰 테이블인지 아닌지 확인
def is_table_view(conn, table_name):
    cursor = conn.cursor()
    sql = """
        SELECT TABLE_TYPE 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
    """
    cursor.execute(sql, (table_name,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        table_type = result[0]
        print(f"✅ {table_name} 타입: {table_type}")
        return table_type == 'VIEW'
    else:
        print(f"⚠ {table_name} 정보 없음")
        return False

# 컬럼 명 가져오기        
def get_column_names(conn, table_name):
    print("get_column_names")
    try:
        cursor = conn.cursor()
        cursor.execute(f"""SHOW COLUMNS FROM `{table_name}`""")
        result = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return result
    except Exception as e:
        print("❌ 컬럼 조회 실패:", e)
        return []        

# where 절 조립
def build_where_clause(condition_frames):
    print("build_where_clause")
    clauses = []
    for cond in condition_frames:
        col = cond["col"].get()
        op = cond["op"].get()
        val = cond["val"].get().strip()
        logic = cond["logic"].get()
        
        null_ops = ["""IS NULL""", """IS NOT NULL"""]

        if not col or not op or (op not in null_ops and not val):
            continue
        
        # 연산자 확인
        if op in ["""IN""", """NOT IN"""]:
            # 쉼표로 나눈 값을 작은 따옴표로 감싸서 괄호 처리
            values = [v.strip() for v in val.split(",")]
            formatted_values = ", ".join(f"""'{v}'""" if not v.isnumeric() else v for v in values)
            clause = f"""{col} {op} ({formatted_values})"""
        elif op in ["""LIKE""", """NOT LIKE"""]:
            val = f"""'%{val}%'"""
            clause = f"""{col} {op} {val}"""
        elif op in ["""IS NULL""", """IS NOT NULL"""]:
            clause = f"{col} {op}"
        elif op in ["""BETWEEN""", """NOT BETWEEN"""]:
            val1, val2 = val.split(""",""")
            clause = f"""{col} {op} '{val1.strip()}' AND '{val2.strip()}'"""
        elif not val.isnumeric():
            val = f"""'{val}'"""
            clause = f"""{col} {op} {val}"""
        else:
            clause = f"""{col} {op} {val}"""

        clauses.append((logic, clause))

    if not clauses:
        return ""

    result = clauses[0][1]
    for logic, clause in clauses[1:]:
        result += f" {logic} {clause}"

    return result

# order 절 조립    
def build_order_clause(order_condition_data):
    print("build_order_clause")
    order_column = order_condition_data["order_column"].get()
    order_dir = order_condition_data["order_dir"].get()
    if order_column:
        return f"""{order_column} {order_dir}"""
    return ""  

# limit 절 조립
def build_limit_clause(order_condition_data):
    print("build_limit_clause")
    try:
        limit = order_condition_data["limit"].get().strip()
        offset = order_condition_data["offset"].get().strip()
        if limit and limit.isdigit():
            if offset and offset.isdigit():
                return f"""{limit} OFFSET {offset}"""
            return f"{limit}"
    except Exception as e:
        print("LIMIT 처리 중 오류:", e)
    return ""    

# select 실행
def run_custom_select(conn, table_name: str, select_fields: str, where_clause: str = "", order_clause: str = "", limit_clause: str = ""):
    print("run_custom_select")
    if not conn:
        return None, "DB 연결 실패"

    try:
        cursor = conn.cursor()
        sql = f"""SELECT {select_fields} FROM {table_name}"""
        
        if where_clause.strip():
            sql += f""" WHERE {where_clause}"""
            
        if order_clause.strip():
            sql += f""" ORDER BY {order_clause}"""
            
        if limit_clause.strip():
            sql += f""" LIMIT {limit_clause}"""
        else:
            sql += """ LIMIT 50""" # (기본 50개만 보여주기)

        print(sql)
        cursor.execute(sql)
        rows = cursor.fetchall()
        # ✅ 컬럼 정보 (리스트 of 튜플)
        columns = cursor.description 

        # ✅ 커서 여기서 닫기
        cursor.close()

        # ✅ 여기서 딕셔너리 형태로 리턴해야 GUI에서 ["columns"] 사용 가능
        return {
            "rows": rows,
            "columns": columns            
        }, None

    except Exception as e:
        # ❌ conn.close() 하지 말자 (다음 호출이 터짐)
        return None, str(e)
    finally:
        try:
            if cursor is not None:
                cursor.close()
        except:
            pass

# 기본키 가져오기
def get_primary_key(conn, table):
    print("get_primary_key")
    try:
        cursor = conn.cursor()
        cursor.execute(f"""DESCRIBE {table}""")
        for row in cursor.fetchall():
            if row[3].upper() == """PRI""":
                return row[0]  # 컬럼명
        return None
    except:
        return None
        
# 기본키로 로우 조회
def get_row_by_pk(conn, table_name, pk_col, pk_val):
    print("get_row_by_pk")
    try:
        pk_val = int(pk_val)
    except ValueError:
        print(f"⚠ PK 값 int 변환 실패: {pk_val}")
        return None, []
        
    cursor = conn.cursor()
    sql = f"""SELECT * FROM `{table_name}` WHERE `{pk_col}` = %s"""
    cursor.execute(sql, (pk_val,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    return row, columns

# 실제 DB에서 컬럼명 불러오기
def fetch_table_columns(conn):
    print("fetch_table_columns")
    table_columns = {}
    cursor = conn.cursor()
    cursor.execute("""SHOW TABLES""")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        cursor.execute(f"""DESCRIBE {table}""")
        cols = [row[0] for row in cursor.fetchall()]
        table_columns[table] = cols
        
    cursor.close()    
    return table_columns, tables

# 전체 컬럼명 가져오기    
def get_full_columns(conn, table_name):
    print("get_insertable_columns")
    cursor = conn.cursor()
    cursor.execute(f"""DESCRIBE {table_name}""")
    cols = []
    for row in cursor.fetchall():
        col_name, _type, _null, _key, _default, extra = row
        cols.append(col_name)
    cursor.close()
    return cols

# 삽입, 수정 시 사용자가 입력할 컬럼명 가져오기    
def get_insertable_columns(conn, table_name):
    print("get_insertable_columns")
    cursor = conn.cursor()
    cursor.execute(f"""DESCRIBE {table_name}""")
    cols = []
    for row in cursor.fetchall():
        col_name, _type, _null, _key, _default, extra = row
        # 제외 조건: auto_increment, generated, on update 등
        if "auto_increment" in extra.lower():
            continue
        if "generated" in extra.lower():
            continue
        if "on update" in extra.lower():
            continue
        cols.append(col_name)
    cursor.close()
    return cols

# 데이터 삽입    
def insert_data(conn, table, columns, values):
    print("insert_data")
    placeholders = ', '.join(['%s'] * len(columns))
    col_names = ', '.join(columns)
    sql = f"""INSERT INTO {table} ({col_names}) VALUES ({placeholders})"""

    try:
        cursor = conn.cursor()
        print(sql)
        cursor.execute(sql, values)
        conn.commit()
        return True, "데이터 삽입 성공"
    except Exception as e:
        return False, str(e)
        
# 단일 행 수정
def update_changed_columns(conn, table, changed_cols, changed_vals, pk_col, pk_val):
    print("update_changed_columns")
    if not changed_cols:
        return False, "변경된 내용이 없습니다."

    set_clause = """, """.join(f"{col} = %s" for col in changed_cols)
    sql = f"""UPDATE {table} SET {set_clause} WHERE {pk_col} = %s"""

    try:
        cursor = conn.cursor()
        print(sql)
        cursor.execute(sql, changed_vals + [pk_val])
        conn.commit()
        return True, "데이터 수정 성공"
    except Exception as e:
        return False, str(e)

# 조건 기반 수정
def update_rows_with_condition(conn, table, set_dict, where_clause):
    print("update_rows_with_condition")
    if not set_dict:
        return False, "수정할 컬럼을 지정하세요."

    set_clause = """, """.join(f"{col} = %s" for col in set_dict)
    values = list(set_dict.values())

    sql = f"""UPDATE {table} SET {set_clause}"""
    if where_clause.strip():
        sql += f""" WHERE {where_clause}"""

    try:
        cursor = conn.cursor()
        print(sql)
        cursor.execute(sql, values)
        conn.commit()
        return True, f"{cursor.rowcount}개 행 수정됨"
    except Exception as e:
        return False, str(e)

# 소프트 삭제        
def delete_soft_where(conn, table, where_clause):
    print("delete_soft_where")
    cursor = conn.cursor()
    sql = f"""UPDATE {table} SET is_deleted = 1 WHERE {where_clause}"""
    print(sql)
    cursor.execute(sql)
    conn.commit()
    cursor.close()

# 하드 삭제 
def delete_hard_where(conn, table, where_clause):
    print("delete_hard_where")
    cursor = conn.cursor()
    sql = f"""DELETE FROM {table} WHERE {where_clause}"""
    print(sql)
    cursor.execute(sql)
    conn.commit()
    cursor.close()

# 소프트 삭제 가능 여부 확인 
def has_is_deleted_column(conn, table):
    print("has_is_deleted_column")
    cursor = conn.cursor()
    cursor.execute(f"""SHOW COLUMNS FROM {table} LIKE 'is_deleted'""")
    result = cursor.fetchone()
    cursor.close()
    return result is not None