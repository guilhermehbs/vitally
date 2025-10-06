import bcrypt

senha = "admin1009"
hashed = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
print(hashed.decode())
