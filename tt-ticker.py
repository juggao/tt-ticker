#
# NOS Teletekst 101 ticker - Pyglet version  (c) 2023 René Oudeweg   GPL 
#
# TODO: background color ticker
# 
import threading
import time
import sys
import os
import subprocess 
import re
from screeninfo import get_monitors

import pyglet as pl
from pyglet.text import Label
from pyglet.window import key
from pyglet.window import Window
from pyglet.gl import GLException

import notify2
import pygame
from pynput import keyboard
import html
import webbrowser

newsstring="TT-ticker"
urgentmessages=[]
urgwindow = None
gbatch = None

stop=False
scroll_speed = 100  # Adjust this value to change the scrolling speed
scroll_speed_factor = 1
ttscroll = None
playing = False

DEBUG = 0
DEBUGUPDATE = 0
DEBUGLINES = 0

TICKERHEIGHT = 55
FONTSIZE = 35
FPS = 60
DEFAULTTXTCOLOR=(255,255,255,255)
COLORCHANGE = 6
YPOSFACTOR = 2
YPOS = 1
MON_WIDTH = 0
MON_HEIGHT = 0
SOUNDFILE = "gong.wav"
MAXPLAY = 5
GLOB_BATCH=0

# STILL UNDER CONSTRUCTION
SHOW_URG=0
URG_WINDOW_HEIGHT = 300
URG_WINDOW_WIDTH = 600
URG_BACKGROUND_COLOR = ( 0, 0, 0, 255)
URG_TEXT_COLOR = (0, 0, 255, 255)

URL="https://nos.nl/teletekst#"

stop_event = None
play_event = None
play_thread = None
listener_thread = None
listener = None
urg_thread = None
updatenews_event = None
drawing_sema = None
updating_sema = None

def printd(txt):
    if DEBUG:
        print("DEBUG: "+txt) 

def extract_number_after_space(input_string):
    # Define a regular expression pattern to match a space followed by a number at the end of the string
    pattern = r' (\d+)$'

    # Use re.search to find the pattern in the input string
    match = re.search(pattern, input_string)

    if match:
        # Extract and return the number after the space as an integer
        trailing_number = int(match.group(1))
        return trailing_number
    else:
        # No matching number found
        return None
    
class QuitException(Exception):
    def __init__(self, message):
        super().__init__(message)

