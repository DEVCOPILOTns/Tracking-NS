def get_unified_orders(
    start_date, end_date,
    guia=None, cliente=None, transportadora=None, pedido=None,
    vendedor=None, estado=None, limit=None, offset=None, count_only=False
):
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
        SELECT 
            fo.f430_id_tipo_docto AS [Tipo de documento],
            RTRIM(fo.f430_id_tipo_docto) + '-' + CONVERT(varchar(50), FORMAT(CONVERT(bigint, fo.f430_consec_docto), '00000000')) AS [Numero de pedido],
            RTRIM(fo.f430_id_tipo_docto) + '-' + CONVERT(varchar(50), fo.f430_consec_docto) AS [Keypedido],

            -- columnas que hacen que la granularidad coincida con SSMS
            CASE 
                WHEN convert(varchar(100), cedi.Remesa) IS NULL THEN UPPER(G.Num_Guia)
                ELSE CONVERT(varchar(100), cedi.Remesa)
            END AS [Guia],
            UPPER(G.Transportador) AS [Transportador],

            fo.f430_fecha_ts_creacion AS [Fecha Registro de pedido],
            maxFechaAprob.FechaAprobada AS [Fecha Preparacion de pedido],
            fo.f430_fecha_ts_aprob_cartera AS [Fecha aprobacion Cartera],
            --fechainicia AS [Fecha picking],
            MAX(s.fechaRegistro) AS [Fecha de alistamiento],
            G.[Fecha_Despacho] AS [Fecha_Despacho],
            cedi.[Fecha_Despacho] AS [Fecha de despacho de Pedido],
            cedi.[Fecha_Entrega] AS [Fecha de entrega de Pedido],
            cedi.ESTADO AS [Estado transportadora],

            CASE 
                WHEN fo.f430_ind_estado = 0 THEN 'En elaboración'
                WHEN fo.f430_ind_estado = 1 THEN 'Retenido'
                WHEN fo.f430_ind_estado = 2 THEN 'Aprobado'
                WHEN fo.f430_ind_estado = 3 THEN 'Comprometido'
                WHEN fo.f430_ind_estado = 4 THEN 'Cumplido'
                WHEN fo.f430_ind_estado = 9 THEN 'Anulado'
                WHEN fo.f430_ind_estado <> 9 AND fo.f430_ind_estado <> 4 THEN 'Pendiente'
                WHEN fo.f430_ind_estado <> 9 THEN 'No Anulado'
            END AS [Estado del documento],

            terc.f200_razon_social AS [Razon social cliente],
            vend.f200_razon_social AS [Razon social vendedor],
            G.Factura AS [Numero de factura],

            CASE 
                WHEN UPPER(G.Transportador)='CONALCA'            THEN 'CONALCA'
                WHEN UPPER(G.Transportador)='CONALCA BOGOTA'     THEN 'Urbano Bogota'
                WHEN UPPER(G.Transportador)='IMD & CIA SAS'      THEN 'Urbano Medellin'
                WHEN UPPER(G.Transportador)='IMD Y CIA SAS'      THEN 'Urbano Medellin'
                WHEN UPPER(G.Transportador)='MEDELLIN GUSTAVO'   THEN 'Urbano Medellin'
                WHEN UPPER(G.Transportador)='S&S ADMINISTRATION' THEN 'S&S ADMINISTRATION'
                WHEN UPPER(G.Transportador)='TACMO SAS'          THEN 'Nacional Guarne-Bogota'
                WHEN UPPER(G.Transportador)='TCC'                THEN 'Paqueteria excepto Bogota-Medellin'
                WHEN UPPER(G.Transportador)='TRANSPORTADORA'     THEN 'TRANSPORTADORA'
            END AS [RUTA],

            cedi.Direccion_Despacho AS [Direccion_Despacho],
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

            f.IdMovimiento AS [numero_de_picking],

            -- métricas item (si las usas en la grilla)
            SUM(s.cantidadAduanada) AS Cantidad

        FROM filtered_orders fo
        LEFT JOIN unoee.dbo.t200_mm_terceros terc ON fo.f430_rowid_tercero_fact=terc.f200_rowid
        LEFT JOIN unoee.dbo.t200_mm_terceros vend ON fo.f430_rowid_tercero_vendedor=vend.f200_rowid
        LEFT JOIN [SGV_BKGENERICABASE1].dbo.v_wms_EPK E
               ON fo.f430_id_tipo_docto = E.tipoDocto AND fo.f430_consec_docto = E.doctoERP
        LEFT JOIN [SGV_BKGENERICABASE1].dbo.v_wms_clientes C ON E.item = C.item
        LEFT JOIN SGV_BKGENERICABASE1.dbo.t_materiales_por_orden MO
               ON CAST(MO.eaninsumo AS NVARCHAR) = CAST(E.numPedido AS NVARCHAR)
              AND MO.color = E.tipoDocto
        LEFT JOIN SGV_BKGENERICABASE1.dbo.T_encabezado_Prepack f ON f.consmov = MO.orden
        LEFT JOIN SGV_BKGENERICABASE1.dbo.T_SSCCxCaja s ON s.idprepack = f.Picking
        LEFT JOIN SGV_BKGENERICABASE1.dbo.t_Guias_Generadas G ON f.IdMovimiento = G.PrepackingID
        LEFT JOIN SGV_BKGENERICABASE1.dbo.V_WMS_Articulos A
               ON CAST(s.EanContenido AS NVARCHAR) = CAST(A.productoEAN AS NVARCHAR)

        -- Igual que SSMS: cruzar por Pedido + NoPicking
        LEFT JOIN cedi_clean cedi
               ON cedi.pedido_clean = fo.f430_consec_docto
              AND cedi.NoPicking   = f.IdMovimiento

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
    {f"AND upper(G.Num_Guia) LIKE '%{guia.upper()}%'" if guia else ""}
    {f"AND terc.f200_razon_social LIKE '%{cliente}%'" if cliente else ""}
        {f"AND UPPER(G.Transportador) LIKE '%{transportadora.upper()}%'" if transportadora else ""}
        {f"AND vend.f200_razon_social LIKE '%{vendedor}%'" if vendedor else ""}
        {estado_condition}

        -- MUY IMPORTANTE: la granularidad exacta (como en tu SSMS)
        GROUP BY
            fo.f430_id_tipo_docto,
            fo.f430_consec_docto,
            CASE 
                WHEN UPPER(G.Transportador) = 'TCC' THEN UPPER(G.Num_Guia)
                ELSE CONVERT(varchar(100), cedi.Remesa)
            END,
            UPPER(G.Transportador),
            fo.f430_fecha_ts_creacion,
            maxFechaAprob.FechaAprobada,
            fo.f430_fecha_ts_aprob_cartera,
            G.[Fecha_Despacho],
            G.Num_Guia,
            cedi.Remesa,
            cedi.[Fecha_Despacho],
            cedi.[Fecha_Entrega],
            cedi.ESTADO,
            terc.f200_razon_social,
            vend.f200_razon_social,
            G.Factura,
            cedi.Direccion_Despacho,
            cedi.Ciudad_Despacho,
            fo.f430_ind_estado,
            f.IdMovimiento
    )
    """

    if count_only:
        # Contar filas del resultado (como lo ves en SSMS)
        query = base_cte + """
        SELECT COUNT(*) AS total_count
        FROM grouped_data;
        """
        return query

    # Traer filas (como SSMS) + paginación si aplica
    query = base_cte + """
    SELECT *
    FROM grouped_data
    ORDER BY OrdenEstado, [Fecha Registro de pedido] DESC
    """
    if limit is not None and offset is not None:
        query += f"\nOFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"

    return query
