import traceback
from gui_login import launch_login_gui  # 앱 실행

if __name__ == "__main__":
    try:
        result = launch_login_gui()
        if result == "cancel":
            print("🛑 사용자에 의해 창이 닫혔습니다.")
        elif result == "error":
            print("❌ GUI 실행 중 예외 발생:")
    except Exception as e:
        print("❌ 예외 발생:")
        traceback.print_exc()
        input("\n엔터를 누르면 종료합니다...")
