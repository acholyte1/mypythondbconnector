# C 확장 안 써도 동작하므로 실행 에러 방지
import os
os.environ["MYSQLCLIENT_NO_CEXT"] = "1"
# mysql 연결 라이브러리 불러오기
import mysql.connector
from mysql.connector import Error
import traceback

# DB 연결
def get_connection(host, port, user, password, database):
    print("get_connection")
    print(mysql.connector.__file__)
    print(mysql.connector.__version__)
    try: 
        conn = mysql.connector.connect(
            host=host.strip(), # 서버 호스트 : "stgrds.gschargev.co.kr"
            port=int(port.strip()), # 포트 : 13306
            user=user.strip(), # 사용자 : "qa"
            password=password.strip(), # 비밀번호 : "qa!23"
            database=database.strip() # DB명 : "gschargev"
        )
        print(mysql.connector.connection_cext)
        print("MySQL 접속 성공")
        return conn, None
        
    except mysql.connector.Error as err:
        print("MySQL 접속 실패 : ", err)
        return None, f"MySQL 오류: {err}"
    except Error as e:
        return None, f"MySQL 오류: {e}"
    except Exception as e:
        # 이 줄이 중요: 실제로 어떤 예외가 발생했는지 전체 트레이스백을 파일로 저장
        with open("error_log.txt", "w") as f:
            traceback.print_exc(file=f)
        return None, f"알 수 없는 에러: {e}"