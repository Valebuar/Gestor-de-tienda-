import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error
from config import DATABASE_CONFIG
from tabulate import tabulate
from tkcalendar import DateEntry

# Clase de conexxion a la base de datos 
class DatabaseConnection:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = ""
        self.database = database
        self.connection = None
        self.cursor = None
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=3306,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor()
            return True
        except Error as e:
            messagebox.showerror("Error de Conexión", f"Error al conectar con la base de datos: {e}")
            return False
    
    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        try:
            if self.connection is None or not self.connection.is_connected():
                if not self.connect():
                    return False
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return True
        except Error as e:
            messagebox.showerror("Error de Base de Datos", f"Error al ejecutar consulta: {e}")
            return False
    
    def fetch_all(self, query, params=None):
        try:
            if self.connection is None or not self.connection.is_connected():
                if not self.connect():
                    return []
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as e:
            messagebox.showerror("Error de Base de Datos", f"Error al obtener datos: {e}")
            return []

    def create_tables(self):
        """Crear las tablas si no existen"""
        tablas = [
            '''CREATE TABLE IF NOT EXISTS Clientes (
                cliente_id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                telefono VARCHAR(15),
                direccion VARCHAR(150)
            )''',
            '''CREATE TABLE IF NOT EXISTS Productos (
                producto_id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                descripcion TEXT,
                precio DECIMAL(10,2) NOT NULL,
                stock INT NOT NULL
            )''',
            '''CREATE TABLE IF NOT EXISTS Categorias (
                categoria_id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(50) NOT NULL,
                descripcion TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS Ventas (
                venta_id INT AUTO_INCREMENT PRIMARY KEY,
                cliente_id INT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                total DECIMAL(10,2),
                FOREIGN KEY (cliente_id) REFERENCES Clientes(cliente_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS DetalleVentas (
                detalle_id INT AUTO_INCREMENT PRIMARY KEY,
                venta_id INT,
                producto_id INT,
                cantidad INT NOT NULL,
                precio_unitario DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES Ventas(venta_id),
                FOREIGN KEY (producto_id) REFERENCES Productos(producto_id)
            )'''
        ]
        if self.connection is None or not self.connection.is_connected():
            if not self.connect():
                return False
        for query in tablas:
            try:
                self.cursor.execute(query)
            except Error as e:
                messagebox.showerror("Error de Base de Datos", f"Error al crear tabla: {e}")
                return False
        self.connection.commit()
        return True


# Crear instancia de conexión usando la configuración importada
db = DatabaseConnection(**DATABASE_CONFIG)

# Conectar y crear tablas al iniciar
if db.connect():
    db.create_tables()

# Crear la ventana principal
root = tk.Tk()
root.geometry('800x400')
root.title("GESTOR DE TIENDA")

# Crear el widget Notebook (pestañas)
notebook = ttk.Notebook(root)

# Crear los frames que irán dentro de las pestañas
tab_clientes = ttk.Frame(notebook)
tab_productos = ttk.Frame(notebook)
tab_categorias = ttk.Frame(notebook)
tab_ventas = ttk.Frame(notebook)
tab_detalle_ventas = ttk.Frame(notebook)

# Añadir las pestañas al Notebook
notebook.add(tab_clientes, text="Clientes")
notebook.add(tab_productos, text="Productos")
notebook.add(tab_categorias, text="Categorias")
notebook.add(tab_ventas, text="Ventas")
notebook.add(tab_detalle_ventas, text="DetalleVentas")

# Empaquetar el Notebook para que se muestre en la ventana
notebook.pack(expand=True, fill="both")

# Tabla base de datos 
def obtener_tablas():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tablas = [t[0] for t in cur.fetchall()]
    conn.close()
    return tablas

def obtener_datos_tabla(tabla):
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {tabla}")
    columnas = [desc[0] for desc in cur.description]
    datos = cur.fetchall()
    conn.close()
    return columnas, datos


# PESTAÑA CLIENTES
# Filtro de búsqueda por nombre
frame_filtro_clientes = tk.Frame(tab_clientes)
frame_filtro_clientes.pack(padx=50, pady=(0,10), anchor="w")
tk.Label(frame_filtro_clientes, text="Buscar por nombre:", font=("Arial", 12)).pack(side=tk.LEFT)
filtro_nombre_cliente = tk.Entry(frame_filtro_clientes, width=20, font=("Arial", 12))
filtro_nombre_cliente.pack(side=tk.LEFT, padx=5)

def filtrar_clientes():
    nombre = filtro_nombre_cliente.get()
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    if nombre:
        cur.execute("SELECT * FROM Clientes WHERE nombre LIKE %s", (f"%{nombre}%",))
    else:
        cur.execute("SELECT * FROM Clientes")
    rows = cur.fetchall()
    conn.close()
    tree_clientes.delete(*tree_clientes.get_children())
    for row in rows:
        tree_clientes.insert('', 'end', values=row)

