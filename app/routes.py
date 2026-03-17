import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.auth import authenticate_user 
from app.Conexion_Sql import DatabaseConnection
from app.notification_db import NotificationDB
from app.models import OrderInfo
from app.queries_unified import get_unified_orders
from app.queries_unified_vendedores import get_unified_orders_vendedores
from functools import lru_cache
import time
import requests
from datetime import datetime
import uuid
import pytz
import unicodedata

# CACHE_TIMEOUT = 5000  # 10 minutos en segundos

# cache = {}


main = Blueprint('main', __name__)

# def order_in_date_range(order, start_date_obj, end_date_obj):
#     fecha_registro_pedido = order.get('fecha_registro_pedido', '')
#     if isinstance(fecha_registro_pedido, datetime):
#         order_date = fecha_registro_pedido
#     elif fecha_registro_pedido:
#         for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y%m%d', '%Y%m'):
#             try:
#                 order_date = datetime.strptime(fecha_registro_pedido, fmt)
#                 break
#             except Exception:
#                 continue
#         else:
#             return False
#     else:
#         return False
#     # Compara solo la fecha, ignora la hora
#     return start_date_obj.date() <= order_date.date() <= end_date_obj.date()



# def get_cache_key(start_date, end_date, guia=None, cliente=None, transportadora=None, pedido=None, vendedor=None, is_vendedor=False, factura=None, referencia=None):
#     """
#     Genera una clave de caché considerando fechas exactas (YYYY-MM-DD) o por mes (YYYYMM).
#     """
#     if is_vendedor and vendedor:
#         return f"vendedor_{vendedor}_{cliente or ''}_{pedido or ''}_{factura or ''}_{referencia or ''}"

#     if start_date is None or end_date is None:
#         if vendedor:
#             return f"vendedor_{vendedor}_{cliente or ''}_{pedido or ''}_{factura or ''}_{referencia or ''}"
#         filters = '_'.join([f for f in [guia or '', cliente or '', transportadora or '', pedido or '', factura or '', referencia or ''] if f])
#         return f"no_date_{filters}" if filters else "no_date"

#     def parse_date(date_str):
#         for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y%m%d', '%Y%m'):
#             try:
#                 return datetime.strptime(date_str, fmt)
#             except ValueError:
#                 continue
#         return None

#     start_date_obj = parse_date(start_date)
#     end_date_obj = parse_date(end_date)

#     if not start_date_obj or not end_date_obj:
#         return f"{start_date}_{end_date}_{'_'.join([guia or '', cliente or '', transportadora or '', pedido or '', vendedor or '', factura or '', referencia or ''])}" if any([guia, cliente, transportadora, pedido, vendedor, factura, referencia]) else f"{start_date}_{end_date}"

#     exact_key = f"{start_date}_{end_date}"
#     if exact_key in cache and not any([guia, cliente, transportadora, pedido, vendedor, factura, referencia]):
#         return exact_key

#     if any([guia, cliente, transportadora, pedido, vendedor, factura, referencia]) and exact_key in cache:
#         return exact_key

#     for cached_key in cache:
#         cached_parts = cached_key.split('_')
#         if len(cached_parts) < 2:
#             continue
#         cached_start, cached_end = cached_parts[0], cached_parts[1]
#         cached_start_obj = parse_date(cached_start)
#         cached_end_obj = parse_date(cached_end)
#         if not cached_start_obj or not cached_end_obj:
#             continue
#         if cached_start_obj <= start_date_obj and cached_end_obj >= end_date_obj:
#             return cached_key

#     if any([guia, cliente, transportadora, pedido, vendedor, factura, referencia]):
#         filters = [guia or '', cliente or '', transportadora or '', pedido or '', vendedor or '', factura or '', referencia or '']
#         return f"{start_date}_{end_date}_{'_'.join(filters)}"
#     else:
#         return f"{start_date}_{end_date}"

