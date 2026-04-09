"""临时测试: 验证Windows跨进程文件大小可见性"""
import csv, os, tempfile, subprocess

p = os.path.join(tempfile.gettempdir(), 'test_cross_proc.csv')
f = open(p, 'w', newline='', encoding='utf-8')
w = csv.writer(f)
w.writerow(['a', 'b', 'c'])
rows = [[i, i*2, i*3] for i in range(10000)]
w.writerows(rows)

# NO flush
size_same = os.path.getsize(p)
r = subprocess.run(
    ['powershell', '-c', f'(Get-Item "{p}").Length'],
    capture_output=True, text=True)
size_ps = r.stdout.strip()
print(f"[No flush ] Same process: {size_same} | PowerShell: {size_ps}")

# After flush
f.flush()
size_same2 = os.path.getsize(p)
r2 = subprocess.run(
    ['powershell', '-c', f'(Get-Item "{p}").Length'],
    capture_output=True, text=True)
size_ps2 = r2.stdout.strip()
print(f"[After flush] Same process: {size_same2} | PowerShell: {size_ps2}")

f.close()
os.remove(p)