btn_filtrar_cliente = tk.Button(frame_filtro_clientes, text="Filtrar", command=filtrar_clientes)
btn_filtrar_cliente.pack(side=tk.LEFT, padx=5)
titulo_clientes = tk.Label(tab_clientes, text="Gestión de Clientes", font=("Arial", 16, "bold"), fg="blue")
titulo_clientes.pack(pady=20)

form_clientes = tk.Frame(tab_clientes)
form_clientes.pack(pady=20, anchor="w", padx=50)

# Treeview para mostrar registros de clientes
# Treeview para mostrar registros de clientes
tree_clientes = ttk.Treeview(tab_clientes)
tree_clientes.pack(fill="x", padx=50, pady=10)
tree_clientes['columns'] = ('cliente_id', 'nombre', 'telefono', 'direccion')
tree_clientes['show'] = 'headings'
for col in tree_clientes['columns']:
    tree_clientes.heading(col, text=col)
    tree_clientes.column(col, width=120)

def copiar_a_formulario_cliente(event):
    seleccionado = tree_clientes.focus()
    if seleccionado:
        valores = tree_clientes.item(seleccionado, 'values')
        nombre_cliente.delete(0, tk.END)
        telefono_cliente.delete(0, tk.END)
        direccion_cliente.delete(0, tk.END)
        nombre_cliente.insert(0, valores[1])
        telefono_cliente.insert(0, valores[2])
        direccion_cliente.insert(0, valores[3])

tree_clientes.bind('<<TreeviewSelect>>', copiar_a_formulario_cliente)

def cargar_clientes():
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    cur.execute("SELECT * FROM Clientes")
    rows = cur.fetchall()
    conn.close()
    tree_clientes.delete(*tree_clientes.get_children())
    for row in rows:
        tree_clientes.insert('', 'end', values=row)

cargar_clientes()

# Dato 1 : Nombre
tk.Label(form_clientes, text="Nombre:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=10)
nombre_cliente = tk.Entry(form_clientes, width=25, font=("Arial", 12), relief="solid", bd=1)
nombre_cliente.grid(row=1, column=1, sticky="w", pady=10)

# Dato 2: Teléfono
tk.Label(form_clientes, text="Teléfono:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", padx=(0, 10), pady=10)
telefono_cliente = tk.Entry(form_clientes, width=25, font=("Arial", 12), relief="solid", bd=1)
telefono_cliente.grid(row=3, column=1, sticky="w", pady=10)

# Dato 3: Dirección
tk.Label(form_clientes, text="Dirección:", font=("Arial", 12)).grid(row=4, column=0, sticky="w", padx=(0, 10), pady=10)
direccion_cliente = tk.Entry(form_clientes, width=25, font=("Arial", 12), relief="solid", bd=1)
direccion_cliente.grid(row=4, column=1, sticky="w", pady=10)

# Botones de acción
button_frame = tk.Frame(tab_clientes)
button_frame.pack(pady=20)

def guardar_cliente():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO Clientes (nombre, telefono, direccion) VALUES (%s, %s, %s)",
                (nombre_cliente.get(), telefono_cliente.get(), direccion_cliente.get()))
    conn.commit()
    conn.close()
    nombre_cliente.delete(0, tk.END)
    telefono_cliente.delete(0, tk.END)
    direccion_cliente.delete(0, tk.END)
    cargar_clientes()
    messagebox.showinfo("Guardado", "Cliente guardado correctamente.")

def actualizar_cliente():
    seleccionado = tree_clientes.focus()
    if not seleccionado:
        messagebox.showwarning("Advertencia", "Selecciona un registro para actualizar.")
        return
    valores = tree_clientes.item(seleccionado, 'values')
    cliente_id = valores[0]
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    cur.execute("UPDATE Clientes SET nombre=%s, telefono=%s, direccion=%s WHERE cliente_id=%s",
                (nombre_cliente.get(), telefono_cliente.get(), direccion_cliente.get(), cliente_id))
    conn.commit()
    conn.close()
    cargar_clientes()
    messagebox.showinfo("Actualizado", "Cliente actualizado correctamente.")

def eliminar_cliente():
    seleccionado = tree_clientes.focus()
    if not seleccionado:
        messagebox.showwarning("Advertencia", "Selecciona un registro para eliminar.")
        return
    valores = tree_clientes.item(seleccionado, 'values')
    cliente_id = valores[0]
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    cur.execute("DELETE FROM Clientes WHERE cliente_id=%s", (cliente_id,))
    conn.commit()
    conn.close()
    cargar_clientes()
    messagebox.showinfo("Eliminado", "Cliente eliminado correctamente.")