def fetch_combined_data(start_date=None, end_date=None, guia=None, cliente=None, transportadora=None, pedido=None, vendedor=None, estado=None, is_vendedor=False, limit=10, offset=0, factura=None):
    try:
        # cache_key = get_cache_key(start_date, end_date, guia, cliente, transportadora, pedido, vendedor, is_vendedor, factura, referencia)
        
        # if cache_key in cache:
        #     cached_data, timestamp = cache[cache_key]
        #     if time.time() - timestamp < CACHE_TIMEOUT:
        #         # Para vista de vendedores, usar datos sin filtrar
        #         if is_vendedor:
        #             filtered_data = cached_data
                    
        #             # Apply filters
        #             if cliente:
        #                 filtered_data = [order for order in filtered_data
        #                                  if str(order.get('cliente', '')).lower().find(str(cliente).lower()) != -1]
        #             if pedido:
        #                 filtered_data = [order for order in filtered_data
        #                                  if str(order.get('numero_pedido', '')).lower().find(str(pedido).lower()) != -1]
        #             if factura:
        #                 filtered_data = [order for order in filtered_data
        #                                  if str(order.get('numero_factura', '')).lower().find(str(factura).lower()) != -1]
        #             if referencia:
        #                 filtered_data = [order for order in filtered_data
        #                                  if str(order.get('referencia', '')).lower().find(str(referencia).lower()) != -1]
                    
        #             total_count = len(filtered_data)
        #             paginated_data = filtered_data[offset:offset + limit]
        #             return paginated_data, total_count

        #         filtered_data = cached_data
                
        #         # Filtrar por rango de fechas solicitado si es necesario
        #         if start_date and end_date:
        #             # Soporta fechas con día y hora
        #             for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y%m%d', '%Y%m'):
        #                 try:
        #                     start_date_obj = datetime.strptime(start_date, fmt)
        #                     break
        #                 except Exception:
        #                     continue
        #             else:
        #                 start_date_obj = None

        #             for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y%m%d', '%Y%m'):
        #                 try:
        #                     end_date_obj = datetime.strptime(end_date, fmt)
        #                     break
        #                 except Exception:
        #                     continue
        #             else:
        #                 end_date_obj = None

        #             if start_date_obj and end_date_obj:
        #                 filtered_data = [
        #                     order for order in filtered_data
        #                     if order_in_date_range(order, start_date_obj, end_date_obj)
        #                 ]

        #         # Aplicar los demás filtros si existen
        #         if guia:
        #             filtered_data = [order for order in filtered_data 
        #                             if str(order.get('guia', '')).lower().find(str(guia).lower()) != -1]
        #         if cliente:
        #             filtered_data = [order for order in filtered_data 
        #                             if str(order.get('cliente', '')).lower().find(str(cliente).lower()) != -1]
        #         if transportadora:
        #             filtered_data = [order for order in filtered_data 
        #                             if str(order.get('transportadora', '')).lower().find(str(transportadora).lower()) != -1]
        #         if pedido:
        #             filtered_data = [order for order in filtered_data 
        #                             if str(order.get('numero_pedido', '')).lower().find(str(pedido).lower()) != -1]
        #         if vendedor:
        #             filtered_data = [order for order in filtered_data 
        #                             if str(order.get('razon_social_vendedor', '')).lower().find(str(vendedor).lower()) != -1]
                
        #         # Aplicar paginación
        #         total_count = len(filtered_data)
        #         paginated_data = filtered_data[offset:offset + limit]
        #         return paginated_data, total_count

        # Si no hay datos en caché o queremos recargarlos, consultamos la base de datos
        if is_vendedor:
            db_connection = DatabaseConnection('SGV_BKGENERICABASE1')
            
            # Obtener conteo primero
            count_query = get_unified_orders_vendedores(vendedor, cliente, pedido, factura, estado, count_only=True)
            count_result = db_connection.execute_query(count_query)
            total_count = count_result[0]['total_count'] if count_result else 0
            
            # Luego obtener datos paginados
            query = get_unified_orders_vendedores(vendedor, cliente, pedido, factura, estado, limit, offset)
            unified_data = db_connection.execute_query(query)
            
            # Transformar los datos al formato que espera la aplicación
            all_combined_data = []
            for item in unified_data:
                order_data = {
                    'Guia': item.get('Guia', 'Sin guía'),
                    'Transportador': item.get('Transportador', 'Sin transportador'),
                    'Razon social cliente': item.get('Razon social cliente', 'Desconocido'),
                    'Numero de pedido': item.get('Numero de pedido', ''),
                    'Numero de factura': item.get('Numero de factura', ''),
                    'LINEA': item.get('LINEA', ''),
                    'GRUPO': item.get('GRUPO', ''),
                    'SUBGRUPO': item.get('SUBGRUPO', ''),
                    'Cantidad': item.get('Cantidad', ''),
                    'Fecha_Despacho': item.get('Fecha_Despacho', 'Pendiente'),
                    'Fecha_Picking': item.get('Fecha picking', 'Pendiente'),
                    'Fecha de alistamiento': item.get('Fecha de alistamiento', 'Pendiente'),
                    'Fecha aprobacion Cartera': item.get('Fecha aprobacion Cartera', 'Pendiente'),
                    'Razon social vendedor': item.get('Razon social vendedor', 'Desconocido'),
                    'Fecha Preparacion de pedido': item.get('Fecha Preparacion de pedido', 'Pendiente'),
                    'Estado del documento': item.get('Estado del documento', ''),
                    'Fecha Registro de pedido': item.get('Fecha Registro de pedido', ''),
                    'Extencion del item': item.get('Extencion del item', ''),
                    'RUTA': item.get('RUTA', item.get('Transportador', '')),
                    'Keypedido': item.get('Keypedido', ''),
                    'Fecha de entrega de Pedido': item.get('Fecha de entrega de Pedido', ''),  # Nuevo campo
                    'Estado transportadora': item.get('Estado transportadora', ''),  # Nuevo campo
                    'Ciudad_Despacho': item.get('Ciudad_Despacho', ''),
                    'Direccion_Despacho': item.get('Direccion_Despacho', ''),
                    'numero_de_picking': item.get('numero_de_picking', '')
                    
                }
                
                order_info = OrderInfo.from_dict(order_data)
                all_combined_data.append(order_info.__dict__)
            
            return all_combined_data, total_count
        
        else:
            # Para el dashboard principal, usamos el nuevo query unificado
            db_connection = DatabaseConnection('SGV_BKGENERICABASE1')  # Usamos esta conexión porque la mayoría de las tablas están ahí
            
            # Obtener el conteo total primero
            count_query = get_unified_orders(start_date, end_date, guia, cliente, transportadora, pedido, vendedor, estado, None, None, count_only=True)
            count_result = db_connection.execute_query(count_query)
            total_count = count_result[0]['total_count'] if count_result else 0
            
            # Luego obtener datos paginados
            query = get_unified_orders(start_date, end_date, guia, cliente, transportadora, pedido, vendedor, estado, limit, offset)
            unified_data = db_connection.execute_query(query)
            
            # Transformar los datos al formato que espera la aplicación
            all_combined_data = []
            for item in unified_data:
                order_data = {
                    'Guia': item.get('Guia', 'Sin guía'),
                    'Transportador': item.get('Transportador', 'Sin transportador'),
                    'Razon social cliente': item.get('Razon social cliente', 'Desconocido'),
                    'Numero de pedido': item.get('Numero de pedido', ''),
                    'Numero de factura': item.get('Numero de factura', ''),
                    'LINEA': '',  # No está en el nuevo query
                    'GRUPO': '',  # No está en el nuevo query
                    'SUBGRUPO': '',  # No está en el nuevo query
                    'Cantidad': item.get('Cantidad', ''),
                    'Fecha_Despacho': item.get('Fecha_Despacho', 'Pendiente'),
                    'Fecha_Picking': item.get('Fecha picking', 'Pendiente'),
                    'Fecha de alistamiento': item.get('Fecha de alistamiento', 'Pendiente'),
                    'Fecha aprobacion Cartera': item.get('Fecha aprobacion Cartera', 'Pendiente'),
                    'Razon social vendedor': item.get('Razon social vendedor', 'Desconocido'),
                    'Fecha Preparacion de pedido': item.get('Fecha Preparacion de pedido', 'Pendiente'),
                    'Estado del documento': item.get('Estado del documento', ''),
                    'Fecha Registro de pedido': item.get('Fecha Registro de pedido', ''),
                    'Extencion del item': item.get('Extencion del item', ''),
                    'RUTA': item.get('RUTA', item.get('Transportador', '')),
                    'Keypedido': item.get('Keypedido', ''),
                    'Fecha de entrega de Pedido': item.get('Fecha de entrega de Pedido', ''),  # Nuevo campo
                    'Estado transportadora': item.get('Estado transportadora', ''),  # Nuevo campo
                    'Ciudad_Despacho': item.get('Ciudad_Despacho', ''),
                    'Direccion_Despacho': item.get('Direccion_Despacho', ''),
                    'numero_de_picking': item.get('numero_de_picking', '')
                }
                
                order_info = OrderInfo.from_dict(order_data)
                all_combined_data.append(order_info.__dict__)

            return all_combined_data, total_count

        # Guardar en caché
        # cache[cache_key] = (all_combined_data, time.time())

        # Obtener el conteo total para la tabla (para la paginación)
        if is_vendedor:
            # Para vendedores, ya tenemos todos los datos, así que calculamos el total
            total_count = len(all_combined_data)
            # Aplicar paginación manualmente ya que el query de vendedores no la incluye
            paginated_data = all_combined_data[offset:offset + limit]
            return paginated_data, total_count
        else:
            # Para el dashboard principal, ejecutamos un query separado para contar
            count_query = get_unified_orders(start_date, end_date, guia, cliente, transportadora, pedido, vendedor, estado, None, None, count_only=True)
            count_result = db_connection.execute_query(count_query)
            total_count = count_result[0]['total_count'] if count_result else len(all_combined_data)
            # DEVOLVER SOLO LOS DATOS DE LA PÁGINA ACTUAL, NO TODOS
            return all_combined_data, total_count

    except Exception as e:
        logging.error(f'Error al obtener datos combinados: {e}')
        return [], 0
    
