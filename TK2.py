# -*- coding: cp950 -*-
#http://lfw.org/python/Console.py

"""
參考資料:

  ascii table:      http://www.asciitable.com/
  unicode literal:  http://www.utf8-chartable.de/unicode-utf8-table.pl?start=23168&number=128&utf8=string-literal
  TK document:      http://effbot.org/tkinterbook/text.htm
  VT100 ESC:        http://www.comptechdoc.org/os/linux/howlinuxworks/linux_hlvt100.html
  BBS色碼:          http://www.geocities.jp/shiny_shimmery/page_shiny/bbs.htm
  TK Text相關:      http://infohost.nmt.edu/tcc/help/pubs/tkinter/text.html
  編碼問題:         http://moztw.org/docs/big5/
"""

#from Tkinter import *
import Tkinter
import sys, string, traceback, types, __builtin__
import threading, telnetlib, re, time, tkFont

from TelnetDecode import telnet_decode
from KeyboardCode import keyboard_code
from big5ToUnicode import load_B2U_table

telnet = None
reader = None

#
g_exit = False

### global vars for Cursor position
g_cursor_line = 1
g_cursor_pos = 0

### Tk root
g_root = None

### 計算每行的 半形/全形位置
g_pos_table = [] 
g_pos_table_origin = []

### 上色位置
g_color_line = ''
g_color_start = ''
g_color_end = ''

### menubar
g_menubar = ''

### 第一次Initial畫面
g_init = 0

### 設定值
g_config_double = True

g_tmp = 0

g_insert_mode = ''

### 編碼表
g_b2u_dict = {}

g_insert_lock = False

def disconnect():
    try:
        telnet.close()
        print 'telnet disconnect!'
    except:
        pass

def onRightClick(event):
    # display the popup menu
    try:
        g_menubar.tk_popup(event.x_root, event.y_root, 0)
    finally:
        # make sure to release the grab (Tk 8.0a1 only)
        g_menubar.grab_release()


def font_size(value):
    g_root.text["font"] = ( u'細明體', value)
    print value
    print g_root.master.geometry()
    """
        8  = 501x268
        12 = 661x388
    """

def auto_resize():
    g_root.master.geometry()
    pass
    
class OutputPipe:
    """A substitute file object for redirecting output to a function."""
    def __init__(self, writer):
        self.writer = writer
        self.closed = 0

    def __repr__(self):
        return "<OutputPipe to %s>" % repr(self.writer)

    def read(self, length):
        return ""

    def write(self, data):
        if not self.closed: self.writer(data)

    def close(self):
        self.closed = 1