def limpiar_cliente():
    nombre_cliente.delete(0, tk.END)
    telefono_cliente.delete(0, tk.END)
    direccion_cliente.delete(0, tk.END)
    cargar_clientes()
    messagebox.showinfo("Limpiar", "Campos de cliente limpiados.")

btn_save = tk.Button(button_frame, text="Guardar", font=("Arial", 12), bg="#4CAF50", fg="white", width=10)
btn_save.pack(side=tk.LEFT, padx=5)

btn_update = tk.Button(button_frame, text="Actualizar", font=("Arial", 12), bg="#2196F3", fg="white", width=10)
btn_update.pack(side=tk.LEFT, padx=5)

btn_delete = tk.Button(button_frame, text="Eliminar", font=("Arial", 12), bg="#f44336", fg="white", width=10)
btn_delete.pack(side=tk.LEFT, padx=5)

btn_clear = tk.Button(button_frame, text="Limpiar", font=("Arial", 12), bg="#FF9800", fg="white", width=10)
btn_clear.pack(side=tk.LEFT, padx=5)

btn_save.config(command=guardar_cliente)
btn_update.config(command=actualizar_cliente)
btn_delete.config(command=eliminar_cliente)
btn_clear.config(command=limpiar_cliente)

# PESTAÑA PRODUCTOS 
# Filtro de búsqueda por nombre
frame_filtro_productos = tk.Frame(tab_productos)
frame_filtro_productos.pack(padx=50, pady=(0,10), anchor="w")
tk.Label(frame_filtro_productos, text="Buscar por nombre:", font=("Arial", 12)).pack(side=tk.LEFT)
filtro_nombre_producto = tk.Entry(frame_filtro_productos, width=20, font=("Arial", 12))
filtro_nombre_producto.pack(side=tk.LEFT, padx=5)

def filtrar_productos():
    nombre = filtro_nombre_producto.get()
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    if nombre:
        cur.execute("SELECT * FROM Productos WHERE nombre LIKE %s", (f"%{nombre}%",))
    else:
        cur.execute("SELECT * FROM Productos")
    rows = cur.fetchall()
    conn.close()
    tree_productos.delete(*tree_productos.get_children())
    for row in rows:
        tree_productos.insert('', 'end', values=row)

btn_filtrar_producto = tk.Button(frame_filtro_productos, text="Filtrar", command=filtrar_productos)
btn_filtrar_producto.pack(side=tk.LEFT, padx=5)
titulo_productos = tk.Label(tab_productos, text="Gestión de Productos", font=("Arial", 16, "bold"), fg="green")
titulo_productos.pack(pady=20)

form_productos = tk.Frame(tab_productos)
form_productos.pack(pady=20, anchor="w", padx=50)

# Treeview para mostrar registros de productos
# Treeview para mostrar registros de productos
tree_productos = ttk.Treeview(tab_productos)
tree_productos.pack(fill="x", padx=50, pady=10)
tree_productos['columns'] = ('producto_id', 'nombre', 'descripcion', 'precio', 'stock')
tree_productos['show'] = 'headings'
for col in tree_productos['columns']:
    tree_productos.heading(col, text=col)
    tree_productos.column(col, width=120)

def copiar_a_formulario_producto(event):
    seleccionado = tree_productos.focus()
    if seleccionado:
        valores = tree_productos.item(seleccionado, 'values')
        nombre_producto.delete(0, tk.END)
        descripcion_producto.delete(0, tk.END)
        precio_producto.delete(0, tk.END)
        stock_producto.delete(0, tk.END)
        nombre_producto.insert(0, valores[1])
        descripcion_producto.insert(0, valores[2])
        precio_producto.insert(0, valores[3])
        stock_producto.insert(0, valores[4])

tree_productos.bind('<<TreeviewSelect>>', copiar_a_formulario_producto)

def cargar_productos():
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    cur.execute("SELECT * FROM Productos")
    rows = cur.fetchall()
    conn.close()
    tree_productos.delete(*tree_productos.get_children())
    for row in rows:
        tree_productos.insert('', 'end', values=row)

cargar_productos()

