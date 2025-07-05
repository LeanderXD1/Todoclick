import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps

# Configuración de la aplicación Flask
app = Flask(__name__)

# Imprimir la ruta de la instancia de Flask para diagnóstico
print(f"Flask instance path: {app.instance_path}") 

app.config['SECRET_KEY'] = 'your_super_secret_key_that_you_must_change_for_production' # ¡CAMBIA ESTO POR UNA CLAVE SECRETA SEGURA Y ÚNICA!

# Configuración de la base de datos (usando app.instance_path)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'dulces.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Carpeta para subir imágenes de dulces
# Asegúrate de que esta carpeta exista: your_project_folder/static/uploads
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inicializar la base de datos
db = SQLAlchemy(app)

# --- Modelos de la Base de Datos ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='vendedor') # 'admin' o 'vendedor'
    dulces_uploaded = db.relationship('Dulce', backref='uploader', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Dulce(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True) # Para el nombre del archivo de imagen
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Quién subió el dulce

    def __repr__(self):
        return f'<Dulce {self.name}>'

# --- Funciones Auxiliares ---

# Verificar la extensión de archivo permitida
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Context processor para hacer user y user_role disponibles en todas las plantillas
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
        g.user_role = None
    else:
        user = User.query.get(user_id)
        g.user = user
        g.user_role = user.role if user else None

# Decorador para requerir autenticación
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Debes iniciar sesión para acceder a esta página.', 'danger')
            return redirect(url_for('admin_login'))
        return view(**kwargs)
    return wrapped_view

# Decorador para requerir rol de administrador
def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not (g.user and g.user_role == 'admin'):
            flash('No tienes permisos para acceder a esta sección.', 'danger')
            return redirect(url_for('admin_login'))
        return view(**kwargs)
    return wrapped_view

# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/productos')
def productos():
    dulces = Dulce.query.all()
    return render_template('productos.html', dulces=dulces)

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

# --- Rutas de Administración ---

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if g.user: # Si ya está logueado, redirigir al panel
        return redirect(url_for('admin_panel'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('admin.html')

@app.route('/admin_panel')
@login_required
def admin_panel():
    dulces = Dulce.query.all()
    return render_template('admin_panel.html', dulces=dulces, username=g.user.username, user_role=g.user_role)

@app.route('/add_dulce', methods=['POST'])
@admin_required # Solo administradores pueden añadir
def add_dulce():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image_file = request.files.get('image')

        # Manejo de la imagen
        image_filename = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            # Asegurarse de que la carpeta UPLOAD_FOLDER exista antes de guardar
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename
        elif image_file and not allowed_file(image_file.filename):
            flash('Tipo de archivo de imagen no permitido. Solo se aceptan PNG, JPG, JPEG, GIF.', 'danger')
            return redirect(url_for('admin_panel'))


        new_dulce = Dulce(name=name, description=description, price=float(price), 
                          image_filename=image_filename, user_id=g.user.id)
        db.session.add(new_dulce)
        db.session.commit()
        flash('Dulce añadido exitosamente!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/edit_dulce/<int:dulce_id>', methods=['GET', 'POST'])
@admin_required # Solo administradores pueden editar
def edit_dulce(dulce_id):
    dulce_to_edit = Dulce.query.get_or_404(dulce_id)
    if request.method == 'POST':
        dulce_to_edit.name = request.form['name']
        dulce_to_edit.description = request.form['description']
        dulce_to_edit.price = float(request.form['price'])
        
        image_file = request.files.get('image')
        if image_file and image_file.filename != '': # Si se sube un nuevo archivo de imagen
            if allowed_file(image_file.filename):
                # Eliminar la imagen antigua si existe
                if dulce_to_edit.image_filename:
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], dulce_to_edit.image_filename)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                filename = secure_filename(image_file.filename)
                # Asegurarse de que la carpeta UPLOAD_FOLDER exista antes de guardar
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                dulce_to_edit.image_filename = filename
            else:
                flash('Tipo de archivo de imagen no permitido. Solo se aceptan PNG, JPG, JPEG, GIF.', 'danger')
                return redirect(url_for('edit_dulce', dulce_id=dulce_id))
        elif 'remove_image' in request.form: # Opción para eliminar la imagen
            if dulce_to_edit.image_filename:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], dulce_to_edit.image_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
                dulce_to_edit.image_filename = None # Establecer a None en la DB
        # Si no se subió una nueva imagen y no se marcó para eliminar, se mantiene la existente
        

        db.session.commit()
        flash('Dulce actualizado exitosamente!', 'success')
        return redirect(url_for('admin_panel'))
    
    # Si es GET, mostrar el formulario de edición
    dulces = Dulce.query.all() # Para mostrar la tabla completa
    return render_template('admin_panel.html', edit_dulce=dulce_to_edit, dulces=dulces, 
                           username=g.user.username, user_role=g.user_role)

@app.route('/delete_dulce/<int:dulce_id>', methods=['POST'])
@admin_required # Solo administradores pueden eliminar
def delete_dulce(dulce_id):
    dulce_to_delete = Dulce.query.get_or_404(dulce_id)
    
    # Eliminar el archivo de imagen asociado si existe
    if dulce_to_delete.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], dulce_to_delete.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(dulce_to_delete)
    db.session.commit()
    flash('Dulce eliminado exitosamente.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('admin_login'))


# --- Inicialización de la Aplicación ---
if __name__ == '__main__':
    # Crear la carpeta de uploads si no existe
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    with app.app_context():
        # Antes de db.create_all(), asegúrate de que app.instance_path exista
        # Flask lo crea automáticamente, pero una verificación adicional no está de más
        if not os.path.exists(app.instance_path): # ¡CORREGIDO AQUÍ! Ya no es os.os.path
            os.makedirs(app.instance_path)

        db.create_all() # Crea las tablas si no existen

        # Crea un usuario administrador si no existe
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('Keilerjose27LeanderGonzalez') # ¡Contraseña de admin solicitada!
            db.session.add(admin_user)
            db.session.commit()
            print(f"Usuario 'admin' creado con contraseña: Keilerjose27LeanderGonzalez")

        # Crea un usuario vendedor1 si no existe
        if not User.query.filter_by(username='vendedor1').first():
            vendedor1_user = User(username='vendedor1', role='vendedor')
            vendedor1_user.set_password('ClaveVendedor1anotarYGuardar12231') # ¡Contraseña de vendedor1 solicitada!
            db.session.add(vendedor1_user)
            db.session.commit()
            print(f"Usuario 'vendedor1' creado con contraseña: ClaveVendedor1anotarYGuardar12231")
            