class Console(Tkinter.Frame):
    def __init__(self, parent=None, dict={}, **options):
        Tkinter.Frame.__init__(self, parent)
        
        """ 建立menu bar """
        menubar = Tkinter.Menu(self, tearoff=0)
        
        """ 字體大小設定 """
        fontmenu = Tkinter.Menu(menubar, tearoff=0)
        fontmenu.add_command(label="8", command=lambda: font_size(8))
        fontmenu.add_command(label="10", command=lambda: font_size(10))
        fontmenu.add_command(label="12", command=lambda: font_size(12))
        fontmenu.add_command(label="14", command=lambda: font_size(14))
        fontmenu.add_command(label="16", command=lambda: font_size(16))
        fontmenu.add_command(label="18", command=lambda: font_size(18))
        fontmenu.add_command(label="20", command=lambda: font_size(20))
        
        
        menubar.add_cascade(label="FontSize", menu=fontmenu)
        menubar.add_command(label="Disconnect", command=disconnect)
        menubar.add_command(label="Quit!", command=self.quit)
        """ 
          要用master!!   
          ref: http://effbot.org/zone/tkinter-menubar.htm
        """
        self.master.config(menu=menubar)
        
        #-- Initialize 初始化 --#
        global g_root
        g_root = self
        
        global g_pos_table
        global g_pos_table_origin
        tmp_list = []
        for j in range(0, 150):
            tmp_list.append(0)
        for i in range(0, 25):
            g_pos_table.append(tmp_list)
            g_pos_table_origin.append(tmp_list)
        
        global g_menubar
        g_menubar = menubar
        
        """ 讀取編碼表 """
        global g_b2u_dict
        g_b2u_dict = load_B2U_table()
        
        #-- End Initialize 初始化 --#
        
        
        #-- Continuation state. --#
        self.continuation = 0
        self.error = 0
        self.intraceback = 0
        self.pasted = 0

        #-- The command history. --#

        self.history = []
        self.historyindex = None
        self.current = ""

        #-- Completion state. --#
        self.compmenus = []
        self.compindex = None
        self.compfinish = ""

        #-- Redirection. --#          
        self.stdout = OutputPipe(lambda data, w=self.write: w(data, "stdout"))
        self.stderr = OutputPipe(lambda data, w=self.write: w(data, "stderr"))

        #-- Interpreter state. --#
        if not hasattr(sys, "ps1"): sys.ps1 = ">>> "
        if not hasattr(sys, "ps2"): sys.ps2 = "... "
        self.prefixes = [sys.ps1, sys.ps2, ">> ", "> "]
        self.dict = dict

        #-- The text box. --#
        # insertbackground: 游標顏色
        # font: Courier?? ** u'\u83ef\u5eb7POP3\u9ad4W12' **
        self.text = Tkinter.Text(self, width=80, height=24, insertontime=600, insertofftime=300, insertbackground="white", 
                            background="black", foreground="white", font=( u'細明體', 12) )
        self.text["padx"] = 1
        self.text["pady"] = 1

        
        #-- 字型 --#
        #print tkFont.families()
        
        #-- initial Text --#
        sps = u" " * 80
        for i in range(1,25):
            self.text.insert("end", sps+"\n")
            self.text.tag_add("here", "%d.0" % i, "%d.80" % i)
            self.text.tag_config("here", foreground="red") #// underline=1

        #self.text.config(cursor="arrow")
   
        #-- 按鍵處理 --#
        
        #-- 不要向TEXT作編輯 --#
        #self.text.bind_all('<KeyPress>', lambda e: None)
        self.bind_class("Text", "<KeyPress>", lambda e: None)
        self.bind_class("Text", "<Up>", lambda e: None)
        self.bind_class("Text", "<Down>", lambda e: None)
        self.bind_class("Text", "<Right>", lambda e: None)
        self.bind_class("Text", "<Left>", lambda e: None)
        self.bind_class("Text", "<Return>", lambda e: None)
        self.bind_class("Text", "<BackSpace>", lambda e: None)
        
        self.bind_class("Text", "<KeyPress-Up>", self.arrow_press)
        self.bind_class("Text", "<KeyPress-Down>", self.arrow_press)
        self.bind_class("Text", "<KeyPress-Left>", self.arrow_press)
        self.bind_class("Text", "<KeyPress-Right>", self.arrow_press)
        self.bind_class("Text", "<KeyPress-Return>", self.arrow_press)
        self.bind_class("Text", "<KeyPress-BackSpace>", self.arrow_press)
        self.bind_class("Text", "<KeyPress-Home>", self.arrow_press)
        self.bind_class("Text", "<KeyPress-End>", self.arrow_press)
        self.bind_class("Text", "<KeyPress-Prior>", self.arrow_press)
        self.bind_class("Text", "<KeyPress-Next>", self.arrow_press)
        
        self.bind_class("Text", "<KeyRelease-Up>", self.arrow_release)
        self.bind_class("Text", "<KeyRelease-Down>", self.arrow_release)
        self.bind_class("Text", "<KeyRelease-Left>", self.arrow_release)
        self.bind_class("Text", "<KeyRelease-Right>", self.arrow_release)
        self.bind_class("Text", "<KeyRelease-Return>", self.arrow_release)
        self.bind_class("Text", "<KeyRelease-BackSpace>", self.arrow_release)
        self.bind_class("Text", "<KeyRelease-Home>", self.arrow_release)
        self.bind_class("Text", "<KeyRelease-End>", self.arrow_release)
        self.bind_class("Text", "<KeyRelease-Prior>", self.arrow_release)
        self.bind_class("Text", "<KeyRelease-Next>", self.arrow_release)
        self.bind_class("Text", "<Button-3>", onRightClick) # 滑鼠右鍵
        self.go = False

        self.text.bind_all('<Key>', self.key)
        
        # The scroll bar.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.text.grid(row=0, column=0, sticky='nswe')
        #xscroll = Scrollbar(self, orient=HORIZONTAL, command=self.text.xview)
        #xscroll.grid(column = 0, row = 1, sticky = (W,E))
        #xscroll.pack(side=BOTTOM, fill=X)
        hScroll = Tkinter.Scrollbar(self, orient=Tkinter.HORIZONTAL, command=self.text.xview)
        hScroll.grid(row=1, column=0, sticky='we')
        #hScroll.pack(side=BOTTOM, fill=X)
        
        yscroll = Tkinter.Scrollbar(self, command=self.text.yview)
        yscroll.grid(row=0, column=1, sticky='ns')
        #yscroll.pack(side=RIGHT, fill=Y)
        
        self.text.config(xscrollcommand=hScroll.set, yscrollcommand=yscroll.set)
        
        #self.text.pack(fill=BOTH, expand=1)
        self.text.focus()

        # Configurable options.
        self.options = {"stdoutcolour": "#7020c0",
                        "stderrcolour": "#c03020",
                        "morecolour": "#a0d0f0",
                        "badcolour": "#e0b0b0",
                        "runcolour": "#90d090",
                        "color_33": "#808000" }
                        
        #apply(self.config, (), self.options)
        #apply(self.config, (), options)
        print self.master.winfo_screenwidth(), self.winfo_screenheight(), self.winfo_reqheight()
        

        
        """ BBS Connect """
        global telnet
        global reader
        telnet = telnetlib.Telnet()
        telnet.open('ptt.cc', 23)
        reader = ReaderThread(telnet, self)
        reader.start()

    def __getitem__(self, key):
        return self.options[key]

    def __setitem__(self, key, value):
        if not self.options.has_key(key):
            raise KeyError, 'no such configuration option "%s"' % key
        self.options[key] = value
        if key == "stdoutcolour":
            self.text.tag_configure("stdout", foreground=value)
        if key == "stderrcolour":
            self.text.tag_configure("stderr", foreground=value)

    def config(self, *args, **dict):
        """Get or set configuration options in a Tkinter-like style."""
        if args == () and dict == {}:
            return self.options
        if len(args) == 1:
            return self.options[args[0]]
        for key, value in dict.items():
            self[key] = value

    def cursor(self):
        """Get the current line and position of the cursor."""
        try:
            cursor = self.text.index("insert")
            #print 'cursor', cursor
            #[line, pos] = map(string.atoi, string.split(cursor, "."))
            line, pos = string.split(cursor, ".")
        except Exception, e:
            #print 'cursor():', e
            line = 0
            pos = 0
        return int(line), int(pos)
    
    def write(self, data, tag=None):
        """Show output from stdout or stderr in the console."""
        if self.intraceback and data[-2:] == "\n ": data = data[:-1]
        start = self.text.index("insert")
        self.text.insert("insert", data)
        end = self.text.index("insert")
        if tag: self.text.tag_add(tag, start, end)
    

    """ 
      binding 按鍵處理 
    """
    def key(self, event):    
        is_char = False
        if event.char == event.keysym:
            msg = 'Normal Key %r' % event.char
            is_char = True
        elif len(event.char) == 1:
            msg = 'Punctuation Key %r (%r)' % (event.keysym, event.char)
            is_char = True
            return None
        else:
            """ 特殊鍵額外處理 """
            msg = 'Special Key %r (%r) - %s' % (event.keysym, event.char, event.keycode)
            return None
        
        
        # 更多KEY代碼 請參考 http://www.comptechdoc.org/os/linux/howlinuxworks/linux_hlvt100.html
        if is_char==False:
            # 特殊KEY 轉換成相對應CODE
            input = keyboard_code(event.keysym)
        else:
            input = event.char
        
        telnet.write(input)

    """
      方向鍵Press / Release處理
    """
    def arrow_press(self, event):
        if self.go == False:
            self.go = True
            self.np1(event.keysym)
        else:
            #-- 設定鍵盤按住時的delay --#
            time.sleep(0.01)
            self.np2(event.keysym)
            
    def arrow_release(self, event):
        self.go = False
        
    def np1(self, keysym):
        input = keyboard_code(keysym)
        telnet.write(input)
        pass
        
    def np2(self, keysym):
        input = keyboard_code(keysym)
        telnet.write(input)        