class TTscroll(Window):
    def __init__(self, winx, winy, txt, posx, posy, priogroup):
        self.xlib_config = pl.gl.Config(double_buffer=True, depth_size=16, sample_buffers=1, samples=4)
        super().__init__(width=winx, height=winy, config=self.xlib_config, style=pl.window.Window.WINDOW_STYLE_BORDERLESS)
        self.set_location(posx, posy)
        self.winx = winx
        self.winy = winy     
        self.posx = posx
        self.posy = posy
        global gbatch
        if GLOB_BATCH==1:
            self.gbatch = None
        else:
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
              anchor_x="right", anchor_y="center", color=self.txtcolor, batch=self.get_batch(), group=priogroup)
        self.reset_textpos()
        return

    def draw_batch(self):
        global gbatch
        if GLOB_BATCH==1 and gbatch is not None:
            gbatch.draw()
        elif self.gbatch is not None:
            self.gbatch.draw()
        return
    
    def get_batch(self):
        global gbatch
        if GLOB_BATCH==1 and gbatch is not None:
            return gbatch
        elif self.gbatch is not None:
            return self.gbatch
        return
        
    def reset_textpos(self):
        printd(f"reset textpos: x = {self.width}")
        self.label.begin_update()
        self.label.x = self.width + self.label.content_width
        self.label.y = self.height // 2
        self.label.end_update()
        return
    
    def reset_textpos_when_complete(self):
        self.reset_textpos()
        return
    
    def set_txtcolor(self, txtcolor):
        printd(f"New textcolor : R={self.R} G={self.G} B={self.B} A={self.A}")
        self.txtcolor = txtcolor
        self.label.begin_update()
        self.label.color = txtcolor
        self.label.end_update()
        return
    
    def set_text(self,txt):
        printd(f"set_text() : {txt}")
        self.label.begin_update()
        self.label.text = txt
        self.label.end_update()
        printd(f"end set_text()")
        self.tickertext = txt
        self.reset_textpos()
        return
    
    def set_increase_fontheigth(self):
        self.label.begin_update()
        self.label.font_size += 1
        self.label.end_update()
        printd(f"font_size: {self.label.font_size}")
        return
    
    def set_decrease_fontheigth(self):
        self.label.begin_update()
        self.label.font_size -= 1
        self.label.end_update()
        printd(f"font_size: {self.label.font_size}")
        return
    
    def set_increase_tickerheigth(self):
        self.height += 1
        printd(f"window height: {self.height}")
        self.reset_textpos()
        return
    
    def set_decrease_tickerheigth(self):
        self.height -= 1
        printd(f"window height: {self.height}")
        self.reset_textpos()
        return
    
    def move_tickerup(self):
        self.posy = self.posy - (self.height * YPOSFACTOR)
        if self.posy <= 0:
            self.posy = 0
        self.set_location(self.posx, self.posy)
        return
    
    def move_tickerdown(self):
        self.posy = self.posy + (self.height * YPOSFACTOR)
        if self.posy >= MON_HEIGHT:
            self.posy = MON_HEIGHT - self.height
        self.set_location(self.posx, self.posy)
        return
    
    def increase_tickerspeed(self):
        global scroll_speed_factor
        scroll_speed_factor += 2
        printd(f"scroll speed factor: {scroll_speed_factor}")
        return
    
    def decrease_tickerspeed(self):
        global scroll_speed_factor
        scroll_speed_factor -= 2
        printd(f"scroll speed factor: {scroll_speed_factor}")
        return
        
    def update(self,delta):
        global scroll_speed
        global scroll_speed_factor
        global updatenews_event
        global drawing_sema

        if drawing_sema.is_set():
            drawing_sema.wait()
        if updatenews_event.is_set():
            self.set_text(newsstring)
            updatenews_event.clear()
        
        self.dt = delta
        self.label.begin_update()
        if delta<0:
            self.label.x -= scroll_speed * (delta*scroll_speed_factor)  # Scroll the text based on scroll_speedQ
        else:
            self.label.x -= 2
        self.label.end_update()

        #self.gbatch.invalidate()
        
        if DEBUGUPDATE==1:
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
        return
    
    def on_draw(self):
        global drawing_sema, updating_sema
        if drawing_sema.is_set():
            drawing_sema.wait()
        if updating_sema.is_set():
            updating_sema.wait()
        self.clear()
        drawing_sema.set()
        printd("TTscroll.on_draw()")
        self.draw_batch()
        drawing_sema.clear()
        return
            
def play_sound():
    global play_event
    printd(f"PLAY: {SOUNDFILE} loops={MAXPLAY}")
    pygame.mixer.music.play(loops=MAXPLAY)
    play_event.set()
    printd("played")
    return

def stop_sound():
    global stop_event
    printd(f"STOP: {SOUNDFILE}")
    pygame.mixer.music.stop()
    stop_event.set()
    printd("stopped")
    return
    
def on_key_release(key):
    printd("on_key_release()")
    global play_event, stop_event
    if key == keyboard.Key.space:
        printd("space pressed")
        stop_sound()
    return

def start_playthreads():
    global play_event, stop_event, play_thread, listener_thread, listener
    if play_thread == None:
        printd("starting play threads")
        play_event = threading.Event()
        stop_event = threading.Event()
        play_thread = threading.Thread(target=play_sound)
        # Set up a listener for key releases
        listener = threading.Thread(target=keyboard.Listener(on_release=lambda k: on_key_release(k)))
        listener = keyboard.Listener(on_release=lambda k: on_key_release(k))
        listener_thread = threading.Thread(target=listener.start)
        play_thread.start()
        listener_thread.start()
    return

def join_play_threads():
    global play_event, stop_event, play_thread
    if play_thread is not None:
        if play_event.set() == True:
            stop_sound()
        play_thread.join()
    if listener_thread is not None:
        listener_thread.join()
    return

