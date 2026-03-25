def get_unified_orders(
    start_date, end_date,
    guia=None, cliente=None, transportadora=None, pedido=None,
    vendedor=None, estado=None, limit=None, offset=None, count_only=False
):
    # Debug output
    import sys
    debug_msg = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║ GET_UNIFIED_ORDERS INICIADO                                              ║
╚════════════════════════════════════════════════════════════════════════════╝
Parámetros recibidos:
  - start_date: {start_date}
  - end_date: {end_date}
  - guia: {guia}
  - cliente: {cliente}
  - transportadora: {transportadora}
  - pedido: {pedido}
  - vendedor: {vendedor}
  - estado: {estado}
  - limit: {limit}
  - offset: {offset}
  - count_only: {count_only}
"""
    sys.stdout.write(debug_msg)
    sys.stdout.flush()
    
    # Si las fechas son None, usar valores por defecto (últimos 90 días)
    from datetime import datetime, timedelta
    if start_date is None or end_date is None:
        today = datetime.today()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
    
    # Construcción de filtros textuales (se mantienen como los usas hoy)
    where_clauses = [
        f"CONVERT(date, t430.f430_fecha_ts_creacion) BETWEEN '{start_date}' AND '{end_date}'",
        "t430.f430_id_tipo_docto IN ('PVN', 'PNF', 'PVI', 'PVL')"  # + PVL
    ]
    # El filtro de guía se aplicará en la consulta principal, no en el CTE
    # El filtro de cliente se aplicará en la consulta principal, no en el CTE
    if transportadora:
        where_clauses.append(f"UPPER(G.Transportador) LIKE '%{transportadora.upper()}%'")
    if pedido:
        pedido_parts = pedido.split('-')
        if len(pedido_parts) > 1:
            tipo_docto = pedido_parts[0]
            num_docto = pedido_parts[1]
            where_clauses.append(
                f"(t430.f430_id_tipo_docto = '{tipo_docto}' "
                f"AND CAST(t430.f430_consec_docto AS NVARCHAR) LIKE '%{num_docto}%')"
            )
        else:
            where_clauses.append(f"CAST(t430.f430_consec_docto AS NVARCHAR) LIKE '%{pedido}%'")
    if vendedor:
        where_clauses.append(f"vend.f200_razon_social LIKE '%{vendedor}%'")

    # Condición de estado (igual que hoy)
    estado_condition = ""
    if estado:
        estado_lower = estado.lower()
        estado_map = {
            'en elaboración': 0,
            'retenido': 1,
            'aprobado': 2,
            'comprometido': 3,
            'cumplido': 4,
            'anulado': 9
        }
        if estado_lower in estado_map:
            estado_condition = f"AND fo.f430_ind_estado = {estado_map[estado_lower]}"
        elif estado_lower == 'pendiente':
            estado_condition = "AND (fo.f430_ind_estado <> 9 AND fo.f430_ind_estado <> 4)"
        elif estado_lower == 'no anulado':
            estado_condition = "AND fo.f430_ind_estado <> 9"

    where_clause = " AND ".join(where_clauses)

    # CTEs y SELECT con la misma granularidad que SSMS
    base_cte = f"""
    WITH filtered_orders AS (
        SELECT 
            t430.f430_id_tipo_docto,
            t430.f430_consec_docto,
            t430.f430_fecha_ts_creacion,
            t430.f430_fecha_ts_aprobacion,
            t430.f430_fecha_ts_aprob_cart_desp,
            t430.f430_fecha_ts_aprob_cartera,
            t430.f430_fecha_ts_aprob_cupo_desp,
            t430.f430_fecha_ts_aprob_margen,
            t430.f430_fecha_ts_aprobacion_cart,
            t430.f430_ind_estado,
            t430.f430_rowid_tercero_fact,
            t430.f430_rowid_tercero_vendedor
        FROM [UNOEE].[dbo].[t430_cm_pv_docto] t430
        LEFT JOIN unoee.dbo.t200_mm_terceros vend ON t430.f430_rowid_tercero_vendedor=vend.f200_rowid
    WHERE {where_clause}
    ),
    cedi_clean AS (
        SELECT 
            CAST(LTRIM(RTRIM([codigo_pedido])) AS VARCHAR(50)) AS pedido_clean,
            [NoPicking],
            [Remesa],
            [Fecha_Despacho],
            [Fecha_Entrega],
            [status],
            [direccion],
            [Ciudad_Despacho]
        FROM [DWH_NEWSTETIC].[Logistica].[despachos_cedi]
        WHERE [Empresa] IN ('NEWSTETIC','NEW STETIC')
          AND [codigo_pedido] IS NOT NULL 
          AND LTRIM(RTRIM([codigo_pedido])) <> ''
    ),
    grouped_data AS (
        SELECT 
            fo.f430_id_tipo_docto AS [Tipo de documento],
            RTRIM(fo.f430_id_tipo_docto) + '-' + CONVERT(varchar(50), fo.f430_consec_docto) AS [Numero de pedido],

            CASE 
                WHEN convert(varchar(100), cedi.Remesa) IS NULL THEN ISNULL(UPPER(G.Num_Guia), '')
                ELSE CONVERT(varchar(100), cedi.Remesa)
            END AS [Guia],
            ISNULL(UPPER(G.Transportador), '') AS [Transportador],

            fo.f430_fecha_ts_creacion AS [Fecha Registro de pedido],
            fo.f430_fecha_ts_aprobacion AS [Fecha Preparacion de pedido],
            fo.f430_fecha_ts_aprob_cartera AS [Fecha aprobacion Cartera],
            
            cedi.[Fecha_Despacho] AS [Fecha de despacho de Pedido],
            cedi.[Fecha_Entrega] AS [Fecha de entrega de Pedido],
            cedi.status AS [Estado transportadora],
            cedi.direccion AS Direccion_Despacho,
            ISNULL(cedi.[Fecha_Despacho], '') AS "Fecha picking",

            CASE 
                WHEN fo.f430_ind_estado = 0 THEN 'En elaboración'
                WHEN fo.f430_ind_estado = 1 THEN 'Retenido'
                WHEN fo.f430_ind_estado = 2 THEN 'Aprobado'
                WHEN fo.f430_ind_estado = 3 THEN 'Comprometido'
                WHEN fo.f430_ind_estado = 4 THEN 'Cumplido'
                WHEN fo.f430_ind_estado = 9 THEN 'Anulado'
                ELSE 'Pendiente'
            END AS [Estado del documento],

            terc.f200_razon_social AS [Razon social cliente],
            vend.f200_razon_social AS [Razon social vendedor],
            ISNULL(G.Factura, '') AS [Numero de factura],

            CASE 
                WHEN UPPER(ISNULL(G.Transportador, ''))='CONALCA' THEN 'CONALCA'
                WHEN UPPER(ISNULL(G.Transportador, ''))='CONALCA BOGOTA' THEN 'Urbano Bogota'
                WHEN UPPER(ISNULL(G.Transportador, ''))='IMD & CIA SAS' THEN 'Urbano Medellin'
                WHEN UPPER(ISNULL(G.Transportador, ''))='IMD Y CIA SAS' THEN 'Urbano Medellin'
                WHEN UPPER(ISNULL(G.Transportador, ''))='MEDELLIN GUSTAVO' THEN 'Urbano Medellin'
                WHEN UPPER(ISNULL(G.Transportador, ''))='S&S ADMINISTRATION' THEN 'S&S ADMINISTRATION'
                WHEN UPPER(ISNULL(G.Transportador, ''))='TACMO SAS' THEN 'Nacional Guarne-Bogota'
                WHEN UPPER(ISNULL(G.Transportador, ''))='TCC' THEN 'Paqueteria excepto Bogota-Medellin'
                WHEN UPPER(ISNULL(G.Transportador, ''))='TRANSPORTADORA' THEN 'TRANSPORTADORA'
                ELSE ''
            END AS [RUTA],

            cedi.Ciudad_Despacho AS [Ciudad_Despacho],

            CASE 
                WHEN fo.f430_ind_estado = 0 THEN 1
                WHEN fo.f430_ind_estado = 2 THEN 2
                WHEN fo.f430_ind_estado = 3 THEN 3
                WHEN fo.f430_ind_estado = 1 THEN 4
                WHEN fo.f430_ind_estado = 4 THEN 5
                WHEN fo.f430_ind_estado = 9 THEN 6
                ELSE 7
            END AS OrdenEstado,

            ISNULL(f.IdMovimiento, 0) AS [numero_de_picking]

        FROM filtered_orders fo
        LEFT JOIN unoee.dbo.t200_mm_terceros terc ON fo.f430_rowid_tercero_fact=terc.f200_rowid
        LEFT JOIN unoee.dbo.t200_mm_terceros vend ON fo.f430_rowid_tercero_vendedor=vend.f200_rowid
        LEFT JOIN SGV_BKGENERICABASE1.dbo.T_encabezado_Prepack f ON fo.f430_consec_docto = CAST(f.consmov AS VARCHAR(50))
        LEFT JOIN SGV_BKGENERICABASE1.dbo.t_Guias_Generadas G ON f.IdMovimiento = G.PrepackingID
        LEFT JOIN cedi_clean cedi
                ON CAST(cedi.pedido_clean AS VARCHAR(50)) = CAST(fo.f430_consec_docto AS VARCHAR(50))

        WHERE 1=1
        {f"AND terc.f200_razon_social LIKE '%{cliente}%'" if cliente else ""}
        {f"AND vend.f200_razon_social LIKE '%{vendedor}%'" if vendedor else ""}
        {estado_condition}
    )
    """

    if count_only:
        # Contar filas del resultado (como lo ves en SSMS)
        query = base_cte + """
        SELECT COUNT(*) AS total_count
        FROM grouped_data;
        """
        
        # DEBUG: Log del query de conteo
        import sys
        debug_info = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║ QUERY COUNT CONSTRUIDO                                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
Parámetros:
  start_date: {start_date}, end_date: {end_date}
  guia: {guia}, cliente: {cliente}, transportadora: {transportadora}
  pedido: {pedido}, vendedor: {vendedor}, estado: {estado}

Primeros 1000 caracteres del query:
{query[:1000]}
...
════════════════════════════════════════════════════════════════════════════
"""
        sys.stdout.write(debug_info)
        sys.stdout.flush()
        
        return query

    # Traer filas (como SSMS) + paginación si aplica
    query = base_cte + """
    SELECT *
    FROM grouped_data
    ORDER BY OrdenEstado, [Fecha Registro de pedido] DESC
    """
    if limit is not None and offset is not None:
        query += f"\nOFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"

    # DEBUG: Log del query completo
    import sys
    debug_info = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║ QUERY SELECT CONSTRUIDO                                                  ║
╚════════════════════════════════════════════════════════════════════════════╝
Parámetros:
  start_date: {start_date}, end_date: {end_date}
  guia: {guia}, cliente: {cliente}, transportadora: {transportadora}
  pedido: {pedido}, vendedor: {vendedor}, estado: {estado}
  limit: {limit}, offset: {offset}

Primeros 1500 caracteres del query:
{query[:1500]}
...
════════════════════════════════════════════════════════════════════════════
"""
    sys.stdout.write(debug_info)
    sys.stdout.flush()

    return query
