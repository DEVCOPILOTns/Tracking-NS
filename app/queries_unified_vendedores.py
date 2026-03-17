def get_unified_orders_vendedores(
    vendedor, cliente=None, pedido=None, factura=None,
    estado=None, limit=None, offset=None, count_only=False
):
    """
    Consulta unificada para la vista de vendedores, agrupando por pedido,
    manteniendo el número de picking y SIN filtro por referencia.
    """
    from datetime import datetime, timedelta
    import unicodedata
    today = datetime.today()
    two_months_ago = today - timedelta(days=60)
    date_filter = two_months_ago.strftime('%Y-%m-%d')

    # Limpiar tildes del nombre de vendedor
    def limpiar_tildes(texto):
        if not texto:
            return texto
        # Solo elimina tildes, pero conserva la ñ
        reemplazos = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        }
        texto_limpio = texto
        for original, reemplazo in reemplazos.items():
            texto_limpio = texto_limpio.replace(original, reemplazo)
        return texto_limpio

    vendedor_limpio = limpiar_tildes(vendedor)
    print(f"Filtro vendedor recibido: {vendedor} | Limpiado: {vendedor_limpio}")

    estado_map = {
        'en elaboración': 0,
        'retenido': 1,
        'aprobado': 2,
        'comprometido': 3,
        'cumplido': 4,
        'anulado': 9
    }

    pedido_like = (
        f"AND CAST(t430.f430_consec_docto AS NVARCHAR) LIKE '%{pedido}%'"
        if pedido and '-' not in pedido else ""
    )
    pedido_parts = pedido.split('-') if pedido else None
    pedido_tipo_consec = (
        f"AND t430.f430_id_tipo_docto = '{pedido_parts[0]}' "
        f"AND CAST(t430.f430_consec_docto AS NVARCHAR) LIKE '%{pedido_parts[1]}%'"
        if pedido and '-' in pedido else ""
    )
    estado_filter = (
        f"AND t430.f430_ind_estado = {estado_map[estado.lower()]}"
        if estado and estado.lower() in estado_map else
        "AND (t430.f430_ind_estado <> 9 AND t430.f430_ind_estado <> 4)"
        if estado and estado.lower() == 'pendiente' else
        "AND t430.f430_ind_estado <> 9"
        if estado and estado.lower() == 'no anulado' else
        ""
    )

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
        WHERE t430.f430_fecha_ts_creacion >= '{date_filter}'
          AND t430.f430_id_tipo_docto IN ('PVN', 'PNF', 'PVI', 'PVL')
          AND vend.f200_razon_social LIKE '%{vendedor_limpio}%'
          {pedido_like}
          {pedido_tipo_consec}
          {estado_filter}
    ),
    cedi_clean AS (
        SELECT 
            CAST(LTRIM(RTRIM([Pedido])) AS BIGINT) AS pedido_clean,
            [NoPicking],
            [Remesa],
            [Fecha_Despacho],
            [Fecha_Entrega],
            [ESTADO],
            [Direccion_Despacho],
            [Ciudad_Despacho]
        FROM [DWH_NEWSTETIC].[dbo].[Despachos_CEDI]
        WHERE [Empresa] IN ('NEWSTETIC','NEW STETIC')
          AND [Pedido] IS NOT NULL 
          AND LTRIM(RTRIM([Pedido])) <> ''
          AND ISNUMERIC(LTRIM(RTRIM([Pedido]))) = 1
    ),
    grouped_data AS (
        SELECT DISTINCT
            fo.f430_id_tipo_docto AS "Tipo de documento",
            RTRIM(fo.f430_id_tipo_docto) + '-' + CONVERT(varchar(50), fo.f430_consec_docto) AS "Numero de pedido",

            --fo.f430_fecha_ts_creacion AS [Fecha Registro de pedido],
            --fo.f430_fecha_ts_aprobacion AS [Fecha Preparacion de pedido],
            --maxFechaAprob.FechaAprobada AS [Fecha aprobacion Cartera],
            --maxFechaAprob.FechaAprobada AS [Fecha de aprobado],
            --MAX(s.fechaRegistro) AS [Fecha de alistamiento],
            --fo.f430_fecha_ts_aprob_cupo_desp, 
            --fo.f430_fecha_ts_aprob_margen
 
                
            CASE
                WHEN fo.f430_ind_estado = 0 THEN 'En elaboración'
                WHEN fo.f430_ind_estado = 1 THEN 'Retenido'
                WHEN fo.f430_ind_estado = 2 THEN 'Aprobado'
                WHEN fo.f430_ind_estado = 3 THEN 'Comprometido'
                WHEN fo.f430_ind_estado = 4 THEN 'Cumplido'
                WHEN fo.f430_ind_estado = 9 THEN 'Anulado'
                WHEN fo.f430_ind_estado <> 9 AND fo.f430_ind_estado <> 4 THEN 'Pendiente'
                WHEN fo.f430_ind_estado <> 9 THEN 'No Anulado'
            END AS "Estado del documento",
            
            
            fo.f430_fecha_ts_creacion AS [Fecha Registro de pedido],
            maxFechaAprob.FechaAprobada AS [Fecha Preparacion de pedido],
            fo.f430_fecha_ts_aprob_cartera AS [Fecha aprobacion Cartera],
            --fechainicia AS "Fecha picking",
            MAX(s.fechaRegistro) AS [Fecha de alistamiento],
            G.[Fecha_Despacho] AS [Fecha_Despacho],
            G.Factura AS "Numero de factura",
            vend.f200_razon_social AS "Razon social vendedor",
            terc.f200_razon_social AS "Razon social cliente",
            
            
            CASE 
                WHEN convert(varchar(100), cedi.Remesa) IS NULL THEN UPPER(G.Num_Guia)
                ELSE CONVERT(varchar(100), cedi.Remesa) 
            END AS Guia,
            UPPER(G.Transportador) AS Transportador,
            cedi.[Fecha_Despacho] AS "Fecha de despacho de Pedido",
            cedi.[Fecha_Entrega] AS "Fecha de entrega de Pedido",
            cedi.ESTADO AS "Estado transportadora",
            CASE
                WHEN UPPER(G.Transportador) = 'CONALCA' THEN 'CONALCA'
                WHEN UPPER(G.Transportador) = 'CONALCA BOGOTA' THEN 'Urbano Bogota'
                WHEN UPPER(G.Transportador) = 'IMD & CIA SAS' THEN 'Urbano Medellin'
                WHEN UPPER(G.Transportador) = 'IMD Y CIA SAS' THEN 'Urbano Medellin'
                WHEN UPPER(G.Transportador) = 'MEDELLIN GUSTAVO' THEN 'Urbano Medellin'
                WHEN UPPER(G.Transportador) = 'S&S ADMINISTRATION' THEN 'S&S ADMINISTRATION'
                WHEN UPPER(G.Transportador) = 'TACMO SAS' THEN 'Nacional Guarne-Bogota'
                WHEN UPPER(G.Transportador) = 'TCC' THEN 'Paqueteria excepto Bogota-Medellin'
                WHEN UPPER(G.Transportador) = 'TRANSPORTADORA' THEN 'TRANSPORTADORA'
            END AS RUTA,
            cedi.Direccion_Despacho AS Direccion_Despacho,
            cedi.Ciudad_Despacho AS Ciudad_Despacho,
            f.IdMovimiento AS numero_de_picking
        FROM filtered_orders fo
        LEFT JOIN unoee.dbo.t200_mm_terceros terc ON fo.f430_rowid_tercero_fact = terc.f200_rowid
        LEFT JOIN unoee.dbo.t200_mm_terceros vend ON fo.f430_rowid_tercero_vendedor = vend.f200_rowid
        LEFT JOIN [SGV_BKGENERICABASE1].dbo.v_wms_EPK E ON fo.f430_id_tipo_docto = E.tipoDocto AND fo.f430_consec_docto = E.doctoERP
        LEFT JOIN [SGV_BKGENERICABASE1].dbo.v_wms_clientes C ON E.item = C.item
        LEFT JOIN SGV_BKGENERICABASE1.dbo.t_materiales_por_orden MO ON CAST(MO.eaninsumo AS NVARCHAR) = CAST(E.numPedido AS NVARCHAR) AND MO.color = E.tipoDocto
        LEFT JOIN SGV_BKGENERICABASE1.dbo.T_encabezado_Prepack f ON f.consmov = MO.orden
        LEFT JOIN SGV_BKGENERICABASE1.dbo.T_SSCCxCaja s ON s.idprepack = f.Picking
        LEFT JOIN SGV_BKGENERICABASE1.dbo.t_Guias_Generadas G ON f.IdMovimiento = G.PrepackingID
        LEFT JOIN SGV_BKGENERICABASE1.dbo.V_WMS_Pedidos P ON CAST(P.pedido AS NVARCHAR) = CAST(f.npedid AS NVARCHAR)
        LEFT JOIN cedi_clean cedi ON cedi.pedido_clean = fo.f430_consec_docto AND cedi.NoPicking = f.IdMovimiento
        CROSS APPLY (
            SELECT MAX(fecha_aprobada) AS FechaAprobada
            FROM (VALUES
                (fo.f430_fecha_ts_aprobacion),
                (fo.f430_fecha_ts_aprob_cart_desp),
                (fo.f430_fecha_ts_aprob_cartera),
                (fo.f430_fecha_ts_aprob_cupo_desp),
                (fo.f430_fecha_ts_aprob_margen),
                (fo.f430_fecha_ts_aprobacion_cart)
            ) AS fechas(fecha_aprobada)
        ) AS maxFechaAprob
        WHERE 1=1
        {f"AND terc.f200_razon_social LIKE '%{cliente}%'" if cliente else ""}
        {f"AND G.Factura LIKE '%{factura}%'" if factura else ""}
        
    GROUP BY
    fo.f430_id_tipo_docto,
    fo.f430_consec_docto,
    fo.f430_ind_estado,
    fo.f430_fecha_ts_creacion,
    maxFechaAprob.FechaAprobada,
    fo.f430_fecha_ts_aprob_cartera,
    G.[Fecha_Despacho],
    G.Factura,
    vend.f200_razon_social,
    terc.f200_razon_social,
    G.Transportador,
    G.Num_Guia,
    cedi.Remesa,
    cedi.[Fecha_Despacho],
    cedi.[Fecha_Entrega],
    cedi.ESTADO,
    cedi.Direccion_Despacho,
    cedi.Ciudad_Despacho,    
    f.IdMovimiento
    )
    """

    if count_only:
        query = base_cte + """
        SELECT COUNT(*) AS total_count
        FROM grouped_data;
        """
        return query

    query = base_cte + """
    SELECT *
    FROM grouped_data
    ORDER BY [Fecha Registro de pedido] DESC
    """
    if limit is not None and offset is not None:
        query += f"\nOFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
        print(f"Filtro vendedor recibido: {vendedor}")

    return query