"""
  移動cursor位置到 (x, y)
"""
def move_cursor(x, y, Back=False):  
    if y <= 0 or Back==True:
        pass
    else:
        count = 0
        tmp = 0
        for i in g_pos_table[x]:
            tmp = tmp + i
            count = count + 1
            if y==tmp or y==tmp-1:
                y = count
                break
    
    g_root.text.mark_set("insert", "%d.%d" % (x, y) )
    
"""
  處理所有Telnet連線時的資料 
  接收/傳輸/解碼 等等
"""
class ReaderThread(threading.Thread):
    def __init__(self, telnet, se):
        self.telnet = telnet
        threading.Thread.__init__(self)
        self.se = se
        self.text = se.text
        self.shutdown = False
        move_cursor(0, 0)
    
    def kill_thread(self):
        self.shutdown = True
        print 'shut down'
    
    def run(self):    
        try:
            data_all = ''
            print 'connecting...plz wait!'
            time.sleep(1)
            data = self.telnet.read_very_eager()

            while self.shutdown==False:              
                while data=='':
                    time.sleep(0.1)
                    data = self.telnet.read_very_eager()
                    
                data = telnet_decode( data.encode('hex') )
                self.render_code( data )
                auto_resize()

                data = '' # clear data buffer
                
        except Exception, e:
            print 'ReaderThread.run()', e
            global g_exit
            g_exit = True
            
    def render_code(self, raw_data):
        #try:
            color_table = { "color_33" : "#808000" }
            line = 1
            pos = 0
            first_pos = 0
            code_buf = ''
            text_buf = ''
            is_code = False
            is_code_finish = True # is_code是否已經輸出
            mode = '' # 更新模式
            
            global g_init
            if g_init == 0:
                move_cursor(1, 0)
                g_init = 1
                
            for i in raw_data:   
                #-- \x1b => Code start --#
                if i == '\x1b': 
                    #-- 輸出上次text_buf --#
                    if text_buf != '':
                        text_buf = outputToText( text_buf.encode('hex'), self.text )
                        mode = ''
                    
                    is_code = True
                    is_code_finish = False
                    continue
                
                if is_code == True:
                    if i == '\x5b': # i == '['
                        continue
                    elif i == '\x6d': # i == 'm'
                        is_code = False
                        global g_color_start
                        global g_color_line
                        g_color_line, g_color_start = g_root.cursor()
                    elif i == '\x48' or i == '\x4A': # i == 'H' or i == 'J'
                        code_buf = code_buf + i
                        is_code = False
                    elif i == '\x4B': # i == 'K'
                        code_buf = code_buf + i
                        is_code = False
                    elif i == '\x4D': # i == 'M'
                        code_buf = code_buf + i
                        is_code = False
                    else:
                        code_buf = code_buf + i
                        continue
                    #-- 輸出控制碼 --#
                    is_code_finish = outputControlCode(code_buf)
                    code_buf = ''
                    continue
                else:
                    if type(text_buf) == types.NoneType:
                        text_buf = ''

                    text_buf = text_buf + i
                    pos = pos + 1
                    
            #-- final output check 最後輸出確認 --#
            text_buf = outputToText( text_buf.encode('hex'), self.text )
            
            if is_code_finish == False:
                outputControlCode(code_buf)
            
            
            ###clean pos_table
            for k in range(0, 25):
                if len(g_pos_table[k]) > 100:
                    g_pos_table[k] = g_pos_table[k][0:140]
            
            x, y = g_root.cursor()
            g_cursor_line = x
            g_cursor_pos = y
            
        #except Exception, e:
        #    print e
        
        
