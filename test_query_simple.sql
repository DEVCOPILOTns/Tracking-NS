-- Query simplificado para verificar que despachos_cedi tiene datos

-- Primero verificar que la tabla existe y tiene datos
SELECT TOP 10 
    [codigo_pedido],
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

-- Luego verificar que hay pedidos en UNOEE en los últimos 90 días
SELECT TOP 10
    t430.f430_id_tipo_docto,
    t430.f430_consec_docto,
    t430.f430_fecha_ts_creacion
FROM [UNOEE].[dbo].[t430_cm_pv_docto] t430
WHERE CONVERT(date, t430.f430_fecha_ts_creacion) BETWEEN DATEADD(day, -90, CAST(GETDATE() AS date)) AND CAST(GETDATE() AS date)
  AND t430.f430_id_tipo_docto IN ('PVN', 'PNF', 'PVI', 'PVL')

-- Ahora hacer un JOIN basico entre ambas tablas
SELECT TOP 10
    t430.f430_id_tipo_docto,
    t430.f430_consec_docto,
    cedi.codigo_pedido,
    cedi.Remesa,
    cedi.status,
    cedi.direccion
FROM [UNOEE].[dbo].[t430_cm_pv_docto] t430
LEFT JOIN [DWH_NEWSTETIC].[Logistica].[despachos_cedi] cedi 
    ON CAST(cedi.codigo_pedido AS VARCHAR(50)) = CAST(t430.f430_consec_docto AS VARCHAR(50))
WHERE CONVERT(date, t430.f430_fecha_ts_creacion) BETWEEN DATEADD(day, -90, CAST(GETDATE() AS date)) AND CAST(GETDATE() AS date)
  AND t430.f430_id_tipo_docto IN ('PVN', 'PNF', 'PVI', 'PVL')
  AND [Empresa] IN ('NEWSTETIC','NEW STETIC')
