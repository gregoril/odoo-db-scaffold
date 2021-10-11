import psycopg2
import sys
import os
import os.path


CONN_STRING = "host=xxx.xxx.xxx.xxx dbname=xxxxxxx user=xxxxxxx password=xxxxxxx port=5432"
MODEL_NAME = "mymodel"
MODEL_LONG_NAME = "My Model"
GROUP_USER = "mymodel.group_user"
GROUP_MANAGER = "mymodel.group_manager"
MODEL_PREFIX = ""
BASE_PATH = "./"  # remember final /
try:
    from dev_settings import *
except ImportError:
    print("Missing dev_settings.py ")
    sys.exit()
    pass

if not os.path.exists(BASE_PATH+"results/models"):
    os.makedirs(BASE_PATH+"results/models")

if not os.path.exists(BASE_PATH+"results/views"):
    os.makedirs(BASE_PATH+"results/views")

if not os.path.exists(BASE_PATH+"results/security"):
    os.makedirs(BASE_PATH+"results/security")


conn = psycopg2.connect(CONN_STRING)
tfilter = "%"
if len(sys.argv) < 2 and TFILTER == False:
    print('usage: py db_scaffold.py <table pattern> \n eg.  py db_scaffold.py customers%    <- scaffold all tables whose name start with customers')
    sys.exit()
else:
    tfilter = TFILTER or sys.argv[1]
    
    print(tfilter)

t = """select table_name from information_schema.tables where table_schema like 'public' and  table_name like '""" + \
    tfilter + """' order by 1"""
cur_t = conn.cursor()
cur_t.execute(t)
tbls = cur_t.fetchall()

ft_sql = ""

