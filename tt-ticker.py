import tkinter as tk
import tkinter.font as TkFont
from tkinter import *

import threading
import time
import sys
import os
import subprocess 

newsstring=""
deli = 68          # milliseconds of delay per character
root = tk.Tk()
svar = tk.StringVar()
fnt = TkFont.Font(family="Helvetica",size=25,weight="bold",underline=0)
labl = tk.Label(root, textvariable=svar, height=1, font=fnt, width=200)
stop=False

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
                shif.msg = newss
            time.sleep(10)
            if stop == True:
                return
    except KeyboardInterrupt:
        return
    
def shif():
    shif.msg = shif.msg[1:] + shif.msg[0]
    svar.set(shif.msg)
    root.after(deli, shif)

def tt():
    subprocess.call(['sh', '/home/reinold/bin/ttdownload.sh'])
    subprocess.call(['sh', '/home/reinold/bin/extract.sh'])
    newss=" (NOS TT 101) "
    f = open('/tmp/lines.txt', "r")
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
    
    emptyMenu = Menu(root)
    root.config(menu=emptyMenu)
    root.wm_attributes('-type', 'splash') 
    root.wm_attributes('-alpha',  1.0, '-fullscreen',  False, '-topmost',  True)
    root.overrideredirect(False)
    
    newsstring = tt()      
    print("FIRST: " , newsstring)  
    shif.msg=newsstring 
    shif()
    labl.pack()
    root.geometry("+1+1")
    root.configure(bg='blue')
    thread = threading.Thread(target=updatenews)
    thread.start()
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        stop=True
        sys.exit(0)
        
if __name__ == "__main__":
    main()


