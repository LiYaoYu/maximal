#!/usr/bin/python3

import signal
import sys
import os
import re

from Xlib import display, X, Xatom


def parse(env):
    for pattern in os.environ.get(env, '').split(','):
        pattern = pattern.strip()
        if pattern:
            yield re.compile('.*%s.*' % pattern)


def match(win):
    try:
        type = win.get_full_property(type_atom, X.AnyPropertyType)
        normal = type and type.value[0] == normal_atom
        target = '%s::%s' % ('::'.join(win.get_wm_class()), win.get_wm_name())
    except Exception:
        return False
    return (normal and
            (not whitelist or any(p.match(target) for p in whitelist)) and
            (not blacklist or all(not p.match(target) for p in blacklist)))


def hide(win):
    if win.id not in handled and match(win):
        hide = win.get_full_property(hide_atom, X.AnyPropertyType)
        handled[win.id] = hide and hide.value
        win.change_property(hide_atom, Xatom.WM_HINTS, 32, [2, 0, 0, 0, 0])


def unhide(win_id, prev_value):
    win = dpy.create_resource_object('window', win_id)
    if prev_value is None:
        win.delete_property(hide_atom)
    elif prev_value is not True:
        win.change_property(hide_atom, Xatom.WM_HINTS, 32, prev_value)


def handle(event):
    if event.type == X.CreateNotify:
        event.window.change_attributes(event_mask=X.StructureNotifyMask)
    elif event.type == X.MapNotify:
        hide(event.window)
    elif event.type == X.DestroyNotify:
        handled.pop(event.window.id, None)


def rlist(parent=None):
    try:
        children = (parent or root).query_tree().children
    except Exception:
        return
    for win in children:
        yield win
        yield from rlist(win)


def loop():
    for win in rlist():
        hide(win)
    root.change_attributes(event_mask=X.SubstructureNotifyMask)
    while True:
        handle(dpy.next_event())


def exit(*args):
    for win_id, value in handled.items():
        unhide(win_id, value)
    dpy.flush()
    sys.exit()


handled = {}
dpy = display.Display()
root = dpy.screen().root
hide_atom = dpy.intern_atom('_MOTIF_WM_HINTS')
type_atom = dpy.intern_atom('_NET_WM_WINDOW_TYPE')
normal_atom = dpy.intern_atom('_NET_WM_WINDOW_TYPE_NORMAL')
whitelist = list(parse('MAXIMAL_WHITELIST'))
blacklist = list(parse('MAXIMAL_BLACKLIST'))
signal.signal(signal.SIGTERM, exit)
loop()