"""
  將Buffer內容輸出到text
"""
def outputToText(nnn, text):
    try:
        nokori = '' # 被截掉的的全型字 前半部分
        nnn = nnn + nokori
        position = 0
        
        for i in range(0, len(nnn), 2 ):                
            if (position+2) == len(nnn):
                cch1 = nnn[position] + nnn[position+1]
                nokori = cch1
                cch2 = '00'

            elif (position+4) > len(nnn):
                break
            else:
                cch1 = nnn[position] + nnn[position+1]
                cch2 = nnn[position+2] + nnn[position+3]   
            
            ch = cch1 + cch2
            
            # 轉換成int運算
            ch1 = int(cch1, 16)
            ch2 = int(cch2, 16)
            
            x, y = g_root.cursor()
            x = int(x)
            y = int(y)
            
            if ch1 >= 0x81 and ch1 <= 0xFE and ch2 >= 0x40 and ch2 <= 0xFE:
                # multibyte
                length = len(ch) / 2
                g_root.text.delete( "%d.%d" % (x, y), "%d.%d" % (x, y+length) )
                
                try:
                    #-- b2u解碼 --#
                    global g_b2u_dict
                    ax = '0x'+str.upper(ch)
                    #if ax in g_b2u_dict:
                    #if g_b2u_dict.has_key(ax):
                    try:
                        ppp = '\\u'+g_b2u_dict[ax][2:]
                        word = ppp.decode('raw_unicode_escape')
                        insertToText(word, x, y, bit=2)
                        
                    #else: #-- 不需要B2U decode table --#
                    except:#-- not found in b2u Table --#
                        insertToText((ch).decode('hex').decode('cp950').encode('utf-8'), x, y, bit=2)
                        
                except:
                    print '=== decode error!', repr(ch), x, y
                    pass
                    
                position = position + 4
            
            else:# ascii
                if ch1 >= 0x81:
                    position = position + 2
                    
                else:
                    """
                      針對ascii code做特別處理
                    """
                    if ch1 == 0x08:
                        move_cursor( x, y-1, Back=True)
                        g_root.text.delete( "%d.%d" % ( x, y ), "%d.%d" % ( x, y-1 ) )
                        
                    elif ch1 == 0x07:
                        pass

                    elif ch1 == 0x0d: # CR \r
                        move_cursor(x, 0)
                        
                    elif ch1 == 0x0a: # LF \n
                        x = x + 1
                        ### 如果已經到底部(超過24行), 則須把"第一行"去除!
                        if x >= 25:
                            text.delete("1.0", "1.80")
                            x = 24
                        move_cursor(x, y)
                        
                    else:
                        length = len(cch1) / 2

                        ### 非M模式時, insert前 需刪除一個字元
                        g_root.text.delete( "%d.%d" % (x, y), "%d.%d" % (x, y+length) )
                        insertToText((cch1).decode('hex').decode('cp950').encode('utf-8'), x, y, bit=1)
                        
                    position = position + 2
                    nokori = ''
        
        return nokori.decode('hex')
    except Exception, e:
        print 'outputToText()', e