@main.route('/')  # Agregar ruta raíz
def index():
    return redirect(url_for('main.login'))

@main.route('/acceso_denegado')
def acceso_denegado():
    return render_template('acceso_denegado.html'), 403

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Autenticación del usuario
        success, user_info, account_status, error_message = authenticate_user(username, password)
        
        if success:
            session['user_info'] = user_info  # Establecer la sesión del usuario con el diccionario de información

            # Lista de nombres permitidos
            allowed_names = [
                # CEDI
                'Yecid David Guzman Diaz',
                'Juan Carlos Escobar Sossa',
                'Alejandro Moreno Jimenez',
                'Samuel Felipe Tapias Vertel',
                'Cesar Augusto Arango Durango',
                'Wilson de Jesus Gallego Serna',
                'Carlos Mario Castro Lopez',
                'Jose Luis Echeverri Alzate',
                'Jhon James Osorio Lopez',
                'Diana Marcela Castañeda Gallego',
                'Sandra Maria Ceballos',
                'Mauricio Saldarriaga Marín',
                'Julio Cesar Gaviria',
                'Yeimer Martinez Montes',
                'Jorge Ivan Yepes Jaramillo',
                # Comerciales_Admin
                'Natalia Eugenia Atehortua Amaya',
                'Liliana Maria Rua Coronado',
                'Ana Maria Vargas Osorio',
                'Gina Tatiana Bastidas Estepa',
                'Sandra Patricia Ruiz Arbeláez',
                'Sandra Catalina Ortiz Castrillón',
                'Ingrid Johana Bulla',
                'Maria del Pilar Orozco Aldana',
                'Maria Yadira Tabares Rios',
                'Viviana Taborda Ospina'
            ]

            # Normalizar todos los nombres permitidos
            allowed_names_normalized = [normalize_user_name(n) for n in allowed_names]
            # Normalizar el nombre del usuario autenticado
            user_normalized = normalize_user_name(user_info['displayName'])

            if user_normalized in allowed_names_normalized:
                return redirect(url_for('main.dashboard'))
            elif user_info['department'] == 'Soluciones Dentales':
                return redirect(url_for('main.dashboard_vendedores'))
            else:
                return redirect(url_for('main.acceso_denegado'))
        else:
            # Manejar error de autenticación
            flash(error_message, 'danger')
            
            return redirect(url_for('main.login'))

    return render_template('login.html')

