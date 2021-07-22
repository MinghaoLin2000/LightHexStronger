# highlighting plugin for Hex-Rays Decompiler
# Copyright (c) 2016
# Milan Bohacek <milan.bohacek+hexlight@gmail.com>
# All rights reserved.
# 
# ==============================================================================
# 
# This file is part of Hexlight.
# 
# Hexlight is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
# ==============================================================================


import idautils
import idaapi
import idc
import ida_kernwin

import traceback

hexlight_cb_info = None
hexlight_cb = None

skip=[]
posledni = 0
import random
import colorsys
def get_n_hls_colors(num):
    hls_colors = []
    i = 0
    step = 360.0 / num
    while i < 360:
        h = i
        s = 90 + random.random() * 10
        l = 50 + random.random() * 10
        _hlsc = [h / 360.0, l / 100.0, s / 100.0]
        hls_colors.append(_hlsc)
        i += step

    return hls_colors

def ncolors(num):
    rgb_colors = []
    if num < 1:
        return rgb_colors
    hls_colors = get_n_hls_colors(num)
    for hlsc in hls_colors:
        _r, _g, _b = colorsys.hls_to_rgb(hlsc[0], hlsc[1], hlsc[2])
        r, g, b = [int(x * 255.0) for x in (_r, _g, _b)]
        rgb_colors.append([r, g, b])

    return rgb_colors
def color(value):
    digit = list(map(str, range(10))) + list("ABCDEF")
    if isinstance(value, tuple):
        string = '#'
        for i in value:
            a1 = i // 16
            a2 = i % 16
            string += digit[a1] + digit[a2]
        return string
    elif isinstance(value, str):
        a1 = digit.index(value[1]) * 16 + digit.index(value[2])
        a2 = digit.index(value[3]) * 16 + digit.index(value[4])
        a3 = digit.index(value[5]) * 16 + digit.index(value[6])
        return (a1, a2, a3)

