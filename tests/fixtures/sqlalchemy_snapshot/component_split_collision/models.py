from sqlalchemy import Table

first = Table("b.c", object(), schema="a")
second = Table("c", object(), schema="a.b")
