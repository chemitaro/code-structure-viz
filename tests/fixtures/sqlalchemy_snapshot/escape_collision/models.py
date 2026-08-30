from sqlalchemy import Table

quoted = Table('"', object())
encoded = Table("_U0022_", object())