def normalize_name(name):
    parts = name.split()
    if len(parts) >= 2:
        # Asumimos que las últimas dos palabras son los apellidos
        last_two_parts = parts[-2:]
        return " ".join(last_two_parts).lower()
    return name.lower()

def normalize_user_name(name):
    # Quitar tildes y espacios, y pasar a minúsculas
    nfkd = unicodedata.normalize('NFKD', name)
    only_ascii = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return only_ascii.replace(" ", "").lower()

@main.route('/dashboard_vendedores')
def dashboard_vendedores():
    if 'user_info' not in session:
        flash('Debe iniciar sesión primero', 'warning')
        return redirect(url_for('main.login'))
    
    displayName = session['user_info']['displayName']
    normalized_displayName = normalize_name(displayName)

    # NO cargar datos iniciales, solo pasar el nombre normalizado
    return render_template('dashboard_Vendedores.html', 
                          displayName=displayName, 
                          normalized_displayName=normalized_displayName,
                          orders=[], # Lista vacía
                          total_count=0) # Contador en 0

@main.route('/dashboard')
def dashboard():
    if 'user_info' not in session:
        flash('Debe iniciar sesión primero', 'warning')
        return redirect(url_for('main.login'))
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    orders = fetch_combined_data(start_date=start_date, end_date=end_date)
    
    return render_template('dashboard.html', 
                         displayName=session['user_info']['displayName'],
                         orders=orders)

