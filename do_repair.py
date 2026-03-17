import re

with open("monitor_new.py", "r", encoding="utf-8") as f:
    code = f.read()

correct_logic = """    # If close button or background clicked
    if 'close-modal-btn' in trigger or 'modal-bg' in trigger:
        return "hidden fixed inset-0 z-[100] items-center justify-center bg-black/60 backdrop-blur-sm", ""

    if 'conn-row' in trigger:
        # Check if any row was actually clicked (n_clicks > 0)
        if not any(clicks and clicks > 0 for clicks in row_clicks):
             raise dash.exceptions.PreventUpdate

        # Find which row was clicked
        prop_dict = json.loads(trigger.rsplit('.', 1)[0])
        row_data = json.loads(prop_dict['index'])

        # Build modal content matching the image"""
        

bad_logic_start = code.find("    # If close button or background clicked")
bad_logic_end = code.find("        # Build modal content matching the image")

if bad_logic_start != -1 and bad_logic_end != -1:
    end_of_block = bad_logic_end + len("        # Build modal content matching the image")
    
    new_code = code[:bad_logic_start] + correct_logic + code[end_of_block:]
    
    with open("monitor_new.py", "w", encoding="utf-8") as f:
        f.write(new_code)
    print("Patched correctly!")
else:
    print("Could not find blocks.")
