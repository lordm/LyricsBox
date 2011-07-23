#!usr/bin/python                                 
#
# LyricsBox
# A Rhythmbox lyrics viewer plugin to show lyrics Karaoke-style.
#
# author: Marwan Osman
# email: lordm2005@gmail.com
##################################################

import re
import rhythmdb, rb
import bisect
import pygtk
pygtk.require('2.0')
import gtk
import pango

patterns = [r'^\[(.*):(.*)\]',
	r'^\[(\d{2}):(\d{2})\.(\d{2})\](.*)'
]

LyricsDir = "/home/lordm/.lyrics/"

class Track():
    def __init__(self):
        self.times = [0]
        self.phrases = [""]
        self.initialized = True
        
    def add_time(self,stamp,text):
        self.times.append(stamp)
        self.phrases.append(text)
    
    def get_phrase(self, ctime):
        i = bisect.bisect_left(self.times, ctime)
        if i != len(self.times):
            return self.phrases[i-1]
        else:
            return ""

class Viewer():
    def __init__(self):
        self.window = gtk.Window()
        self.window.connect("destroy", self.destroy)
        self.window.set_default_size(600,20);
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#000000'))
        self.window.set_title("LyricsBox")
        self.window.set_decorated(False)
        self.window.set_has_frame(False)
        self.window.set_keep_above(True)
        self.window.set_property('skip-taskbar-hint', True)
        self.window.set_gravity(gtk.gdk.GRAVITY_SOUTH_EAST)
        width, height = self.window.get_size()
        self.window.move(gtk.gdk.screen_width()/2 - width/2, gtk.gdk.screen_height() - height)
        self.window.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#ffffff'))
        self.window.set_border_width(2)
        self.window.add_events( gtk.gdk.BUTTON_PRESS_MASK )
        self.window.connect('button-press-event', self.clicked)
        self.label = gtk.Label("")
        self.label.modify_font(pango.FontDescription("sans 9"))
        self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#ffffff'))
        self.window.add(self.label)
        self.label.show()
        self.window.show()
        
    def clicked(self,widget,event):
        self.window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
        
    def destroy(self,widget, data=None):
        self.window.hide()
        
    def update_text(self,new_text):
        self.label.set_text(new_text)

class LyricsBoxPlugin(rb.Plugin):
    def __init__ (self):
        rb.Plugin.__init__ (self)

    def parse_file(self, filename, track):
        try:
            inputfile = open(LyricsDir+filename)
            while True:
                line = inputfile.readline()
                if len(line)==0:
	                break
                #process the line
                #p = re.compile(patterns[0])
                #res = p.search(line)
                #if res != None
                #	setattr(track,res.groups()[0],res.groups()[1])
                #	continue
                p = re.compile(patterns[1])
                res = p.search(line)
                if res != None:
                    temp_stamp = ( int(res.groups()[0]) *60 + int(res.groups()[1]))*100 + int(res.groups()[2])
                    track.add_time(temp_stamp,res.groups()[3])
                    
            inputfile.close()
            print "track length = " + str(len(track.times)) #FOR DEBUGGING
        except IOError:
            print "File not found" #FOR DEBUGGING
            track.initialized = False
            self.viewer.update_text("Lyrics File could not be found")

    def activate (self, shell):
        self.shell = shell
        sp = shell.get_player ()
        self.psc_id = sp.connect ('playing-song-changed', self.playing_entry_changed)
        self.enc_id = sp.connect ('elapsed-nano-changed', self.elapsed_nano_changed) 
        self.viewer = Viewer()
        if sp.get_playing ():
            self.playing_entry_changed(sp.get_playing_entry ())
            
    def deactivate (self, shell):
        self.shell = None
        sp = shell.get_player ()
        sp.disconnect (self.psc_id)
        sp.disconnect (self.enc_id)
        
    def playing_entry_changed (self, sp, entry):
        if sp.get_playing ():
            self.current_track = Track()
            db = self.shell.get_property ("db")
            self.current_track.artist = db.entry_get (entry, rhythmdb.PROP_ARTIST)
            self.current_track.title  = db.entry_get (entry, rhythmdb.PROP_TITLE)
            file_name = self.current_track.artist+ " - " + self.current_track.title + ".lrc"
            self.parse_file(file_name,self.current_track)
            
    def elapsed_nano_changed (self, sp, elapsed):
        stamp_elapsed = elapsed/10000000
        if self.current_track.initialized == True:
            string = self.current_track.get_phrase(stamp_elapsed)
            print string #FOR DEBUGGING
            self.viewer.update_text(string)
