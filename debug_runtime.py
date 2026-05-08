# debug_runtime.py — ملف تشخيص سريع
import sys
sys.path.insert(0, ".")

from utils.runtime_manager import RuntimeManager

rt   = RuntimeManager()
info = rt.get_debug_info()

print("\n=== Runtime Debug Info ===")
for key, val in info.items():
    print(f"  {key:20} = {val}")

print("\n=== Detect Result ===")
mode = rt.detect()
print(f"  Mode    = {rt.mode_label}")
print(f"  Path    = {rt.ww_path}")
print(f"  Ready   = {rt.is_available}")
