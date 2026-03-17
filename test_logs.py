import traceback
import monitor
try:
    print('Testing layout_logs()...')
    monitor.layout_logs()
    print('Success!')
except Exception as e:
    print('Exception!')
    traceback.print_exc()
