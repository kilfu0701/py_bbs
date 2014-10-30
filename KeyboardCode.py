# -*- coding: cp950 -*-

"""
  鍵盤特殊按鍵 code對應表
""" 
def keyboard_code(key_name):
    try:
        #print "key_b:", key_name
        keyboard_tables = {
            "Up" : "\x1b\x5b\x41",
            "Down" : "\x1b\x5b\x42",
            "Right" : "\x1b\x5b\x43",
            "Left" : "\x1b\x5b\x44",
            "Control_L" : "",
            "Control_R" : "",
            "Shift_L" : "",
            "shift_R" : "",
            "Caps_lock" : "",
            "BackSpace" : "\x08",
            "Return" : "\r", # Enter
            "End" : "\033[8~",
            "Home": "\033[7~",
            "Prior": "\033[5~", # PageUp
            "Next": "\033[6~" # PageDown
        }
        return keyboard_tables[key_name]
    except Exception, e:
        print e
        return ""