@main.route('/api/orders', methods=['GET'])
def get_orders():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    guia = request.args.get('guia')
    cliente = request.args.get('cliente')
    transportadora = request.args.get('transportadora')
    pedido = request.args.get('pedido')
    vendedor = request.args.get('vendedor')
    estado = request.args.get('estado')  # Agregar esta línea
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 51))
    offset = (page - 1) * limit

    if not start_date or not end_date:
        return jsonify({'error': 'Se requieren fechas de inicio y fin', 'success': False})

    try:
        orders, total_count = fetch_combined_data(
            start_date=start_date,
            end_date=end_date,
            guia=guia,
            cliente=cliente,
            transportadora=transportadora,
            pedido=pedido,
            vendedor=vendedor,
            estado=estado,  # Agregar esta línea
            limit=limit,
            offset=offset
        )

        return jsonify({
            'orders': orders,
            'total_count': total_count,
            'page': page,
            'success': True
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'success': False})

@main.route('/api/vendedor_orders', methods=['GET'])
def get_vendedor_orders():
    vendedor = request.args.get('vendedor')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit
    cliente = request.args.get('cliente', '')
    pedido = request.args.get('pedido', '')
    factura = request.args.get('factura', '')
    estado = request.args.get('estado', '')
    
    if not vendedor:
        return jsonify({'error': 'Vendedor no especificado'}), 400
    
    try:
        # Usar la función fetch_combined_data que ya tienes optimizada
        orders, total_count = fetch_combined_data(
            vendedor=vendedor,
            cliente=cliente,
            pedido=pedido,
            factura=factura,
            estado=estado,
            is_vendedor=True,
            limit=limit,
            offset=offset
        )
        
        # Calcular páginas totales
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        return jsonify({
            'orders': orders,
            'totalPages': total_pages,
            'currentPage': page,
            'totalItems': total_count,
            'total_count': total_count
        })
            
    except Exception as e:
        print(f"Error en vendedor_orders: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@main.route('/logout')
def logout():
    session.clear()  # Limpiar toda la sesión
    flash('Sesión cerrada correctamente' , 'info')
    return redirect(url_for('main.login'))

# Lista de notificaciones (en producción, esto debería estar en una base de datos)
# notifications_db = [
#     {
#         'id': '1',
#         'message': 'Bienvenido al nuevo sistema de seguimiento de pedidos',
#         'author': 'Sistema',
#         'timestamp': '2025-05-01T12:00:00',
#         'read_by': [],  # Lista de usuarios que han leído esta notificación
#         'for_user': None  # None significa para todos los usuarios
#     }
# ]

# Verificar si un usuario es administrador
def is_admin(username):
    # Lista de usuarios administradores que pueden publicar notificaciones
    admin_users = ['Practicante TIC', 'Alejandro Moreno Jimenez']
    return username in admin_users

@main.route('/api/notifications', methods=['GET'])
def get_notifications():
    if 'user_info' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    user_id = session['user_info']['displayName']
    
    # Verificar si el usuario es administrador
    if is_admin(user_id):
        # Obtener todas las notificaciones sin filtrar
        notifications = NotificationDB.get_all_notifications()
    else:
        # Filtrar notificaciones para este usuario (o para todos)
        notifications = NotificationDB.get_all_notifications()
        notifications = [
            n for n in notifications 
            if n['for_user'] is None or n['for_user'] == user_id
        ]
    
    return jsonify({'notifications': notifications})

@main.route('/api/notifications', methods=['POST'])
def create_notification():
    if 'user_info' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    user_id = session['user_info']['displayName']
    
    # Verificar si el usuario es administrador
    if not is_admin(user_id):
        return jsonify({'error': 'No tienes permisos para crear notificaciones'}), 403
    
    # Obtener datos de la solicitud
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'Mensaje requerido'}), 400
    
    # Crear nueva notificación en la base de datos
    new_notification = NotificationDB.create_notification(
        message=data['message'],
        author=user_id,
        for_user=data.get('for_user')
    )
    
    return jsonify({
        'success': True,
        'notification': new_notification
    }), 201