for tbl in tbls:
    tname = tbl[0]
    q = """                              
    SELECT column_name, data_type, is_nullable, (
            SELECT
                pg_catalog.col_description(c.oid, cols.ordinal_position::int)
            FROM
                pg_catalog.pg_class c
            WHERE
                c.oid = (SELECT ('"' || cols.table_name || '"')::regclass::oid)
                AND c.relname = cols.table_name
        ) AS column_comment, udt_name
    FROM information_schema.columns cols
    WHERE table_name = '""" + tname + "';"

    print(q)
    tname = MODEL_PREFIX+tname
    cur = conn.cursor()
    cur.execute(q, ('BADGES_SFR',))  # (table_name,) passed as tuple
    fields = cur.fetchall()

    module_text = """# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class """ + tname.replace(".", "_") + """(models.Model):
    _name = '""" + tname + """'
    _description = '""" + tname.replace(".", "_") + """'
    _auto = False
    _table = '""" + tname + """'  \n \n"""

    security_text = """access_""" + tname.replace(".", "_") + """,access_""" + tname.replace(".", "_") + """,""" + MODEL_NAME + """.model_""" + tname.replace(".", "_") + """,""" + GROUP_USER + """,1,0,0,0
manage_""" + tname.replace(".", "_") + """,manage_""" + tname.replace(".", "_") + """,""" + MODEL_NAME + """.model_""" + tname.replace(".", "_") + """,""" + GROUP_MANAGER + """,1,1,1,1
"""

    form_tree = """
        <!-- """ + tname.replace(".", "_") + """ tree -->
            <record id=\"""" + tname.replace(".", "_") + """_tree" model="ir.ui.view">
                <field name="name">""" + MODEL_LONG_NAME + " " + tname.replace(".", " ") + """ tree</field>
                <field name="model">""" + tname + """</field>
                <field name="arch" type="xml">

                    <tree default_order="name" create="0" delete="0">
                        #######
                    </tree>

                </field>
            </record>
    """
    form_search = """
<!-- """ + tname.replace(".", "_") + """ search -->
            <record id=\"""" + tname.replace(".", "_") + """_search" model="ir.ui.view">
                <field name="name">""" + MODEL_LONG_NAME + " " + tname.replace(".", " ") + """ tree</field>
                <field name="model">""" + tname + """</field>
                <field name="arch" type="xml">
                     <search string="Search ">
                        #######
                    </search>

                </field>
            </record>
    """
    form_form = """
<!-- """ + tname.replace(".", "_") + """ form -->
            <record id=\"""" + tname.replace(".", "_") + """_form" model="ir.ui.view">
                <field name="name">""" + MODEL_LONG_NAME + " " + tname.replace(".", " ") + """ form</field>
                <field name="model">""" + tname + """</field>
                <field name="arch" type="xml">
                     <form string="Dati ">
                     <header>
                     </header>
                     <sheet>
                        #######
                        <navigation>
                        <page>
                        </page>
                        </navigation>
                    <sheet>
                    </form>

                </field>
            </record>
    """


    form_menu = """
        <!-- """ + tname.replace(".", "_") + """ action -->
        <record id="view_""" + tname.replace(".", "_") + """_action" model="ir.actions.act_window">
            <field name="name">""" + tname.replace(".", "_") + """</field>
            <field name="res_model">""" + tname + """</field>
            <field name="view_mode">tree</field>
            <field name="view_id" ref=\"""" + tname.replace(".", "_") + """_tree"/>
        </record>


        <!-- """ + tname.replace(".", "_") + """ menu -->
        <menuitem id="view_""" + tname.replace(".", "_") + """_menu\"
            name=\"""" + tname.replace(".", "_") + """\"
            parent=\"""" + MODEL_NAME + """.main_menu\"
            sequence=\"40\"
            action=\"view_""" + tname.replace(".", "_") + """_action\"
            groups=\"""" + GROUP_MANAGER + """\"
        />
"""
    ft_sql += "CREATE FOREIGN TABLE " + tname + " ("
    for f in fields:
        print(f[0], f[1], f[3])
        ft_sql += "\n    " + f[0] + " \t" + f[1] + ","
        label = (f[3] or f[0]).replace('\'', '\'\'')
        module_text = module_text + "\n    " + f[0] + "="
        if (f[1] == "character varying"):
            module_text += "fields.Char("
        elif (f[1] == "text"):
            module_text += "fields.Text("
        elif (f[1] == "json"):
            module_text += "fields.Text("
        elif (f[1] == "date"):
            module_text += "fields.Date("
        elif (f[1] == "integer"):
            module_text += "fields.Integer("
        elif (f[1] == "numeric" or f[1] == "double precision"):
            module_text += "fields.Float("
        elif (f[1] == "boolean"):
            module_text += "fields.Boolean("
        elif (f[1].startswith("timestamp")):
            module_text += "fields.Datetime("
        elif (f[4].startswith("geometry")):
            if f[0].endswith("_line"):
                module_text += "fields.GeoLine("
            if f[0].endswith("_mline"):
                module_text += "fields.GeoMultiLine("
            if f[0].endswith("_poly"):
                module_text += "fields.GeoPolygon("
            if f[0].endswith("_mpoly"):
                module_text += "fields.GeoMultiPolygon("
            if f[0].endswith("_mpoint"):
                module_text += "fields.GeoMultiPoint("
            else:
                module_text += "fields.GeoPoint("
        else:
            module_text += "#fields." + \
                f[1] + "(********************************************************************"
        module_text += "string = '" + f[0] + "', "
        module_text += "help = '" + label + "', "

        if (f[2] == 'NO'):
            module_text += " Required = 'true',  "

        module_text += ")"
        if f[0] not in ['created_at', 'updated_at', 'created_uid', 'updated_uid', ]:
            widget= ' widget="url" ' if '_url' in f[0] else ''
            widget= ' widget="html" ' if '_html' in f[0] else ''
            widget= ' widget="email" ' if 'email' in f[0] else ''
                        
            form_tree = form_tree.replace(
                "#######", "\t\t\t\t<field name = \"" + f[0] + widget + "\" />\n#######")
            form_search = form_search.replace(
                "#######", "\t\t\t\t<field name = \"" + f[0] + "\" />\n#######")
            form_form = form_search.replace(
                "#######", "\t\t\t\t<field name = \"" + f[0] + widget + "\" />\n#######")

    ft_sql = ft_sql[:-1]
    ft_sql += ")\nSERVER " + MODEL_PREFIX + \
        "db OPTIONS (schema_name 'public', table_name '" + tbl[0] + "');\n "

    form_tree = form_tree.replace("#######", "\n")
    form_search = form_search.replace("#######", "\n")
    form_form = form_form.replace("#######", "\n")

    print(module_text)

    view_text = """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        """ + form_form + """
        """ + form_tree + """
        """ + form_search + """
        """ + form_menu + """

    </data>
</odoo>"""

    print(view_text)
    f = open(BASE_PATH+"results/models/" + tname.replace(".", "_")+".py", "w+")
    f.write(module_text)
    f.close()
    f = file_object = open(BASE_PATH+"results/models/__init__.py", "a")
    f.write("from . import " + tname.replace(".", "_") + "\n")
    f.close

    f = open(BASE_PATH+"results/views/" +
             tname.replace(".", "_")+"_view.xml", "w+")
    f.write(view_text)
    f.close()
    f = file_object = open(BASE_PATH+"results/__manifest_view.txt", "a")
    f.write("'views/" + tname.replace(".", "_") + "_view.xml',\n")
    f.close
    if not os.path.exists(BASE_PATH+"results/security/ir.model.access.csv"):
        f = open(BASE_PATH+"results/security/ir.model.access.csv", "w")
        f.write(
            "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink")
    else:
        f = open(BASE_PATH+"results/security/ir.model.access.csv", "a")
    f.write(security_text)
    f.close()
    
    f = open(BASE_PATH+"results/foreign_tables.sql", "w+")
    f.write(ft_sql)
    f.close()

