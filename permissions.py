"""
permission.py
-------------
MySQL 계정의 권한을 조회해서 앱 실행 중에 SELECT / INSERT / UPDATE / DELETE 권한 여부를 확인하는 모듈.

⚡ 주요 동작:
1. 로그인 직후 `load_session_permissions(conn)`를 호출 → 현재 로그인한 계정의 `SHOW GRANTS` 결과를 읽어서 캐싱
2. 이후 `can(conn, table_name, priv)`로 권한 여부를 즉시 확인 가능 (DB 호출 X)
   - table_name에 'schema.table' 형식을 주면 해당 스키마 우선
   - table_name이 스키마 없이 오면 conn.database를 사용
3. 권한이 없으면 UI에서 버튼 비활성화, 실행 시 경고 메시지 등 처리 가능

※ SHOW GRANTS 자체도 권한이 필요한 명령이므로, 이 권한이 없는 계정은
  `SESSION_PERM_MAP`이 None이 되어 권한 체크 없이 실행을 허용(실행 시 DB가 최종 차단).
"""

import re
from mysql.connector import Error

# 로그인 시 불러온 권한 정보를 저장하는 전역 캐시
SESSION_PERM_MAP = None

# SHOW GRANTS 결과를 파싱하기 위한 정규식
# 예시: "GRANT SELECT, UPDATE ON `mydb`.`orders` TO 'user'@'%'"
_GRANT_RE = re.compile(
    r"GRANT (.+) ON (`?([^`]+)`?\.)?(`?\*`?|`?([^`]+)`?) TO", re.I
)

CRUD = {"SELECT", "INSERT", "UPDATE", "DELETE"}

def _expand_privs(raw: set[str]) -> set[str]:
    up = {p.upper() for p in raw}
    # USAGE는 권한 없음(로그인만 허용)이라 확장 X
    if "ALL PRIVILEGES" in up or "ALL" in up:
        # 필요시 다른 권한도 추가 가능 (INDEX, CREATE 등)
        return up | CRUD
    return up
    
def _norm_name(name: str | None) -> str:
        if not name:
            return "*"
        return name.strip().strip("`").lower()

def load_session_permissions(conn):
    """
    현재 로그인한 MySQL 계정의 SHOW GRANTS 결과를 읽어 SESSION_PERM_MAP에 저장.
    - conn: mysql.connector.connect()로 얻은 Connection 객체
    - 호출 시점: 로그인 성공 직후 1회
    """
    global SESSION_PERM_MAP
    
    if conn is None:
        SESSION_PERM_MAP = None
        return
        
    cur = conn.cursor()
    cur.execute("SHOW GRANTS")
    rows = [r[0] for r in cur.fetchall()]  # 첫 번째 컬럼 문자열만 추출
    cur.close()

    perm_map = {}
    for g in rows:
        m = _GRANT_RE.search(g)
        if not m:
            continue

        # 1. 권한 문자열 → set으로 변환 + ALL PRIVILEGES 확장
        raw_privs = {p.strip() for p in m.group(1).split(",")}
        privs = _expand_privs(raw_privs)  # ← ALL PRIVILEGES → CRUD 확장

        # 2. DB명 / 테이블명 정규화
        db = _norm_name(m.group(3))  # 스키마(DB명)
        tbl_raw = m.group(5) if m.group(5) else m.group(4)
        tbl = "*" if tbl_raw in ("*", "`*`") else _norm_name(tbl_raw)

        # 3. 키 생성 + 권한 저장
        key = (db, tbl)
        perm_map.setdefault(key, set()).update(privs)

        
    SESSION_PERM_MAP = perm_map


def _has_priv(db, table, need):
    """
    특정 DB/테이블에 필요한 권한이 있는지 확인.
    우선순위: (db, table) → (db, *) → (*, *) 순으로 확인
    """
    if SESSION_PERM_MAP is None:
        return True
    need = need.upper()
    db_n = _norm_name(db)
    tbl_n = _norm_name(table)
    for key in [(db_n, tbl_n), (db_n, "*"), ("*", "*")]:
        privs = SESSION_PERM_MAP.get(key, set())
        if "ALL PRIVILEGES" in {p.upper() for p in privs} or "ALL" in {p.upper() for p in privs}:
            return True  # ✅ 안전장치(확장 실패 대비)
        if need in privs:
            return True
    return False


def _split_qualified(table_name: str):
    """
    'schema.table' → (schema, table)
    'table' → (None, table)
    백틱(`)으로 감싼 경우도 제거.
    """
    if "." in table_name:
        left, right = table_name.split(".", 1)
        return left.strip("`"), right.strip("`")
    return None, table_name.strip("`")


def can(conn, table_name, priv, db: str | None = None) -> bool:
    """
    현재 세션에서 주어진 테이블/권한이 가능한지 여부를 반환.
    - conn: MySQL Connection 객체
    - table_name: 'table' 또는 'schema.table'
    - priv: 'SELECT', 'INSERT', 'UPDATE', 'DELETE' 중 하나
    - db: 스키마명 강제 지정 (기본값: table_name 또는 conn.database)

    반환값:
    - True  → 권한 있음
    - False → 권한 없음
    """
    if SESSION_PERM_MAP is None:
        # SHOW GRANTS 권한이 없거나 실행 안 한 경우 → 낙관 허용
        # 실행 시 DB가 최종적으로 에러를 발생시키도록 둔다.
        return True

    tbl_db, tbl = _split_qualified(table_name)
    use_db = (tbl_db or db or getattr(conn, "database", None) or "*")
    return _has_priv(use_db, tbl, priv)
   