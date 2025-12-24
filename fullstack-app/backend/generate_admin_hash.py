#!/usr/bin/env python3
"""
Script para generar el hash de la contraseña de administrador.
Ejecuta: python generate_admin_hash.py
"""
import bcrypt
import getpass

def main():
    print("=" * 50)
    print("Generador de Hash para Contraseña de Administrador")
    print("=" * 50)
    print()
    
    password = getpass.getpass("Ingresa la contraseña de administrador: ")
    if not password:
        print("Error: La contraseña no puede estar vacía")
        return
    
    confirm = getpass.getpass("Confirma la contraseña: ")
    if password != confirm:
        print("Error: Las contraseñas no coinciden")
        return
    
    # Generar hash
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    print()
    print("=" * 50)
    print("Hash generado exitosamente:")
    print("=" * 50)
    print()
    print(f"ADMIN_PASSWORD_HASH={password_hash}")
    print()
    print("Copia esta línea a tu archivo .env en el backend")
    print("=" * 50)

if __name__ == "__main__":
    main()
