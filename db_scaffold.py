import psycopg2
import sys


conn_string = "host=xxx.xxx.xxx.xxx dbname=xxxxxxx user=xxxxxxx password=xxxxxxx port=5432"
try:
   from dev_settings import *
except ImportError:
       pass

conn = psycopg2.connect(conn_string)
tfilter = sys.argv[1]
print(tfilter)

t= """select table_name from information_schema.tables where table_name like '""" + tfilter +"""' """
cur_t = conn.cursor()
cur_t.execute(t)
tbls = cur_t.fetchall()

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
        ) AS column_comment
    FROM information_schema.columns cols
    WHERE table_name = '""" + tname + "';"

    print (q)
    cur = conn.cursor()
    cur.execute(q, ('BADGES_SFR',))  # (table_name,) passed as tuple
    fields = cur.fetchall()

    module_text="""
    # -*- coding: utf-8 -*-
    from odoo import models, fields, api, _
    from odoo.exceptions import ValidationError

    import logging
    _logger = logging.getLogger(__name__)


    class """ + tname.replace(".","_") + """(models.Model):
        _name = '""" + tname+ """'
        _description = '""" + tname.replace(".","_") + """'
        _auto = False
        _table = '""" + tname + """'  \n \n"""
    
    security_text= """id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
    access_""" + tname.replace(".","_")  +""",access_""" + tname.replace(".","_")  +""",sotras-sot.model_""" + tname.replace(".","_")  +""",sotras-main.sotras_group_user,1,0,0,0
    manage_""" + tname.replace(".","_")  +""",manage_""" + tname.replace(".","_")  +""",sotras-sot.model_""" + tname.replace(".","_")  +""",sotras-main.sotras_group_manager,1,1,1,1

    """
    
    form_tree = """<!-- """ + tname.replace(".","_") + """ tree -->
            <record id=\"""" + tname.replace(".","_") + """_tree" model="ir.ui.view">
                <field name="name">SOTraS """ + tname.replace("."," ") + """ tree</field>
                <field name="model">""" + tname + """</field>
                <field name="arch" type="xml">

                    <tree default_order="name" create="0" delete="0">
                        #######
                    </tree>

                </field>
            </record>
    """

    form_menu = """
            <!-- """ + tname.replace(".","_") + """ action -->
            <record id="view_""" + tname.replace(".","_") + """_action" model="ir.actions.act_window">
                <field name="name">""" + tname.replace(".","_") + """</field>
                <field name="res_model">""" + tname + """</field>
                <field name="view_mode">tree</field>
                <field name="view_id" ref=\"""" + tname.replace(".","_") + """_tree"/>
            </record>


            <!-- """ + tname.replace(".","_") + """ menu -->
            <menuitem id="view_""" + tname.replace(".","_") + """_menu\"
                name=\"""" + tname.replace(".","_") + """\"
                parent=\"sotras-sot.main_sot_menut\"
                sequence=\"40\"
                action=\"view_""" + tname.replace(".","_") + """_action\"
                groups=\"sotras-main.sotras_group_manager\"
            />
    """

    for f in fields:
        print (f[0], f[1], f[3])
        label = (f[3] or f[0]).replace('\'','\'\'')
        module_text = module_text + "\n\t" + f[0] + "="
        if (f[1] == "character varying"):
            module_text += "fields.Char("
        elif (f[1] == "text"):
            module_text += "fields.Text("
        elif (f[1] == "date"):
                module_text += "fields.Date("
        elif (f[1] == "integer"):
                module_text += "fields.Integer("
        elif (f[1] == "numeric" or f[1] == "double precision"  ):
                module_text += "fields.Float("
        elif (f[1] == "boolean"):
                module_text += "fields.Boolean("
        elif (f[1].startswith("timestamp")):
                module_text += "fields.Datetime("
        else:
                module_text += "fields."+ f[1] + "(********************************************************************"
        module_text += "string = '" + f[0] +"', "
        module_text += "help = '" + label +"', "
        
        if (f[2] == 'NO' ):
            module_text += " Required = 'true',  "
        
        module_text += ")"

        form_tree = form_tree.replace("#######", "\t\t\t\t<field name = \"" + f[0] + "\" />\n#######")

    form_tree = form_tree.replace("#######", "\n")

    print (module_text)

    view_text = """<?xml version="1.0" encoding="utf-8"?>
    <odoo>
        <data>
    """ + form_tree + """
    """ + form_menu + """

        </data>
    </odoo>"""

    print (view_text)
    f = open("results/" + tname.replace(".","_")+".py", "w+")
    f.write(module_text)
    f.close()
    f = open("results/" + tname.replace(".","_")+"_view.xml", "w+")
    f.write(view_text)
    f.close()
    f = open("results/" + tname.replace(".","_")+"_security.csv", "w+")
    f.write(security_text)
    f.close()