def randomcolor():
    colorArr = ['1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
    color = ""
    for i in range(6):
        color += colorArr[random.randint(0,14)]
    return int("0x"+color,16)
def jump(custom_viewer, line):
    (pl, x, y) = idaapi.get_custom_viewer_place(custom_viewer, False)
    pl2 = idaapi.place_t_as_simpleline_place_t(pl.clone())
    oldline = pl2.n
    pl2.n = line
    idaapi.jumpto(custom_viewer, pl2, x, y)
    return oldline

class hexrays_callback_info(object):
    
    def __init__(self):
        self.vu = None
        self.highlights = {}
        self.highl_brack = {}
        self.hicolor = 0x6AA84F		#0xF2E8BF #0x00ffff00
        self.theotherline = None
        self.safe = False
        self.colorPackage=["#ed1299", "#09f9f5", "#246b93", "#cc8e12", "#d561dd", "#c93f00", "#ddd53e",
"#4aef7b", "#e86502", "#9ed84e", "#39ba30", "#6ad157", "#8249aa", "#99db27", "#e07233", "#ff523f",
"#ce2523", "#f7aa5d", "#cebb10", "#03827f", "#931635", "#373bbf", "#a1ce4c", "#ef3bb6", "#d66551",
"#1a918f", "#ff66fc", "#2927c4", "#7149af" ,"#57e559" ,"#8e3af4" ,"#f9a270" ,"#22547f", "#db5e92",
"#edd05e", "#6f25e8", "#0dbc21", "#280f7a", "#6373ed", "#5b910f" ,"#7b34c1" ,"#0cf29a" ,"#d80fc1",
"#dd27ce", "#07a301", "#167275", "#391c82", "#2baeb5","#925bea", "#63ff4f"]
        self.tt=0
        return
    
    def clearall(self, ps, refresh=True):
        ctr = 0
        #for i in self.highlights:
            #try:            
                #ps[i].bgcolor = self.highlights[i]
                #ctr += 1
            #except:
                #pass
#               place_t_as_simpleline_place_t
#              ps[i].line.replace("\x04{\x04", "{")
#              ps[i].line.replace("\x04}\x04", "}")
                
        self.highlights = {}
        self.theotherline = None
        if((ctr > 0) and refresh):
            idaapi.refresh_idaview_anyway()

    def clearbracket(self, ps, refresh=True):
        ctr = 0
        for i in self.highl_brack:
            try:            
                ps[i].line = self.highl_brack[i]
                ctr += 1
                #print('clear' + ps[i].line)
            except:
                pass
            
        self.highl_brack = {}
        if((ctr > 0) and refresh):
            idaapi.refresh_idaview_anyway()     
            
    def highlight_bracket2(self, ps, pos_brach, xpos, ypos):
        ln = ps[ypos].line[:]
        if (self.highl_brack.__contains__(ypos) == False):
            self.clearbracket(ps, True)
            self.highl_brack[ypos] = ln
        else:
            ln = self.highl_brack[ypos]
        # 在某行中移动指针到对应的位置
        s1pos = idaapi.tag_advance(ln, pos_brach)
        s2pos = idaapi.tag_advance(ln, xpos)
        line = list(ln)
        while (line[s1pos] != idaapi.SCOLOR_ON or line[s1pos+1] != idaapi.SCOLOR_SYMBOL):
            s1pos += 1
            if (s1pos > len(line)):
                return
        while (line[s2pos] != idaapi.SCOLOR_ON or line[s2pos+1] != idaapi.SCOLOR_SYMBOL):
            s2pos += 1
            if (s2pos > len(line)):
                return

        line[s1pos+1] = idaapi.SCOLOR_ERROR
        line[s1pos+4] = idaapi.SCOLOR_ERROR
        line[s2pos+1] = idaapi.SCOLOR_ERROR
        line[s2pos+4] = idaapi.SCOLOR_ERROR
        ps[ypos].line = ''.join(line)        
        idaapi.refresh_idaview_anyway()  
    
    def rfind_match_brack(self, start, strline, brack1, brack2):
        i = 0
        while (start >= 0) :
            if (strline[start] == brack1):
                i = i + 1
            elif (strline[start] == brack2):
                i = i - 1
            if (i == 0) :
                #find match
                return start 
            start = start - 1
            
        return -1    
        
    def find_match_brack(self, start, strline, brack1, brack2):
        i = 0
        while (start < len(strline)) :
            if (strline[start] == brack1):
                i = i + 1
            elif (strline[start] == brack2):
                i = i - 1
            if (i == 0) :
                #find match
                return start 
            start = start + 1
            
        return -1                   

    def event_callback(self, event, *args):
        try:
#            print "event: %d"%event
            if event == idaapi.hxe_keyboard:
                vu, keycode, shift = args

                if idaapi.lookup_key_code(keycode, shift, True) == idaapi.get_key_code("B") and shift == 0:
                    self.vu = args[0]
                    wpos2 = self.vu.cpos
                    yk2 = wpos2.lnnum
                    ps2 = self.vu.cfunc.get_pseudocode()
                    ln2 = ps2[yk2].line[:]
                    curline2 = idaapi.tag_remove(ln2)
                    yk3 = curline2.find('{')
                    yk4 = curline2.find('}')
                    if yk3>=0 or yk4>=0:
                        if self.theotherline:
                            self.theotherline = jump(vu.ct, self.theotherline)
                        return 0
                elif idaapi.lookup_key_code(keycode, shift, True) == idaapi.get_key_code("V") and shift == 0:
                    self.vu = args[0]
                    wpos = self.vu.cpos
                    yk1 = wpos.lnnum
                    ps = self.vu.cfunc.get_pseudocode()
                    ln = ps[yk1].line[:]
                    curline = idaapi.tag_remove(ln)
                    yk2 = curline.find('{')
                    yk3 = curline.find('}')
                    if yk2>=0 or yk3>=0:
                        ps[yk1].bgcolor=0xFFFFFF
                        if self.theotherline!=None:
                            ps[self.theotherline].bgcolor=0xFFFFFF
                        idaapi.refresh_idaview_anyway()
                        return 0
                elif idaapi.lookup_key_code(keycode, shift, True) == idaapi.get_key_code("H") and shift == 0:
                    
                    if not self.safe:
                        return 0
                    #print "1"
                    self.vu = args[0]

                    if not self.vu:
                        return 0
                    #print "2"

                    if self.vu.cfunc.maturity != idaapi.CMAT_FINAL:
                        return 0
                    #print "3"

                    if not self.vu.visible():
                        return 0
                    #print "4"
                    if not self.vu.refresh_cpos(idaapi.USE_KEYBOARD):
                    #   print "refresh_cpos failed"
                        return 0
                    pos = self.vu.cpos
                    ypos = pos.lnnum
                    xpos = pos.x
                    #print "cursor click %d %d %d" % (pos.x, pos.y, pos.lnnum)
                    #DDD
                    #if self.highlights.__contains__(ypos):
                        #return 0
                    #print "5"
                    #拿到伪代码
                    ps = self.vu.cfunc.get_pseudocode()
                    #print "6"
                    #print "ypos:%d"%ypos
                    #print "ps[ypos].line: %s"%(ps[ypos].line)

                    #line = [idaapi.COLSTR("[%02d]"%i, chr(i)) for i in
                    #range(1,0x40) ]
                    #ps[0].line = ''.join(line);
                    #ps[1].line = '\x04'.join(line);
                    #line = [idaapi.COLSTR( idaapi.COLSTR("[ \x04%02d\x04 ]"%i,
                    #chr(i)), chr(i+1)) for i in range(1,0x40) ]
                    #ps[2].line = ''.join(line);
                    #ps[3].line = '\x04'.join(line);
                    #相当于伪代码的一行
                    ln = ps[ypos].line[:]
                    curline = idaapi.tag_remove(ln)
                    idxO = curline.find('{')
                    idxC = curline.find('}')
                    #print "O:", idxO, " C: ",idxC
                    #there is no need to highlight first and last {
                    #print "8"

                    if (idxO >= 0) or (idxC >= 0):
                    #   print "9"
                        self.clearall(ps, False)
                        # 将本身行颜色存放起来了
                        self.highlights[ypos] = ps[ypos].bgcolor
                        #将 自己的颜色弄进去了
                        #ps[ypos].bgcolor = self.hicolor
                        self.hicolor=int("0x"+self.colorPackage[random.randint(0,49)][1:],16)
                        while(self.hicolor in skip):
                            self.hicolor=int("0x"+self.colorPackage[random.randint(0,49)][1:],16)
                        skip.append(self.hicolor)
                        if ps[ypos].bgcolor not in skip:
                            ps[ypos].bgcolor = self.hicolor
                        
                        dir = 1
                        bracechar = '}'
                        idx = idxO

                        if (idxC >= 0):
                            dir = -1
                            bracechar = '{'
                            idx = idxC

                        j = ypos + dir

                        max = len(ps)
                    #   print "max: ",max

                        while (j >= 0) and (j < max):
                    #       print "10"
                            #print "j:", j
                            ln = idaapi.tag_remove(ps[j].line)
                            if ln.find(bracechar) == idx:
                                if not(self.highlights.__contains__(j)):
                                    self.highlights[j] = ps[j].bgcolor
                                #ps[j].line = ps[j].line.replace(bracechar,
                                #idaapi.COLSTR("\x04"+bracechar+"\x04", "\x27"))
                                #ps[j].line = ps[j].line.replace(bracechar,
                                #idaapi.COLSTR(bracechar, chr(52)))
                                #删除
                                #ps[j].bgcolor = self.hicolor
                                if ps[j].bgcolor not in skip:
                                    ps[j].bgcolor = self.hicolor
                                self.theotherline = j
                                break
                            j+=dir
                        
                        idaapi.refresh_idaview_anyway()
                    else:
                        #self.clearall(ps)
                        print("")
                    #print "11"
                    return 0
                    

            if event <= idaapi.hxe_print_func:
                self.safe = False

            if event == idaapi.hxe_switch_pseudocode:
                self.safe = False

            if event == idaapi.hxe_func_printed:
                self.safe = True

            if event == idaapi.hxe_text_ready:
                self.safe = True
            if event == idaapi.hxe_curpos:
                if not self.safe:
                    return 0
                #print "1"
                self.vu = args[0]

                if not self.vu:
                    return 0
                #print "2"

                if self.vu.cfunc.maturity != idaapi.CMAT_FINAL:
                    return 0
                #print "3"

                if not self.vu.visible():
                    return 0
                #print "4"
                if not self.vu.refresh_cpos(idaapi.USE_KEYBOARD):
                 #   print "refresh_cpos failed"
                    return 0
                pos = self.vu.cpos
                ypos = pos.lnnum
                xpos = pos.x
                #拿到伪代码
                ps = self.vu.cfunc.get_pseudocode()
                ln = ps[ypos].line[:]
                curline = idaapi.tag_remove(ln)
                idxO = curline.find('{')
                idxC = curline.find('}')
                #print "O:", idxO, " C: ",idxC
                #there is no need to highlight first and last {
                #print "8"

                if (idxO >= 0) or (idxC >= 0):
                #   print "9"
                    self.clearall(ps, False)
                    # 将本身行颜色存放起来了
                    self.highlights[ypos] = ps[ypos].bgcolor
                    #将 自己的颜色弄进去了
                    #ps[ypos].bgcolor = self.hicolor
                    self.hicolor=randomcolor()
                    while(self.hicolor in skip):
                        self.hicolor=randomcolor()
                    skip.append(self.hicolor)
                    if ps[ypos].bgcolor not in skip:
                        print("")
                        #ps[ypos].bgcolor = self.hicolor
                    
                    dir = 1
                    bracechar = '}'
                    idx = idxO

                    if (idxC >= 0):
                        dir = -1
                        bracechar = '{'
                        idx = idxC

                    j = ypos + dir

                    max = len(ps)
                 #   print "max: ",max

                    while (j >= 0) and (j < max):
                #       print "10"
                        #print "j:", j
                        ln = idaapi.tag_remove(ps[j].line)
                        if ln.find(bracechar) == idx:
                            if not(self.highlights.__contains__(j)):
                                self.highlights[j] = ps[j].bgcolor
                            #ps[j].line = ps[j].line.replace(bracechar,
                            #idaapi.COLSTR("\x04"+bracechar+"\x04", "\x27"))
                            #ps[j].line = ps[j].line.replace(bracechar,
                            #idaapi.COLSTR(bracechar, chr(52)))
                            #删除
                            #ps[j].bgcolor = self.hicolor
                            if ps[j].bgcolor not in skip:
                                print('')
                                #ps[j].bgcolor = self.hicolor
                            self.theotherline = j
                            break
                        j+=dir
                    
                    idaapi.refresh_idaview_anyway()
                else:
                    #self.clearall(ps)
                    print("")
                #print "11"
                return 0
                
        except:
            traceback.print_exc()
        
        return 0
        

def remove():
    if hexlight_cb:
        idaapi.remove_hexrays_callback(hexlight_cb)

class HexHLightPlugin_t(idaapi.plugin_t):
    flags = idaapi.PLUGIN_HIDE
    comment = "highlights the matching brace in Pseudocode-View"
    help = "press B to jump to the matching brace"
    wanted_name = "HexLight"
    wanted_hotkey = ""

    def init(self):
        # Some initialization
        global hexlight_cb_info, hexlight_cb

        if idaapi.init_hexrays_plugin():
            hexlight_cb_info = hexrays_callback_info()
            hexlight_cb = hexlight_cb_info.event_callback
            if not idaapi.install_hexrays_callback(hexlight_cb):
            #    print "could not install hexrays_callback"
                return idaapi.PLUGIN_SKIP
            print("Hexlight plugin installed Mod by YenKoc")
            addon = idaapi.addon_info_t()
            addon.id = "milan.bohacek.hexlight"
            addon.name = "Hexlight"
            addon.producer = "YenKoc"
            addon.url = "110@qq.com"
            addon.version = "7.5"
            idaapi.register_addon(addon)
            return idaapi.PLUGIN_KEEP
        #print "init_hexrays_plugin failed"
        return idaapi.PLUGIN_SKIP

    def run(self, arg=0):
        return

    def term(self):
        remove()

def PLUGIN_ENTRY():
    return HexHLightPlugin_t()
