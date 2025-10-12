import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('imss_pension.db')
cursor = conn.cursor()

# Ver usuarios actuales
print("Usuarios actuales:")
cursor.execute("SELECT id, email, analisis_restantes, total_analisis FROM users")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Email: {row[1]}, Créditos: {row[2]}, Total: {row[3]}")

# Resetear créditos (ajusta el ID o email según necesites)
cursor.execute("UPDATE users SET analisis_restantes = 1000 WHERE id = 1")
conn.commit()

print("\n✅ Créditos actualizados")

# Verificar
cursor.execute("SELECT id, email, analisis_restantes FROM users WHERE id = 1")
user = cursor.fetchone()
print(f"Usuario ID {user[0]}: {user[1]} ahora tiene {user[2]} créditos")

conn.close()