# Dato 1 : Nombre
tk.Label(form_productos, text="Nombre:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=10)
nombre_producto = tk.Entry(form_productos, width=25, font=("Arial", 12), relief="solid", bd=1)
nombre_producto.grid(row=1, column=1, sticky="w", pady=10)

# Dato 2: Descripción
tk.Label(form_productos, text="Descripción:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=10)
descripcion_producto = tk.Entry(form_productos, width=25, font=("Arial", 12), relief="solid", bd=1)
descripcion_producto.grid(row=2, column=1, sticky="w", pady=10)

# Dato 3: Precio
tk.Label(form_productos, text="Precio:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", padx=(0, 10), pady=10)
precio_producto = tk.Entry(form_productos, width=25, font=("Arial", 12), relief="solid", bd=1)
precio_producto.grid(row=3, column=1, sticky="w", pady=10)

# Dato 4: Stock
tk.Label(form_productos, text="Stock:", font=("Arial", 12)).grid(row=4, column=0, sticky="w", padx=(0, 10), pady=10)
stock_producto = tk.Entry(form_productos, width=25, font=("Arial", 12), relief="solid", bd=1)
stock_producto.grid(row=4, column=1, sticky="w", pady=10)

# Botones de acción
button_productos = tk.Frame(tab_productos)
button_productos.pack(pady=20)
def guardar_producto():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO Productos (nombre, descripcion, precio, stock) VALUES (%s, %s, %s, %s)",
                (nombre_producto.get(), descripcion_producto.get(), precio_producto.get(), stock_producto.get()))
    conn.commit()
    conn.close()
    nombre_producto.delete(0, tk.END)
    descripcion_producto.delete(0, tk.END)
    precio_producto.delete(0, tk.END)
    stock_producto.delete(0, tk.END)
    cargar_productos()
    messagebox.showinfo("Guardado", "Producto guardado correctamente.")

def actualizar_producto():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("UPDATE Productos SET descripcion=%s, precio=%s, stock=%s WHERE nombre=%s",
                (descripcion_producto.get(), precio_producto.get(), stock_producto.get(), nombre_producto.get()))
    conn.commit()
    conn.close()
    cargar_productos()
    messagebox.showinfo("Actualizado", "Producto actualizado correctamente.")

def eliminar_producto():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("DELETE FROM Productos WHERE nombre=%s", (nombre_producto.get(),))
    conn.commit()
    conn.close()
    nombre_producto.delete(0, tk.END)
    descripcion_producto.delete(0, tk.END)
    precio_producto.delete(0, tk.END)
    stock_producto.delete(0, tk.END)
    cargar_productos()
    messagebox.showinfo("Eliminado", "Producto eliminado correctamente.")

def limpiar_producto():
    nombre_producto.delete(0, tk.END)
    descripcion_producto.delete(0, tk.END)
    precio_producto.delete(0, tk.END)
    stock_producto.delete(0, tk.END)
    cargar_productos()
    messagebox.showinfo("Limpiar", "Campos de producto limpiados.")

btn_save_producto = tk.Button(button_productos, text="Guardar", font=("Arial", 12), bg="#4CAF50", fg="white", width=10)
btn_save_producto.pack(side=tk.LEFT, padx=5)

btn_update_producto = tk.Button(button_productos, text="Actualizar", font=("Arial", 12), bg="#2196F3", fg="white", width=10)
btn_update_producto.pack(side=tk.LEFT, padx=5)

btn_delete_producto = tk.Button(button_productos, text="Eliminar", font=("Arial", 12), bg="#f44336", fg="white", width=10)
btn_delete_producto.pack(side=tk.LEFT, padx=5)

btn_clear_producto = tk.Button(button_productos, text="Limpiar", font=("Arial", 12), bg="#FF9800", fg="white", width=10)
btn_clear_producto.pack(side=tk.LEFT, padx=5)

btn_save_producto.config(command=guardar_producto)
btn_update_producto.config(command=actualizar_producto)
btn_delete_producto.config(command=eliminar_producto)
btn_clear_producto.config(command=limpiar_producto)

# PESTAÑA CATEGORIAS
# Filtro de búsqueda por nombre
frame_filtro_categorias = tk.Frame(tab_categorias)
frame_filtro_categorias.pack(padx=50, pady=(0,10), anchor="w")
tk.Label(frame_filtro_categorias, text="Buscar por nombre:", font=("Arial", 12)).pack(side=tk.LEFT)
filtro_nombre_categoria = tk.Entry(frame_filtro_categorias, width=20, font=("Arial", 12))
filtro_nombre_categoria.pack(side=tk.LEFT, padx=5)

def filtrar_categorias():
    nombre = filtro_nombre_categoria.get()
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    if nombre:
        cur.execute("SELECT * FROM Categorias WHERE nombre LIKE %s", (f"%{nombre}%",))
    else:
        cur.execute("SELECT * FROM Categorias")
    rows = cur.fetchall()
    conn.close()
    tree_categorias.delete(*tree_categorias.get_children())
    for row in rows:
        tree_categorias.insert('', 'end', values=row)

btn_filtrar_categoria = tk.Button(frame_filtro_categorias, text="Filtrar", command=filtrar_categorias)
btn_filtrar_categoria.pack(side=tk.LEFT, padx=5)
titulo_categorias = tk.Label(tab_categorias, text="Gestión de Categorias", font=("Arial", 16, "bold"), fg="purple")
titulo_categorias.pack(pady=20)

form_categorias = tk.Frame(tab_categorias)
form_categorias.pack(pady=20, anchor="w", padx=50)

# Treeview para mostrar registros de categorias
# Treeview para mostrar registros de categorias
tree_categorias = ttk.Treeview(tab_categorias)
tree_categorias.pack(fill="x", padx=50, pady=10)
tree_categorias['columns'] = ('categoria_id', 'nombre', 'descripcion')
tree_categorias['show'] = 'headings'
for col in tree_categorias['columns']:
    tree_categorias.heading(col, text=col)
    tree_categorias.column(col, width=120)

def copiar_a_formulario_categoria(event):
    seleccionado = tree_categorias.focus()
    if seleccionado:
        valores = tree_categorias.item(seleccionado, 'values')
        nombre_categoria.delete(0, tk.END)
        descripcion_categoria.delete(0, tk.END)
        nombre_categoria.insert(0, valores[1])
        descripcion_categoria.insert(0, valores[2])

tree_categorias.bind('<<TreeviewSelect>>', copiar_a_formulario_categoria)

def cargar_categorias():
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    cur.execute("SELECT * FROM Categorias")
    rows = cur.fetchall()
    conn.close()
    tree_categorias.delete(*tree_categorias.get_children())
    for row in rows:
        tree_categorias.insert('', 'end', values=row)

cargar_categorias()

# Dato 1 : Nombre
tk.Label(form_categorias, text="Nombre:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=10)
nombre_categoria = tk.Entry(form_categorias, width=25, font=("Arial", 12), relief="solid", bd=1)
nombre_categoria.grid(row=1, column=1, sticky="w", pady=10)

# Dato 2: Descripción
tk.Label(form_categorias, text="Descripción:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=10)
descripcion_categoria = tk.Entry(form_categorias, width=25, font=("Arial", 12), relief="solid", bd=1)
descripcion_categoria.grid(row=2, column=1, sticky="w", pady=10)

# Botones de acción
button_categorias = tk.Frame(tab_categorias)
button_categorias.pack(pady=20)

def guardar_categoria():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO Categorias (nombre, descripcion) VALUES (%s, %s)",
                (nombre_categoria.get(), descripcion_categoria.get()))
    conn.commit()
    conn.close()
    nombre_categoria.delete(0, tk.END)
    descripcion_categoria.delete(0, tk.END)
    cargar_categorias()
    messagebox.showinfo("Guardado", "Categoría guardada correctamente.")

def actualizar_categoria():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("UPDATE Categorias SET descripcion=%s WHERE nombre=%s",
                (descripcion_categoria.get(), nombre_categoria.get()))
    conn.commit()
    conn.close()
    cargar_categorias()
    messagebox.showinfo("Actualizado", "Categoría actualizada correctamente.")

def eliminar_categoria():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("DELETE FROM Categorias WHERE nombre=%s", (nombre_categoria.get(),))
    conn.commit()
    conn.close()
    nombre_categoria.delete(0, tk.END)
    descripcion_categoria.delete(0, tk.END)
    cargar_categorias()
    messagebox.showinfo("Eliminado", "Categoría eliminada correctamente.")

def limpiar_categoria():
    nombre_categoria.delete(0, tk.END)
    descripcion_categoria.delete(0, tk.END)
    cargar_categorias()
    messagebox.showinfo("Limpiar", "Campos de categoría limpiados.")


btn_save_categoria = tk.Button(button_categorias, text="Guardar", font=("Arial", 12), bg="#4CAF50", fg="white", width=10)
btn_save_categoria.pack(side=tk.LEFT, padx=5)

btn_update_categoria = tk.Button(button_categorias, text="Actualizar", font=("Arial", 12), bg="#2196F3", fg="white", width=10)
btn_update_categoria.pack(side=tk.LEFT, padx=5)

btn_delete_categoria = tk.Button(button_categorias, text="Eliminar", font=("Arial", 12), bg="#f44336", fg="white", width=10)
btn_delete_categoria.pack(side=tk.LEFT, padx=5)

btn_clear_categoria = tk.Button(button_categorias, text="Limpiar", font=("Arial", 12), bg="#FF9800", fg="white", width=10)
btn_clear_categoria.pack(side=tk.LEFT, padx=5)

btn_save_categoria.config(command=guardar_categoria)
btn_update_categoria.config(command=actualizar_categoria)
btn_delete_categoria.config(command=eliminar_categoria)
btn_clear_categoria.config(command=limpiar_categoria)


# PESTAÑA VENTAS
# Filtro de búsqueda por cliente_id
frame_filtro_ventas = tk.Frame(tab_ventas)
frame_filtro_ventas.pack(padx=50, pady=(0,10), anchor="w")
tk.Label(frame_filtro_ventas, text="Buscar por cliente_id:", font=("Arial", 12)).pack(side=tk.LEFT)
filtro_cliente_id_venta = tk.Entry(frame_filtro_ventas, width=20, font=("Arial", 12))
filtro_cliente_id_venta.pack(side=tk.LEFT, padx=5)

def filtrar_ventas():
    cliente_id = filtro_cliente_id_venta.get()
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    if cliente_id:
        cur.execute("SELECT * FROM Ventas WHERE cliente_id LIKE %s", (f"%{cliente_id}%",))
    else:
        cur.execute("SELECT * FROM Ventas")
    rows = cur.fetchall()
    conn.close()
    tree_ventas.delete(*tree_ventas.get_children())
    for row in rows:
        tree_ventas.insert('', 'end', values=row)

btn_filtrar_venta = tk.Button(frame_filtro_ventas, text="Filtrar", command=filtrar_ventas)
btn_filtrar_venta.pack(side=tk.LEFT, padx=5)
titulo_ventas = tk.Label(tab_ventas, text="Gestión de Pedidos", font=("Arial", 16, "bold"), fg="red")
titulo_ventas.pack(pady=20)

form_ventas = tk.Frame(tab_ventas)
form_ventas.pack(pady=20, anchor="w", padx=50)

# Treeview para mostrar registros de ventas
# Treeview para mostrar registros de ventas
tree_ventas = ttk.Treeview(tab_ventas)
tree_ventas.pack(fill="x", padx=50, pady=10)
tree_ventas['columns'] = ('venta_id', 'cliente_id', 'fecha', 'total')
tree_ventas['show'] = 'headings'
for col in tree_ventas['columns']:
    tree_ventas.heading(col, text=col)
    tree_ventas.column(col, width=120)

def copiar_a_formulario_venta(event):
    seleccionado = tree_ventas.focus()
    if seleccionado:
        valores = tree_ventas.item(seleccionado, 'values')
        cliente_id_ventas.delete(0, tk.END)
        fecha_ventas.delete(0, tk.END)
        total_ventas.delete(0, tk.END)
        cliente_id_ventas.insert(0, valores[1])
        fecha_ventas.insert(0, valores[2])
        total_ventas.insert(0, valores[3])

tree_ventas.bind('<<TreeviewSelect>>', copiar_a_formulario_venta)

def cargar_ventas():
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    cur.execute("SELECT * FROM Ventas")
    rows = cur.fetchall()
    conn.close()
    tree_ventas.delete(*tree_ventas.get_children())
    for row in rows:
        tree_ventas.insert('', 'end', values=row)

cargar_ventas()

# Dato 1 : Cliente ID
tk.Label(form_ventas, text="Cliente ID:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=10)
cliente_id_ventas = tk.Entry(form_ventas, width=25, font=("Arial", 12), relief="solid", bd=1)
cliente_id_ventas.grid(row=1, column=1, sticky="w", pady=10)

# Dato 2: Fecha Pedido
tk.Label(form_ventas, text="Fecha venta:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=10)
from tkcalendar import DateEntry
fecha_ventas = DateEntry(form_ventas, width=25, font=("Arial", 12), relief="solid", bd=1, date_pattern='y-mm-dd')
fecha_ventas.grid(row=2, column=1, sticky="w", pady=10)

# Dato 3: Total
tk.Label(form_ventas, text="Total:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", padx=(0, 10), pady=10)
total_ventas = tk.Entry(form_ventas, width=25, font=("Arial", 12), relief="solid", bd=1)
total_ventas.grid(row=3, column=1, sticky="w", pady=10)

# Botones de acción
button_ventas = tk.Frame(tab_ventas)
button_ventas.pack(pady=20)
def guardar_venta():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO Ventas (cliente_id, fecha, total) VALUES (%s, %s, %s)",
                (cliente_id_ventas.get(), fecha_ventas.get(), total_ventas.get()))
    conn.commit()
    conn.close()
    cliente_id_ventas.delete(0, tk.END)
    fecha_ventas.delete(0, tk.END)
    total_ventas.delete(0, tk.END)
    cargar_ventas()
    messagebox.showinfo("Guardado", "Venta guardada correctamente.")

def actualizar_venta():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("UPDATE Ventas SET cliente_id=%s, fecha=%s, total=%s WHERE venta_id=%s",
                (cliente_id_ventas.get(), fecha_ventas.get(), total_ventas.get(), cliente_id_ventas.get()))
    conn.commit()
    conn.close()
    cargar_ventas()
    messagebox.showinfo("Actualizado", "Venta actualizada correctamente.")

def eliminar_venta():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("DELETE FROM Ventas WHERE venta_id=%s", (cliente_id_ventas.get(),))
    conn.commit()
    conn.close()
    cliente_id_ventas.delete(0, tk.END)
    fecha_ventas.delete(0, tk.END)
    total_ventas.delete(0, tk.END)
    cargar_ventas()
    messagebox.showinfo("Eliminado", "Venta eliminada correctamente.")

def limpiar_venta():
    cliente_id_ventas.delete(0, tk.END)
    fecha_ventas.delete(0, tk.END)
    total_ventas.delete(0, tk.END)
    cargar_ventas()
    messagebox.showinfo("Limpiar", "Campos de venta limpiados.")


btn_save_venta = tk.Button(button_ventas, text="Guardar", font=("Arial", 12), bg="#4CAF50", fg="white", width=10)
btn_save_venta.pack(side=tk.LEFT, padx=5)

btn_update_venta = tk.Button(button_ventas, text="Actualizar", font=("Arial", 12), bg="#2196F3", fg="white", width=10)
btn_update_venta.pack(side=tk.LEFT, padx=5)

btn_delete_venta = tk.Button(button_ventas, text="Eliminar", font=("Arial", 12), bg="#f44336", fg="white", width=10)
btn_delete_venta.pack(side=tk.LEFT, padx=5)

btn_clear_venta= tk.Button(button_ventas, text="Limpiar", font=("Arial", 12), bg="#FF9800", fg="white", width=10)
btn_clear_venta.pack(side=tk.LEFT, padx=5)


btn_save_venta.config(command=guardar_venta)
btn_update_venta.config(command=actualizar_venta)
btn_delete_venta.config(command=eliminar_venta)
btn_clear_venta.config(command=limpiar_venta)

# PESTAÑA DETALLE PEDIDO
# Filtro de búsqueda por venta_id
frame_filtro_detalle = tk.Frame(tab_detalle_ventas)
frame_filtro_detalle.pack(padx=50, pady=(0,10), anchor="w")
tk.Label(frame_filtro_detalle, text="Buscar por venta_id:", font=("Arial", 12)).pack(side=tk.LEFT)
filtro_venta_id_detalle = tk.Entry(frame_filtro_detalle, width=20, font=("Arial", 12))
filtro_venta_id_detalle.pack(side=tk.LEFT, padx=5)

def filtrar_detalle():
    venta_id = filtro_venta_id_detalle.get()
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    if venta_id:
        cur.execute("SELECT * FROM DetalleVentas WHERE venta_id LIKE %s", (f"%{venta_id}%",))
    else:
        cur.execute("SELECT * FROM DetalleVentas")
    rows = cur.fetchall()
    conn.close()
    tree_detalle.delete(*tree_detalle.get_children())
    for row in rows:
        tree_detalle.insert('', 'end', values=row)

btn_filtrar_detalle = tk.Button(frame_filtro_detalle, text="Filtrar", command=filtrar_detalle)
btn_filtrar_detalle.pack(side=tk.LEFT, padx=5)
titulo_detalle = tk.Label(tab_detalle_ventas, text="Gestión de Detalle Ventas", font=("Arial", 16, "bold"), fg="orange")
titulo_detalle.pack(pady=20)

form_detalle = tk.Frame(tab_detalle_ventas)
form_detalle.pack(pady=20, anchor="w", padx=50)

# Treeview para mostrar registros de detalle ventas
# Treeview para mostrar registros de detalle ventas
tree_detalle = ttk.Treeview(tab_detalle_ventas)
tree_detalle.pack(fill="x", padx=50, pady=10)
tree_detalle['columns'] = ('detalle_id', 'venta_id', 'producto_id', 'cantidad', 'precio_unitario')
tree_detalle['show'] = 'headings'
for col in tree_detalle['columns']:
    tree_detalle.heading(col, text=col)
    tree_detalle.column(col, width=120)

def copiar_a_formulario_detalle(event):
    seleccionado = tree_detalle.focus()
    if seleccionado:
        valores = tree_detalle.item(seleccionado, 'values')
        venta_id_detalle.delete(0, tk.END)
        producto_id_detalle.delete(0, tk.END)
        cantidad_detalle.delete(0, tk.END)
        precio_unitario_detalle.delete(0, tk.END)
        venta_id_detalle.insert(0, valores[1])
        producto_id_detalle.insert(0, valores[2])
        cantidad_detalle.insert(0, valores[3])
        precio_unitario_detalle.insert(0, valores[4])

tree_detalle.bind('<<TreeviewSelect>>', copiar_a_formulario_detalle)

def cargar_detalle():
    conn = mysql.connector.connect(host=db.host, user=db.user, password=db.password, database=db.database)
    cur = conn.cursor()
    cur.execute("SELECT * FROM DetalleVentas")
    rows = cur.fetchall()
    conn.close()
    tree_detalle.delete(*tree_detalle.get_children())
    for row in rows:
        tree_detalle.insert('', 'end', values=row)

cargar_detalle()

# Dato 1 : Venta ID
tk.Label(form_detalle, text="Venta ID:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=10)
venta_id_detalle = tk.Entry(form_detalle, width=25, font=("Arial", 12), relief="solid", bd=1)
venta_id_detalle.grid(row=1, column=1, sticky="w", pady=10)

# Dato 2: Producto ID
tk.Label(form_detalle, text="Producto ID:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=10)
producto_id_detalle = tk.Entry(form_detalle, width=25, font=("Arial", 12), relief="solid", bd=1)
producto_id_detalle.grid(row=2, column=1, sticky="w", pady=10)

# Dato 3: Cantidad
tk.Label(form_detalle, text="Cantidad:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", padx=(0, 10), pady=10)
cantidad_detalle = tk.Entry(form_detalle, width=25, font=("Arial", 12), relief="solid", bd=1)
cantidad_detalle.grid(row=3, column=1, sticky="w", pady=10)

# Dato 4: Precio Unitario
tk.Label(form_detalle, text="Precio Unitario:", font=("Arial", 12)).grid(row=4, column=0, sticky="w", padx=(0, 10), pady=10)
precio_unitario_detalle = tk.Entry(form_detalle, width=25, font=("Arial", 12), relief="solid", bd=1)
precio_unitario_detalle.grid(row=4, column=1, sticky="w", pady=10)

# Botones de acción
button_detalle = tk.Frame(tab_detalle_ventas)
button_detalle.pack(pady=20)
def guardar_detalle():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO DetalleVentas (venta_id, producto_id, cantidad, precio_unitario) VALUES (%s, %s, %s, %s)",
                (venta_id_detalle.get(), producto_id_detalle.get(), cantidad_detalle.get(), precio_unitario_detalle.get()))
    conn.commit()
    conn.close()
    venta_id_detalle.delete(0, tk.END)
    producto_id_detalle.delete(0, tk.END)
    cantidad_detalle.delete(0, tk.END)
    precio_unitario_detalle.delete(0, tk.END)
    cargar_detalle()
    messagebox.showinfo("Guardado", "Detalle de venta guardado correctamente.")

def actualizar_detalle():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("UPDATE DetalleVentas SET producto_id=%s, cantidad=%s, precio_unitario=%s WHERE detalle_id=%s",
                (producto_id_detalle.get(), cantidad_detalle.get(), precio_unitario_detalle.get(), venta_id_detalle.get()))
    conn.commit()
    conn.close()
    cargar_detalle()
    messagebox.showinfo("Actualizado", "Detalle de venta actualizado correctamente.")

def eliminar_detalle():
    conn = mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.database
    )
    cur = conn.cursor()
    cur.execute("DELETE FROM DetalleVentas WHERE detalle_id=%s", (venta_id_detalle.get(),))
    conn.commit()
    conn.close()
    venta_id_detalle.delete(0, tk.END)
    producto_id_detalle.delete(0, tk.END)
    cantidad_detalle.delete(0, tk.END)
    precio_unitario_detalle.delete(0, tk.END)
    cargar_detalle()
    messagebox.showinfo("Eliminado", "Detalle de venta eliminado correctamente.")

def limpiar_detalle():
    venta_id_detalle.delete(0, tk.END)
    producto_id_detalle.delete(0, tk.END)
    cantidad_detalle.delete(0, tk.END)
    precio_unitario_detalle.delete(0, tk.END)
    cargar_detalle()
    messagebox.showinfo("Limpiar", "Campos de detalle de venta limpiados.")


btn_save_detalle = tk.Button(button_detalle, text="Guardar", font=("Arial", 12), bg="#4CAF50", fg="white", width=10)
btn_save_detalle.pack(side=tk.LEFT, padx=5)

btn_update_detalle = tk.Button(button_detalle, text="Actualizar", font=("Arial", 12), bg="#2196F3", fg="white", width=10)
btn_update_detalle.pack(side=tk.LEFT, padx=5)

btn_delete_detalle = tk.Button(button_detalle, text="Eliminar", font=("Arial", 12), bg="#f44336", fg="white", width=10)
btn_delete_detalle.pack(side=tk.LEFT, padx=5)

btn_clear_detalle = tk.Button(button_detalle, text="Limpiar", font=("Arial", 12), bg="#FF9800", fg="white", width=10)
btn_clear_detalle.pack(side=tk.LEFT, padx=5)

btn_save_detalle.config(command=guardar_detalle)
btn_update_detalle.config(command=actualizar_detalle)
btn_delete_detalle.config(command=eliminar_detalle)
btn_clear_detalle.config(command=limpiar_detalle)


root.mainloop()
