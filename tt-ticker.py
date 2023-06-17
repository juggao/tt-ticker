import tkinter as tk
import tkinter.font as TkFont
from tkinter import *

import threading
import time
import sys
import os
import subprocess 
import pygame as pg
  

newsstring=""
deli = 133          # milliseconds of delay per character
root = tk.Tk()
svar = tk.StringVar()
fnt = TkFont.Font(family="Helvetica",size=25,weight="bold",underline=0)
labl = tk.Label(root, textvariable=svar, height=1, font=fnt, width=200)
stop=False


class TTscroll:
    def __init__(self, screen_rect, lst):
        self.srect = screen_rect
        self.lst = lst
        self.size = 18
        self.color = (0,0,0)
        self.buff_centery = self.srect.height/2 + 5
        #self.buff_centery = self.srect.h
        self.buff_lines = 50
        self.timer = 0.0
        self.delay = 0
        self.make_surfaces()
    
    def make_text(self,message):
        global newsstring
        font = pg.font.SysFont('Liberation Sans', self.size)
        text = font.render(newsstring,True,self.color)
        #rect = text.get_rect(center = (self.srect.w, self.srect.centery + self.buff_centery) )
        rect = text.get_rect(center = (self.srect.w, self.srect.centery))
        return text,rect
  
    def make_surfaces(self):
        global newsstring
        self.text = []
        for i, line in enumerate(newsstring):
            l = self.make_text(line)
            l[1].y =  self.srect.height/2 - 7
            l[1].x =  self.srect.w
            self.text.append(l)
  
    def update(self):
        if pg.time.get_ticks()-self.timer > self.delay:
            self.timer = pg.time.get_ticks()
            for text, rect in self.text:
                rect.x -= 2
            if rect.x <= -(rect.w):
                print("center")    
                self.make_surfaces()
                
    def render(self, surf):
        for text, rect in self.text:
            surf.blit(text, rect)
  


def updatenews():
    global newsstring
    try:
        while (1):
            print("updatenews")
            newss=tt()
            print("glob:"+ newsstring)
            print("update:" + newss)
            if newsstring == newss:
                print("SAME NEWS")    
            else:
                print("NEW NEWS")
                #print(newss)
                #shif.msg = newss
            time.sleep(10)
            if stop == True:
                return
    except KeyboardInterrupt:
        return
    
def tt():
    subprocess.call(['sh', '/home/reinold/bin/ttdownload.sh'])
    subprocess.call(['sh', '/home/reinold/bin/extract.sh'])
    newss=" (NOS TT 101) "
    f = open('/tmp/lines.txt', encoding = "ISO-8859-1")
    #lines = f.read().splitlines().decode('utf-8')    
    lines = f.read().splitlines()
    f.close()
    import html
    for l in lines:
        l = html.unescape(l)
        newss += l + " *** "  
    return newss
        
def main():
    #   tk.Button(root, text="Click Me", command=click_btn).pack()
    global newsstring
   
    x = 0
    y = 1080
    from screeninfo import get_monitors
    for m in get_monitors():
        y = m.height-35
        print(str(m))
    
    import os
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)
  
    pg.init() 
    
    thread = threading.Thread(target=updatenews)
    thread.start()
    
    newsstring = tt()      
    print("FIRST: " , newsstring)  

    print(pg.display.Info().current_w)
    screen = pg.display.set_mode(size=(pg.display.Info().current_w,35), flags=pg.NOFRAME)
#   screen = pg.display.set_mode(size=(pg.display.Info().current_w,35))
  
   
    screen_rect = screen.get_rect()
    clock = pg.time.Clock()
    done = False
    cred = TTscroll(screen_rect, newsstring)    
            
    while not done:
        for event in pg.event.get(): 
            if event.type == pg.QUIT:
                done = True
        screen.fill((255,255,255))
        cred.update()
        cred.render(screen)
        pg.display.update()
        clock.tick(60)
    
        
if __name__ == "__main__":
    main()


  

