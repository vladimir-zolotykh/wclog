#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
# from dataclasses import dataclass
import os
import threading
from typing import Optional
from datetime import datetime
import argparse
import argcomplete
import tkinter as tk
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import askyesno
from scrolled_treeview import ScrolledTreeview
from time4 import Time4, Time4Var
from combo_db import ComboDb
from logrecord import LogRecord
from sqlalchemy import select, create_engine, func
from sqlalchemy.orm import sessionmaker
import models as md
from database import session_scope
from database import initialize, Session
import button_font
from tooltip import Tooltip


class LogViewer(tk.Tk):
    # LOG_FORM_FLD = f'_{fld_name}_var'
    log_list_test = [
        ('639', '2024-01-26 13:00:00', 'pee', '439', 'Creatine'),
        ('640', '2024-01-26 13:31:00', 'pee', '581', ''),
        ('641', '2024-01-26 14:00:00', 'pee', '706', '')
    ]

    # def __init__(self, con, *args, **kwargs):
    def __init__(self, engine):
        super().__init__()
        # self.db_con = con
        self.engine = engine
        self.title(engine.url.database)
        # con.app = self          # use case: askyesno(parent=con.app,...
        self.form_vars = {}
        # Better not to mention data structure type in a variable name
        log_list = ScrolledTreeview(self, columns=('id', 'stamp', 'label',
                                                   'volume', 'note'),
                                    selectmode='browse')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        log_list.grid(column=0, row=0, sticky=tk.NSEW)
        # .bind: two handlers are called: ScrolledTreeview.on_select,
        # then LogViewer.on_treeview_select
        log_list.bind('<<TreeviewSelect>>', self.on_treeview_select, add='+')
        self.log_list = log_list
        self.update_log_list()
        form = tk.Frame(self)
        form.grid(column=1, row=0, sticky=tk.NS)
        row = self.create_form_fields(form)
        row += 1
        buttons_bar = tk.Frame(form)
        form.rowconfigure(row, weight=1)
        buttons_bar.grid(column=0, row=row, columnspan=2, sticky=tk.S)
        update_btn = tk.Button(buttons_bar,
                               text='Update', command=self.edit_log)
        Tooltip(update_btn, """\
Update the existing sample or
create a new one""",
                font=button_font.TooltipFont())
        narrow_btn = tk.Button(buttons_bar,
                               text='Narrow\nto date',
                               command=self.narrow_to_date)
        Tooltip(narrow_btn, """\
Select/enter the date into "stamp" field click the button.
Click again to revert.""",
                font=button_font.TooltipFont())
        self.script_btn = tk.Menubutton(
            buttons_bar, text='Script', relief=tk.RAISED, bd=2)
        script_menu = tk.Menu(self.script_btn, tearoff=0)
        self.script_btn.config(menu=script_menu)
        script_menu.add_command(
            label='Make blank sample', font=button_font.ButtonFont(),
            command=self.make_new)
        script_menu.add_command(
            label='pee', font=button_font.ButtonFont(),
            command=lambda: self.make_tagged_sample('pee'))
        script_menu.add_command(
            label='IMET', font=button_font.ButtonFont(),
            command=lambda: self.make_tagged_sample('IMET'))
        if engine.url.database == ':memory:':
            script_menu.add_command(
                label='Set logfile date', font=button_font.ButtonFont(),
                command=(lambda sm=script_menu, lt='Set logfile date':
                         self.set_logfile_date(sm, lt)),
                # command=self.set_logfile_date
            )
            script_menu.add_command(
                label='Save as .txt', font=button_font.ButtonFont(),
                command=self.save_mem_as_txt)
        Tooltip(self.script_btn, """\
Initialize the fields above for the selected action""",
                font=button_font.TooltipFont())
        self.del_btn = tk.Button(
            buttons_bar, text='Del', command=self.del_log, state=tk.DISABLED)
        self.del_btn.grid(column=2, row=0)
        Tooltip(self.del_btn, """\
Delete the sample from the database""",
                font=button_font.TooltipFont())
        # >>> tkFont.nametofont('TkDefaultFont').config()['family']
        # 'sans-serif'
        for col, btn in enumerate((update_btn, narrow_btn, self.script_btn,
                                   self.del_btn)):
            size = 6 if btn.cget('text').startswith('Narrow') else 8
            btn.grid(column=col, row=0)
            btn.config(font=button_font.ButtonFont(size=size))

    def set_logfile_date(self, menu, label):
        def menu_item_index(menu, label):
            for i in range(menu.index("end")):
                opt = menu.entryconfig(i)
                if "label" in opt and opt["label"][4].startswith(label):
                    return i
            return None
        self.logfile_date = datetime.strptime(self.get_var('stamp').get(),
                                              '%Y-%m-%d %H:%M:%S').date()
        label = ' '.join(label.split(maxsplit=3))
        index = menu_item_index(menu, label)
        menu.entryconfigure(
            index,
            label=f'{label} ({self.logfile_date.strftime("%Y-%m-%d")})')

    def save_mem_as_txt(self):
        now = datetime.now()
        log_file = asksaveasfilename(
            title='wclog.db viewer', parent=self, initialdir='./LOG_DIARY',
            initialfile=f'{now.strftime("%Y-%m-%d")}.txt',
            filetypes=[('Log files', '*.txt')])
        if log_file:
            with open(log_file, 'w') as fd:
                today = datetime.now().date()
                with Session(self.engine) as session:
                    for sample in session.scalars(select(md.Sample)):
                        if today:
                            print(today.strftime('%Y-%m-%d'), file=fd)
                            today = None
                        sample_day = datetime.strptime(
                            sample.time, '%Y-%m-%d %H:%M:%S').date()
                        print(sample, file=fd)
                        # if sample_day == today:
                        #     pass
                        # else:
                        #     raise ValueError()

    def narrow_to_date(self):
        # stamp str -> datetime obj
        if not hasattr(self, 'req_date'):
            setattr(self, 'req_date', None)
        try:
            req_date = datetime.strptime(
                self.get_var('stamp').get(), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            req_date = None
        if self.req_date == req_date:
            req_date = None
        self.config(cursor='watch')
        _t = threading.Thread(target=self.update_log_list, args=(req_date, ))
        _t.start()
        self.req_date = req_date

    def create_form_fields(self, form) -> int:
        """Create form fields and their StringVar -s

        see self.form_vars dict
        """
        for row, fld_name in enumerate(LogRecord.__fields__):
            _ = tk.Label(form, text=fld_name)
            _.grid(column=0, row=row, sticky=tk.E)
            var = self.get_var(fld_name)
            if fld_name == 'stamp':
                _ = Time4(form, time4variable=var)
                padx = 1
            elif fld_name.startswith('label'):
                _ = ComboDb(form, self.engine, textvariable=var)
                _.update_values()
                padx = 2
            else:
                _ = tk.Entry(form, textvariable=var)
                padx = 1
            _.bind("<Double-1>", self.muffle_click)
            _.grid(column=1, row=row, sticky=tk.W, padx=padx, pady=2)
        return row

    def muffle_click(self, event):
        return "break"

    def update_log_list(
            self,
            narrow_to_date: Optional[datetime.date] = None  # %Y-%m-%d
    ):
        """Update Treeview (.log_list)

        delete all view items, read all db records, add them to the view"""

        self.log_list.delete(*self.log_list.get_children(''))
        # Session = SA.sessionmaker(self.engine)
        on_date = True          # all samples
        if narrow_to_date:
            # narrow_to_date datetime obj -> date str
            date_str = narrow_to_date.strftime('%Y-%m-%d')
            on_date = (func.DATE(md.Sample.time) == date_str)
        with Session(self.engine) as session:
            for rec in session.scalars(select(md.Sample).where(on_date)):
                labels = [''] * 3
                for i in range(3):
                    try:
                        t = rec.tags[i].text
                    except IndexError:
                        t = ''
                    labels[i] = t
                log = LogRecord(
                    id=rec.id,
                    stamp=rec.time,
                    label1=labels[0],
                    label2=labels[1],
                    label3=labels[2],
                    volume=rec.volume,
                    note=rec.text if rec.text else '')
                self.log_list.insert_log(log)
        self.config(cursor='')

    def get_var(self, fld_name):
        """Return tk.StringVar "form variable" named FLD_NAME

        variable objects are stored in the self.form_vars
        dictionary. If the variable doesn't exist, it is created"""

        if fld_name not in self.form_vars:
            if fld_name == 'stamp':
                var = Time4Var()
            elif fld_name.startswith('label'):
                var = tk.StringVar()
            else:
                var = tk.StringVar()
            self.form_vars[fld_name] = var
        return self.form_vars[fld_name]

    def set_val(self, fld_name, value=''):
        """Set "form variable" value

        see get_var.__doc__"""

        var = self.get_var(fld_name)
        var.set(value)

    def make_new(self):
        """Set the form fields to defaults"""

        with Session(self.engine) as session:
            id = session.scalar(select(func.max(md.Sample.id)))
        self.form_vars['id'].set(str(id + 1) if isinstance(id, int) else '1')
        self.form_vars['stamp'].set(datetime.now())
        self.del_btn.config(state=tk.DISABLED)

    def make_tagged_sample(self, *tags):
        self.make_new()
        if not tags:
            tags = ('pee', )
        for n, tag in enumerate(tags, 1):
            assert n < 3
            self.form_vars[f'label{n}'].set(tag)

    def del_log(self):
        """Delete selected log record"""

        rec = self.get_logrecord()
        if askyesno(f"{os.path.basename(__file__)}",
                    f"Delete log id={rec.id}? ",
                    parent=self):
            Session = sessionmaker(self.engine)
            with Session() as session:
                delete_me = session.scalar(select(md.Sample).where(
                    md.Sample.id == rec.id))
                session.delete(delete_me)
                session.commit()
            self.update_log_list()

    def edit_log(self) -> None:
        """Add/update log record (Sample) to "sample" table"""

        rec = self.get_logrecord()
        # with SA.Session(self.engine) as session:
        with session_scope(self.engine) as session:
            sample = session.get(md.Sample, rec.id)
            if sample:
                if askyesno(f"{os.path.basename(__file__)}",
                            f"Log {rec.id} exists. Update? ",
                            parent=self):
                    session.update_sample(sample, rec)
            else:
                sample = md.Sample(id=rec.id, time=rec.stamp,
                                   volume=rec.volume, text=rec.note)
                session.add_sample(sample, rec)
        self.update_log_list()

    def update_fields(self, log_rec: LogRecord) -> None:
        """Update form Entry values"""

        for fld_name in LogRecord.__fields__:
            val = getattr(log_rec, fld_name)
            if fld_name == 'volume' and val is None:
                val = ''
            self.set_val(fld_name, val)

    def get_logrecord(self) -> LogRecord:
        '''Get 'form' fields, make a LogRecord from them, return'''

        values = []
        for fld_name in LogRecord.__fields__:
            var = self.get_var(fld_name)
            if fld_name.startswith('label'):
                values.append(var.get())
            else:
                values.append(var.get())
        return LogRecord.from_list(values)

    def on_treeview_select(self, event):
        log = self.log_list.selected_log
        if log:
            self.update_fields(log)
            self.del_btn.config(state=tk.NORMAL)


parser = argparse.ArgumentParser(
    prog='log_viewer.py',
    description="wclog db viewer",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--db', help='Database file (.db)',
                    default='./wclog.db')
parser.add_argument('--echo', action='store_true', default=False,
                    help='Print emitted SQL commands')
parser.add_argument('--temp', help='''
Db in memory. Could be copied to .txt file before destroying''',
                    action='store_true')


if __name__ == '__main__':
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    database_url = ('sqlite:///:memory:' if args.temp
                    else f'sqlite:///{args.db}')
    engine = create_engine(database_url, echo=args.echo)
    initialize(engine)
    v = LogViewer(engine)
    # create_engine(database_url, echo=args.echo))
    v.mainloop()