"""
  把字元insert到text
"""
def insertToText(input, x, y , bit=1):
    try:
        g_root.text.insert("insert", input)
        g_pos_table[x][y] = bit

    except Exception, e:
        print 'eee', e
    
"""
  刪除text內容
"""
def delete(input):
    pass
    
"""
  控制碼處理+輸出
"""                
def outputControlCode(code_buf):
    global g_root
    
    if code_buf == '2J': #-- 清空畫面 --#
        move_cursor(1, 0)
        g_root.text.delete("1.0", Tkinter.END)
        sps = u" " * 80
        for i in range(0, 24):
            g_root.text.insert("insert", sps+"\n")
        g_pos_table = g_pos_table_origin
        move_cursor(1, 0)
        
    elif "H" in code_buf: #-- 移動游標 x,y --#
        mode = 'H'
        if code_buf == "H":
            move_cursor(1, 0)
        else:
            code_buf = code_buf.replace('H', '')
            x, y = code_buf.split(';')
            move_cursor(int(x), int(y)-1) # H 移動時,text的y從0開始, y軸需左移1單位
            
    elif code_buf == 'K': #-- 清除一行 --#
        try:
            line, pos = g_root.cursor()
            g_root.text.delete( "%d.%d" % (line, pos), "%d.%d" % (line, 80) )
        except Exception, e:
            print e

    elif code_buf == 'M': #-- 游標上移一行 --#
        move_cursor(1, 0)
        g_root.text.insert("insert", " "*80+"\n")
        print 'mode M:'
        #exit()

    else:
        if ';' in code_buf: # 顏色碼
            color_list = string.split(code_buf, ';')
            for i in color_list:
                if i == '33':
                    pass

        else:
            pass
    return True


