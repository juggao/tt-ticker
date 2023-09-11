#
# NOS Teletekst 703 weerbericht ticker - Pyglet version  (c) 2023 René Oudeweg   GPL 
#
# TODO: background color ticker
# 
import threading
import time
import sys
import os
import subprocess 
import pyglet as pl
from screeninfo import get_monitors
from pyglet.text import Label
from pyglet.window import key
import notify2
from pyglet.window import Window

newsstring="TT-ticker"
stop=False
scroll_speed = 100  # Adjust this value to change the scrolling speed
scroll_speed_factor = 1
ttscroll = None
updatenews_event = None

TICKERHEIGHT = 35
FONTSIZE = 19
UPDATE_INTERVAL_SEC = 1800 # Elk half uur
DEBUG = 0
FPS = 60
DEFAULTTXTCOLOR=(0,100,200,255)
COLORCHANGE = 6
YPOSFACTOR = 2
YPOS = 1
MON_WIDTH = 0
MON_HEIGHT = 0

def printd(txt):
    if DEBUG:
        print("DEBUG: "+txt) 

class QuitException(Exception):
    def __init__(self, message):
        super().__init__(message)

class TTscroll(Window):
    def __init__(self, winx, winy, txt, posx, posy):
        self.xlib_config = pl.gl.Config(double_buffer=True, depth_size=16, sample_buffers=1, samples=4)
        super().__init__(width=winx, height=winy, config=self.xlib_config, style=pl.window.Window.WINDOW_STYLE_BORDERLESS)
        self.set_location(posx, posy)
        self.winx = winx
        self.winy = winy     
        self.posx = posx
        self.posy = posy
        self.gbatch = pl.graphics.Batch()
        self.dt = 1.0
        self.txtcolor = DEFAULTTXTCOLOR
        self.R = DEFAULTTXTCOLOR[0]
        self.G = DEFAULTTXTCOLOR[1]
        self.B = DEFAULTTXTCOLOR[2]
        self.A = DEFAULTTXTCOLOR[3]
        # Create a label with scrolling text
        self.tickertext = txt   
        self.label = Label(self.tickertext, font_name="Liberation Sans", font_size=FONTSIZE, x=self.width, y=self.height // 2, 
              anchor_x="right", anchor_y="center", color=self.txtcolor, batch=self.gbatch)
        self.reset_textpos()
        
    def reset_textpos(self):
        printd(f"reset textpos: x = {self.width}")
        self.label.x = self.width + self.label.content_width
        self.label.y = self.height // 2

    def reset_textpos_when_complete(self):
        self.reset_textpos()

    def set_txtcolor(self, txtcolor):
        printd(f"New textcolor : R={self.R} G={self.G} B={self.B} A={self.A}")
        self.txtcolor = txtcolor
        self.label.begin_update()
        self.label.color = txtcolor
        self.label.end_update()

    def set_text(self,txt):
        self.label.begin_update()
        self.label.text = txt
        self.label.end_update()
        self.tickertext = txt
        self.reset_textpos()

    def set_increase_fontheigth(self):
        self.label.begin_update()
        self.label.font_size += 1
        self.label.end_update()
        printd(f"font_size: {self.label.font_size}")

    def set_decrease_fontheigth(self):
        self.label.begin_update()
        self.label.font_size -= 1
        self.label.end_update()
        printd(f"font_size: {self.label.font_size}")

    def set_increase_tickerheigth(self):
        self.height += 1
        printd(f"window height: {self.height}")
        self.reset_textpos()

    def set_decrease_tickerheigth(self):
        self.height -= 1
        printd(f"window height: {self.height}")
        self.reset_textpos()

    def move_tickerup(self):
        self.posy = self.posy - (self.height * YPOSFACTOR)
        if self.posy <= 0:
            self.posy = 0
        self.set_location(self.posx, self.posy)
    
    def move_tickerdown(self):
        self.posy = self.posy + (self.height * YPOSFACTOR)
        if self.posy >= MON_HEIGHT:
            self.posy = MON_HEIGHT - self.height
        self.set_location(self.posx, self.posy)

    def increase_tickerspeed(self):
        global scroll_speed_factor
        scroll_speed_factor += 2
        printd(f"scroll speed factor: {scroll_speed_factor}")

    def decrease_tickerspeed(self):
        global scroll_speed_factor
        scroll_speed_factor -= 2
        printd(f"scroll speed factor: {scroll_speed_factor}")
        
    def update(self,delta):
        global scroll_speed
        global scroll_speed_factor
        global updatenews_event
        if updatenews_event.is_set():
            self.set_text(newsstring)
            updatenews_event.clear()

        self.label.begin_update()
        self.dt = delta
        if delta<0:
            self.label.x -= scroll_speed * (delta*scroll_speed_factor)  # Scroll the text based on scroll_speedQ
        else:
            self.label.x -= 2
        self.label.end_update()

        printd(f"update self.label.x = {self.label.x} scroll_speed = {scroll_speed} dt: {delta}")
        if self.label.x <= 0:
           self.reset_textpos_when_complete()
        return
    
    def on_key_press(self, symbol, modifiers):
        printd(f"A key was pressed: {symbol} {modifiers}")
        if symbol == key.Q:
            raise QuitException("Quit")
        elif symbol == key.R:
            self.R = (self.R + COLORCHANGE) % 256            
            self.set_txtcolor((self.R,self.G,self.B,self.A))
        elif symbol == key.G:
            self.G = (self.G + COLORCHANGE) % 256
            self.set_txtcolor((self.R,self.G,self.B,self.A))
        elif symbol == key.B:
            self.B = (self.B + COLORCHANGE) % 256
            self.set_txtcolor((self.R,self.G,self.B,self.A))
        elif symbol == key.P:
            self.reset_textpos()
        elif symbol == key.F:
            self.set_increase_fontheigth()
        elif symbol == key.D:
            self.set_decrease_fontheigth()
        elif symbol == key.H:
            self.set_increase_tickerheigth()
        elif symbol == key.J:
            self.set_decrease_tickerheigth()
        elif symbol == key.MOTION_UP:
            self.move_tickerup()
        elif symbol == key.MOTION_DOWN:
            self.move_tickerdown()
        elif symbol == key.PLUS:
            self.increase_tickerspeed()
        elif symbol == key.MINUS:
            self.decrease_tickerspeed()

    def on_draw(self):
        self.clear()
        self.gbatch.draw()
        

