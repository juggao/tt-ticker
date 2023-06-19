#
# NEWSAPI.ORG ticker  (c) 2023 René Oudeweg   GPL 
# usage python newsapiticker.py [countrycode]
#
# write your newsapi.org apikey in file apikey.txt first!
#
import threading
import time
import sys
import os
import subprocess 
import pygame as pg
import notify2
import urllib.request, json 

newsstring=""
stop=False
maxnews=10
country="us"
apikey=""
 
class TTscroll:
    def __init__(self, screen_rect, lst):
        self.srect = screen_rect
        self.lst = lst
        self.size = 16
        self.color = (0,0,0)
        self.buff_centery = self.srect.height/2 + 5
        #self.buff_centery = self.srect.h
        self.timer = 0.0
        self.delay = 0
        self.make_surface()
    
    def make_text(self,message):
        global newsstring
        font = pg.font.SysFont('Liberation Sans', self.size)
        print("-> ", newsstring)
        text = font.render(newsstring,True,self.color)
        rect = text.get_rect(center = (self.srect.w, self.srect.centery))
        text.convert()
        return text,rect
  
    def make_surface(self):
        global newsstring
        self.text = []
        for i, line in enumerate(newsstring):
            l = self.make_text(line)
            l[1].y =  self.srect.height/2 - 10
            l[1].x =  self.srect.w
            self.text.append(l)
  
    def update(self):
        if pg.time.get_ticks()-self.timer > self.delay:
            self.timer = pg.time.get_ticks()
            for text, rect in self.text:
                rect.x -= 3
            if rect.x <= -(rect.w):
                print("center")    
                self.make_surface()
                
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
                newsstring = newss;
                notify2.init('foo')
                n = notify2.Notification('NEWS ALERT', newsstring[:60])
                n.show()
            time.sleep(20)
            if stop == True:
                return
    except KeyboardInterrupt:
        return
    
def tt():
    newss = "[NEWSAPI "+country+"] *** "
    x = 0
    
    with urllib.request.urlopen("http://newsapi.org/v2/top-headlines?country="+country+"&apiKey=" + apikey) as url:
        data = json.load(url)
        #print(data)
        for i in data['articles']:
                print(i['title'])
                newss += i['title'] + " *** "
                x += 1
                if (x == maxnews):
                        break
                print("\n");
    return newss
        
def main():
    global newsstring
    global country
    global apikey
    argc = len(sys.argv)
    if argc == 1:
        print("newsapiticker [countrycode]")
        return
    country = sys.argv[1]    
    x = 0
    y = 1080
    from screeninfo import get_monitors
    for m in get_monitors():
        y = m.height-35
        print(str(m))
    
    import os
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)

    keyfile = os.path.join(os.path.abspath(sys.path[0]), 'apikey.txt')
    with open(keyfile, 'r') as file:
        apikey = file.read().rstrip()
    
    print("apikey: "+apikey)
      
    pg.init() 
    
    thread = threading.Thread(target=updatenews)
    thread.start()
  
    newsstring = tt()      
    print("FIRST: " , newsstring)  
    print(pg.display.Info().current_w)
    screen = pg.display.set_mode(size=(pg.display.Info().current_w,35), flags=pg.NOFRAME)
    #pg.display.gl_set_attribute(pg.GL_ACCELERATED_VISUAL,1)
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
        clock.tick(50)
    
        
if __name__ == "__main__":  
    main()

