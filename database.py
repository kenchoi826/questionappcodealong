import sqlite3
import psycopg2
from psycopg2.extras import DictCursor
from flask import g

# def connect_db():
#     sql = sqlite3.connect('questions.db')
#     sql.row_factory = sqlite3.Row
#     return sql    

# def get_db():
#     if not hasattr(g, 'sqlite_db'):
#         g.sqlite_db = connect_db() 
#     return g.sqlite_db

def connect_db():
    conn = psycopg2.connect('postgres://nxrbrctpsxrilx:89469b83e6202a20d1aa3406c671ff584e98dd903e2ae51d93aa12af07c4ae94@ec2-54-227-243-210.compute-1.amazonaws.com:5432/d863hfc9uheorl',cursor_factory=DictCursor)
    conn.autocommit = True
    sql = conn.cursor()
    return conn, sql

def get_db():
    db = connect_db()

    if not hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn = db[0]

    if not hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur = db[1]

    return g.postgres_db_cur

def init_db():
    db = connect_db()

    db[1].execute(open('questions.sql','r').read())
    db[1].close()

    db[0].close()

def init_admin():
    db = connect_db()

    db[1].execute('update users set admin = True where name = %s',('admin',))
    db[1].close()
    db[0].close()





