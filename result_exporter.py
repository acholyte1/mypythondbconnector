# result_exporter.py
import csv
from tkinter import filedialog, messagebox

def save_result_to_csv(result):
    print("save_result_to_csv")
    if not result or "columns" not in result or "rows" not in result:
        messagebox.showerror("저장 오류", "저장할 데이터가 없습니다.")
        return

    filepath = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV 파일", "*.csv")],
        title="저장할 파일 선택"
    )
    if not filepath:
        return  # 사용자가 취소함

    try:
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([desc[0] for desc in result["columns"]])
            for row in result["rows"]:
                writer.writerow(row)
        messagebox.showinfo("성공", f"결과가 저장되었습니다:\n{filepath}")
    except Exception as e:
        messagebox.showerror("저장 오류", str(e))