@main.route('/api/notifications/<notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    if 'user_info' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    user_id = session['user_info']['displayName']
    
    # Marcar notificación como leída en la base de datos
    readers_count = NotificationDB.mark_notification_read(notification_id, user_id)
    
    return jsonify({'success': True, 'readers_count': readers_count})

@main.route('/api/notifications/read-all', methods=['POST'])
def mark_all_read():
    if 'user_info' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    user_id = session['user_info']['displayName']
    
    # Marcar todas las notificaciones como leídas
    marked_count = NotificationDB.mark_all_read(user_id)
    
    return jsonify({'success': True, 'marked_count': marked_count})

@main.route('/admin/notifications')
def admin_notifications():
    if 'user_info' not in session:
        flash('Debe iniciar sesión primero', 'warning')
        return redirect(url_for('main.login'))
    
    user_id = session['user_info']['displayName']
    
    # Verificar si el usuario es administrador
    if not is_admin(user_id):
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('admin_notifications.html', displayName=user_id)

@main.route('/api/notifications/<notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    if 'user_info' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    user_id = session['user_info']['displayName']
    
    # Verificar si el usuario es administrador
    if not is_admin(user_id):
        return jsonify({'error': 'No tienes permisos para eliminar notificaciones'}), 403
    
    # Eliminar la notificación
    success = NotificationDB.delete_notification(notification_id)
    
    if not success:
        return jsonify({'error': 'Notificación no encontrada'}), 404
    
    return jsonify({'success': True})
