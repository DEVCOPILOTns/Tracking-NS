#EL MODELO EN DONDE ESPECIFICO LOS CAMPOS A LLAMAR DESDE LA BASE DE DATOS Y QUERY
from typing import Dict, Any

class OrderInfo:
    def __init__(self, guia: str, transportadora: str, cliente: str, 
                numero_pedido: str, numero_factura: str, linea: str, grupo: str, 
                subgrupo: str, cantidad: str,
                fecha_despacho: str = '', fecha_despacho_cedi: str = '',  # Diferenciar ambos campos
                fecha_picking: str = '', razon_social_vendedor: str = '', 
                fecha_preparacion: str = '', estado_documento: str = '',
                ruta: str = '', fecha_de_alistamiento: str = '', 
                fecha_aprobacion_cartera: str = '', fecha_entrega: str = '', 
                estado_transportadora: str = '', Ciudad_Despacho: str = '',
                Direccion_Despacho: str = '', numero_de_picking: str = ''):
        self.guia = guia
        self.transportadora = transportadora
        self.cliente = cliente
        self.numero_pedido = numero_pedido
        self.numero_factura = numero_factura
        self.linea = linea
        self.grupo = grupo
        self.subgrupo = subgrupo
        self.cantidad = cantidad
        self.fecha_despacho = fecha_despacho  # Campo general
        self.fecha_despacho_cedi = fecha_despacho_cedi  # Campo específico del CEDI
        self.fecha_picking = fecha_picking
        self.razon_social_vendedor = razon_social_vendedor
        self.fecha_preparacion = fecha_preparacion
        self.estado_documento = estado_documento
        self.ruta = ruta
        self.fecha_de_alistamiento = fecha_de_alistamiento
        self.fecha_aprobacion_cartera = fecha_aprobacion_cartera
        self.fecha_entrega = fecha_entrega
        self.estado_transportadora = estado_transportadora
        self.Ciudad_Despacho = Ciudad_Despacho
        self.Direccion_Despacho = Direccion_Despacho
        self.numero_de_picking = numero_de_picking

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'OrderInfo':
        info = OrderInfo(
            guia=data.get('Guia', ''),
            transportadora=data.get('Transportador', ''),
            cliente=data.get('Razon social cliente', ''),
            numero_pedido=data.get('Numero de pedido', ''),
            numero_factura=data.get('Numero de factura', ''),
            linea=data.get('LINEA', ''),
            grupo=data.get('GRUPO', ''),
            subgrupo=data.get('SUBGRUPO', ''),
            cantidad=data.get('Cantidad', ''),
            fecha_despacho=data.get('Fecha_Despacho', ''),  # Campo general
            fecha_despacho_cedi=data.get('Fecha de despacho de Pedido', ''),  # Campo específico del CEDI
            fecha_picking=data.get('Fecha_Picking', ''),
            razon_social_vendedor=data.get('Razon social vendedor', ''),
            fecha_preparacion=data.get('Fecha Preparacion de pedido', ''),
            estado_documento=data.get('Estado del documento', ''),
            ruta=data.get('RUTA', ''),
            fecha_de_alistamiento=data.get('Fecha de alistamiento', ''),
            fecha_aprobacion_cartera=data.get('Fecha aprobacion Cartera', ''),
            fecha_entrega=data.get('Fecha de entrega de Pedido', ''),
            estado_transportadora=data.get('Estado transportadora', ''),
            Ciudad_Despacho=data.get('Ciudad_Despacho', ''),
            Direccion_Despacho=data.get('Direccion_Despacho', ''),
            numero_de_picking=data.get('numero_de_picking', '')
        )
        info.fecha_registro_pedido = data.get('Fecha Registro de pedido', '')
        return info