### Main program. ###
if __name__ == "__main__":
    ### ref: http://www.utf8-chartable.de/unicode-utf8-table.pl?start=23168&number=128&utf8=string-literal
    c = Console(dict={})
    c.dict["console"] = c
    c.pack(fill=Tkinter.BOTH, expand=1)
    c.master.title("PyKT BBS")
    
    Tkinter.mainloop()
    
    # 關閉視窗
    print "... Done!"
    telnet.close()
    reader.kill_thread()
    exit()


"""
ref: http://www.geocities.jp/shiny_shimmery/page_shiny/bbs.htm

*[31m暗紅*[m　字變暗紅色。
*[32m暗綠*[m　字變暗綠色。
*[33m暗黃*[m　字變暗黃色。
*[34m暗藍*[m　字變深藍色。
*[35m深紫*[m　字變深紫色。
*[36m藍綠*[m　字變藍綠色。
*[30m黑*[m　　字變黑色。
*[37m暗白*[m　字變暗白色。
 
另外在程式碼加上;1字會變亮。
例如：*[31;1m紅*[m　字會變成亮紅色。
還有特殊效果，加上;5字會閃動。
例如：*[32;5m綠*[m　字就會閃（對不起網頁不知道該怎麼讓他閃）。
也可以加背景顏色。
背景顏色的話，就是把前面的色碼的時未數字改成4。
例如：*[44m背景*[m　字後面的顏色就會變成深藍色。
當然也可以混合使用，
例如：*[43;31;1m嘎嘎嘎*[m　就會變成嘎嘎嘎。
記得在結束控制碼一定要在最後面加上*[m，
不然會很恐怖。

===============================================ANSI控制?的?明  
＼33[0m ??所有?性  
＼33[1m ?置高亮度  
＼33[4m 下划?  
＼33[5m ??  
＼33[7m 反?  
＼33[8m 消?  
＼33[30m -- ＼33[37m ?置前景色  
＼33[40m -- ＼33[47m ?置背景色  
＼33[nA 光?上移n行  
＼33[nB 光?下移n行  
＼33[nC 光?右移n行  
＼33[nD 光?左移n行  
＼33[y;xH?置光?位置  
＼33[2J 清屏  
＼33[K 清除?光?到行尾的?容  
＼33[s 保存光?位置  
＼33[u 恢复光?位置  
＼33[?25l ?藏光?  
＼33[?25h ?示光?  

使用格式能更复?： 
^[[..m;..m;..m;..m
例如： ＼033[2;7;1m高亮＼033[2;7;0m
"""