def updatenews():
    global newsstring
    global ttscroll
    global stop
    global updatenews_event
    try:
        while (1):
            printd("updatenews")
            newss=tt()
            printd("glob:"+ newsstring)
            printd("update:" + newss)
            if newsstring == newss:
                printd("SAME NEWS")    
            else:
                printd("NEW NEWS")
                newsstring = newss
                updatenews_event.set()
                notify2.init('foo')
                n = notify2.Notification('TELETEKST ALERT', newsstring[:70])
                n.show()
            time.sleep(UPDATE_INTERVAL_SEC)
            if stop == True:
                return
    except KeyboardInterrupt:
        return
    
def tt():
    s1 = os.path.join(os.path.abspath(sys.path[0]), 'ttdownload.sh')
    s2 = os.path.join(os.path.abspath(sys.path[0]), 'extract703.sh')
    print (s1)
    print (s2)
    
    subprocess.call(['bash', s1])
    subprocess.call(['bash', s2])
    newss=" (NOS TT 703) "
    f = open('/tmp/lines.txt', encoding = "ISO-8859-1")  
    lines = f.read().splitlines()
    f.close()
    import html
    for l in lines:
        l.rstrip()
        l.lstrip()
        l = html.unescape(l)
        newss += l
    return newss   

def main():
    global newsstring
    global ttscroll
    global stop 
    global YPOSFACTOR
    global MON_HEIGHT
    global MON_WIDTH
    global updatenews_event

    updatenews_event = threading.Event()
    updatenews_event.clear()

    argc = len(sys.argv)
    #if argc > 1:
    #    YPOSFACTOR = int(sys.argv[1])
    #else:
    #    YPOSFACTOR = 1
    printd(f"YPOSFACTOR = {YPOSFACTOR}")
    
    x = 1
    y = 1080
    for m in get_monitors():
        if m.is_primary:
            y = m.height
            MON_HEIGHT = m.height
            MON_WIDTH = m.width
        print(str(m))

    if m == None:
        exit

    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)
    printd(f"x = {x} , y = {y}")

    newsstring = tt()      
    printd("FIRST: " + newsstring)  
    ttscroll = TTscroll(MON_WIDTH, TICKERHEIGHT, newsstring, x, y-(YPOS*TICKERHEIGHT))    
    updatenews_event.set()

    thread = threading.Thread(target=updatenews)
    thread.start()
    
    # Register the update function to be called regularly
    pl.clock.schedule_interval(ttscroll.update, 1 / FPS) 
    try:
        pl.app.run()
    except pl.window.WindowException as e:
        print(f"Window error: {e}")
    except QuitException as e:
        print(f"QuitException: {e}")
    
    stop = True
    printd("unschedule ttscroll.update")
    pl.clock.unschedule(ttscroll.update)
    ttscroll.close()
    ttscroll = None
    printd("waiting for thread to join")  
    thread.join()
    printd("exiting...")
    pl.app.exit()
    exit()
        
if __name__ == "__main__":
    main()