class ClickableURLLabel(pl.text.Label):
    def __init__(self, text, xpos, ypos, gbatch):
        super().__init__(text, font_name='Arial', font_size=13, x=xpos, y=ypos, anchor_x="center", anchor_y="center", color=URG_TEXT_COLOR,  
                             batch=gbatch)
        self.ttpage = 101
        if len(text):
            self.ttpage = extract_number_after_space(text)
        self.url = URL+str(self.ttpage)

    def on_mouse_press(self, x, y, button, modifiers):
        printd("ClickableURLLabel.on_mouse_press()")
        if self.x <= x <= self.x + self.content_width and self.y <= y <= self.y + self.content_height:
            # The label area was clicked, so open the URL
            printd("on_mouse_press() open webbrowser")
            webbrowser.open(self.url)
        return
        
class DisplayWindow(pl.window.Window):
    def __init__(self):
        self.xlib_config = pl.gl.Config(double_buffer=True, depth_size=16, sample_buffers=1, samples=4)
        super().__init__(width=URG_WINDOW_WIDTH, height=URG_WINDOW_HEIGHT, config=self.xlib_config, caption="URGENT NEWS")
        self.set_location(0, 0)
        self.updated = threading.Event()
        self.updated.clear()
        if GLOB_BATCH==1:
            self.gbatch = None
        else:
            self.gbatch = pl.graphics.Batch()
        self.urgentmessages_labels = []
        return
    
    def draw_batch(self):
        global gbatch
        if GLOB_BATCH==1 and gbatch is not None:
            gbatch.draw()
        elif self.gbatch is not None:
            self.gbatch.draw()
        return
    
    def get_batch(self):
        global gbatch
        if GLOB_BATCH==1 and gbatch is not None:
            return gbatch
        elif self.gbatch is not None:
            return self.gbatch
        return

    def make_labels(self, priogroup):
        y_position = URG_WINDOW_HEIGHT - 50
        for n in range(1,6):
            printd(f"make label: {n}")

            label = ClickableURLLabel(" ", URG_WINDOW_WIDTH // 2, y_position, self.get_batch())

            #label = pl.text.Label(" ", font_name='Arial', font_size=13,
            #                  x=URG_WINDOW_WIDTH // 2, y=y_position,
            #                  anchor_x='center', anchor_y='center',
            #                  color=URG_TEXT_COLOR, batch=self.gbatch, group=priogroup)
            
            y_position -= 50
            self.urgentmessages_labels.append(label)        
        return
    
    def update(self, delta):
        global urgentmessages, drawing_sema, updating_sema
        if drawing_sema.is_set():
            drawing_sema.wait()
        if updating_sema.is_set():
            updating_sema.wait()
        updating_sema.set()
        printd("urgwindow.update()")
        n_msg =  len(urgentmessages)
        n_labels = len(self.urgentmessages_labels)
        printd(f"urgwindow.update() n_msg: {n_msg} n_labels: {n_labels}")
        if n_msg > n_labels:
            n_msg = n_labels
        for n in range(0,n_labels):
            txt = "*"
            if n < n_msg:
                txt = urgentmessages[n]
            self.urgentmessages_labels[n].begin_update()
            printd(f"urgwindow.update() txt: {txt}")
            self.urgentmessages_labels[n].text = txt
            self.urgentmessages_labels[n].end_update()
        self.updated.set()
        updating_sema.clear()
        printd("urgwindow.update() exit")
        return
#DEBUG:    
    def on_draw(self):
        global drawing_sema, updating_sema
        if self.updated.is_set() == False:
            return
        if drawing_sema.is_set():
            drawing_sema.wait()
        if updating_sema.is_set():
            updating_sema.wait()
        self.clear()
        drawing_sema.set()
        printd("urgwindow.on_draw()")
        self.draw_batch()
        drawing_sema.clear()
        return
    
def updatenews():
    global newsstring
    global ttscroll
    global stop
    global updatenews_event
    global drawing_sema, updating_sema

    try:
        while (1):
            printd("updatenews")
            #newss=tt()
            if drawing_sema.is_set():
                drawing_sema.wait()
            newss=tt_fetch_and_check()
            if newsstring == newss:
                printd("SAME NEWS")    
            else:
                printd("NEW NEWS")
                newsstring = newss
                updatenews_event.set()

                notify2.init('foo')
                n = notify2.Notification('TELETEKST ALERT', newsstring[:70])
                n.show()
            time.sleep(20)
            join_play_threads()
            if stop == True:
                return
    except KeyboardInterrupt:
        return

def tt_fetch_and_check():
    global urgentmessages
    urgentmsgs = []
    rval=tt()
    newss, urgentmsgs = rval
    printd("glob:"+ newsstring)
    printd("update:" + newss)
    if len(urgentmsgs):
        if urgentmsgs != urgentmessages:
            newurgentmessages = list(set(urgentmsgs + urgentmessages))
            urgentmessages = newurgentmessages
            printd(f"HEADLINES:{len(urgentmessages)} : {urgentmessages}")
            start_playthreads()
        else:
            printd("HEADLINES already played sound")
    return newss
    
def tt():
    s1 = os.path.join(os.path.abspath(sys.path[0]), 'ttdownload.sh')
    s2 = os.path.join(os.path.abspath(sys.path[0]), 'extract.sh')
    
    if DEBUGLINES == 0:
        subprocess.call(['bash', s1])
        subprocess.call(['bash', s2])
    newss=" (NOS TT 101) "
    f = open('/tmp/lines.txt', encoding = "ISO-8859-1")  
    lines = f.read().splitlines()
    f.close()
    urgentmsgs = []
    for l in lines:
        l = html.unescape(l)
        if l.isupper():
            urgentmsgs.append(l)
        newss += l + " *** "  
    return newss, urgentmsgs   

def main():
    global newsstring
    global ttscroll
    global urgwindow
    global stop 
    global gbatch
    global YPOSFACTOR
    global MON_HEIGHT
    global MON_WIDTH
    global drawing_sema, updating_sema, updatenews_event

    argc = len(sys.argv)
    #if argc > 1:
    #    YPOSFACTOR = int(sys.argv[1])
    #else:
    #    YPOSFACTOR = 1
    printd(f"YPOSFACTOR = {YPOSFACTOR}")

    updatenews_event = threading.Event()
    drawing_sema = threading.Event()
    updating_sema = threading.Event()
    updating_sema.clear()
    drawing_sema.clear()
    updatenews_event.clear()

    x = 1
    y = 1080
    for m in get_monitors():
        if m.is_primary:
            y = m.height
            MON_HEIGHT = m.height
            MON_WIDTH = m.width
        print(str(m))

    if m == None:
        exit()

    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)
    printd(f"x = {x} , y = {y}")

    pygame.mixer.init()
    gongsoundfile = os.path.join(os.path.abspath(sys.path[0]), SOUNDFILE)
    pygame.mixer.music.load(gongsoundfile)
    
    rval=tt()
    newsstring, urgentmsgs = rval   
    updatenews_event.set()

    printd("FIRST: " + newsstring)  

    if GLOB_BATCH==1:
        gbatch = pl.graphics.Batch()

    prio1 = pl.graphics.Group(order=0)
    prio2 = pl.graphics.Group(order=1)
    
    if SHOW_URG:
        urgwindow = DisplayWindow()
    ttscroll = TTscroll(MON_WIDTH, TICKERHEIGHT, newsstring, x, y-(YPOS*TICKERHEIGHT), prio1)         

    pl.clock.schedule_interval(ttscroll.update, 1 / FPS) 
    
    if SHOW_URG:
        urgwindow.make_labels(prio2)
        pl.clock.schedule_interval(urgwindow.update, 1)    
    
    updatethread = threading.Thread(target=updatenews)
    updatethread.start()
    
    ttscroll.activate()
    if SHOW_URG:
        urgwindow.activate()
    try:
        pl.app.run()
    except pl.window.WindowException as e:
        print(f"Window error: {e}")
    except QuitException as e:
        print(f"QuitException: {e}")
    except GLException as e:
         print(f"GLException: {e}")
         
    stop = True
    printd("unschedule ttscroll.update")
    pl.clock.unschedule(ttscroll.update)
    ttscroll.close()
    ttscroll = None

    if SHOW_URG:
        pl.clock.unschedule(urgwindow.update)
        urgwindow.close()

    printd("waiting for threads to join")  
    updatethread.join()
    join_play_threads()
    if urg_thread:
        urg_thread.join()
    printd("exiting...")
    pl.app.exit()
    exit()    
        
if __name__ == "__main__":
    main()
