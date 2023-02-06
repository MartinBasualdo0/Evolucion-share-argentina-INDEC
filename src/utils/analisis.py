import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def chequeo_partidas_com_ind(partida_df, df_comtrade):
    print("Chequeo de los datos para el 2021")
    print("Partidas: Indec: ",len(partida_df[partida_df.año=='2021'].partida.unique()), 
    "|| COMTRADE: ",  len(df_comtrade[df_comtrade.yr == "2021"].cmdCode.unique()))
    print("Exportaciones: INDEC: ", "{:,.0f}".format(partida_df[partida_df.año=='2021']["fob(u$s)"].sum()),
    "|| COMTRADE: " "{:,.0f}".format(df_comtrade[df_comtrade.yr=='2021'].TradeValue.sum()))

def get_dict_subp_anuales(partida_df):
    dict_subp_anuales = {}
    for año in partida_df.año.unique():
        dict_subp_anuales.update({año : partida_df[partida_df.año == año].partida.unique()})
    return dict_subp_anuales

def get_partidas_comunes(dict_subp_anuales):
    subp_2011 = list(dict_subp_anuales.keys())[0]
    part_comunes = set(dict_subp_anuales[subp_2011])
    for key in dict_subp_anuales:
        if key != subp_2011:
            part_comunes &= set(dict_subp_anuales[key])
    return list(part_comunes)

def comparar_indec_comtrade(partida_df, df_comtrade):
    comparacion_indec_comtrade=partida_df.merge(df_comtrade[["yr","cmdCode","TradeValue"]],how="left", right_on = ["yr","cmdCode"], left_on=["año","partida"])\
                                                .drop(["yr","cmdCode"],axis=1)

    comparacion_indec_comtrade = comparacion_indec_comtrade.rename({"fob(u$s)":"indec","TradeValue":"comtrade"},axis=1,)
    comparacion_indec_comtrade.indec = comparacion_indec_comtrade.indec
    comparacion_indec_comtrade["diferencia"] = comparacion_indec_comtrade.indec - comparacion_indec_comtrade.comtrade
    comparacion_indec_comtrade["diferencia en mill"] = comparacion_indec_comtrade.diferencia / 1000000
    return comparacion_indec_comtrade


def testeo_datos_mundiales(df_comtrade_mundo):
    prueba = df_comtrade_mundo.query('yr == "2011"').cmdCode.unique()
    prueba_21 = df_comtrade_mundo.query('yr == "2021"').cmdCode.unique()
    if len([x for x in prueba_21 if x not in prueba ]) == 0:
        print("Si la consulta fue para 2011-2021, todo está correcto. No hay diferencias en las partidas")
    else: print("Hay diferencias en el número de partidas. O hubo un error con la api, o el período es distinto al de 2011-2021. CHEQUEAR!!!")

def genera_prop_mundial(partida_df,df_comtrade_mundo):
    prop_mundial = partida_df.merge(df_comtrade_mundo, right_on=["yr","cmdCode"],left_on=["año","partida"], how = "left")
    prop_mundial = prop_mundial[prop_mundial.año != "2022"].dropna()
    prop_mundial = prop_mundial.drop(["yr","cmdCode"],axis=1,)
    prop_mundial = prop_mundial.rename({"fob(u$s)":"expo_arg", "TradeValue":"expo_mundo"},axis=1,)
    prop_mundial["prop"]= prop_mundial.expo_arg / prop_mundial.expo_mundo
    for año in prop_mundial.año.unique():
        print(f"partidas en {año}:", len(prop_mundial[prop_mundial.año == año].partida.unique()))
    print("-----------------")
    print("Cantidad de proporciones mayores al 100%:",len(prop_mundial[prop_mundial.prop >=1].partida.unique()))
    return prop_mundial

def get_partidas_relevantes(prop_mundial):
    print("Cantidad de partidas que caen por debajo del 0,1% del comercio mundial:")
    for año in prop_mundial.año.unique():
        print(f"{año}:",len(prop_mundial[(prop_mundial.año == año) & (prop_mundial.prop < 0.001) ].partida.unique()))
    part_irrelevantes_2011 = prop_mundial[(prop_mundial.año == "2011") & (prop_mundial.prop < 0.001) ].partida.unique()
    part_irrelevantes_2021 = prop_mundial[(prop_mundial.año == "2021") & (prop_mundial.prop < 0.001) ].partida.unique()
    print("----------------------")
    partidas_irrelevantes = list(set(part_irrelevantes_2011).intersection(part_irrelevantes_2021))
    print(f"Partidas irrelevantes: {len(partidas_irrelevantes)}")

    prop_mundial_sin_irrelevantes = prop_mundial[~prop_mundial.partida.isin(partidas_irrelevantes)].copy()
    print("Partidas para análisis:",len(prop_mundial_sin_irrelevantes.partida.unique()))
    return prop_mundial_sin_irrelevantes

def plot_evolucion_share(prop_mundial_sin_irrelevantes, anio_desde, anio_hasta):
    df_share = prop_mundial_sin_irrelevantes.copy()
    df_share = df_share.drop(["expo_arg","expo_mundo"],axis=1)
    df_share = df_share.pivot_table(values="prop",index=["partida","cmdDescE"], columns="año").reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x = df_share["2011"]*100,y = df_share["2021"]*100, mode = "markers",
                        customdata = np.transpose([df_share.partida,
                                                df_share.cmdDescE.apply(lambda x:x[:50]),
                                                df_share["2011"],
                                                df_share["2021"]
                                                    ]),
                        hovertemplate="<b>Partida: \"%{customdata[0]}\"</b><br>\"%{customdata[1]}\"" 
                                    "<br>Proporcion 2011: %{customdata[2]:.3%}"
                                    "<br>Proporcion 2021: %{customdata[3]:.3%}"
                                    "<br<extra></extra>>",))
    fig.update_layout(template =None)
    fig.update_xaxes(range =[0,50], title_text = "2011", nticks = 20)
    fig.update_yaxes(range =[0,50], title_text = "2021",nticks = 20)
    fig.update_layout(shapes = [{'type': 'line', 'yref': 'paper', 'xref': 'paper', 'y0': 0, 'y1': 1, 'x0': 0, 'x1': 1, "line_dash":"dot"}],
                        # height = 500, width = 500,
                        title_text = f"Evolución del share de la Argentina en las X mundiales por posición del SA<br><sup> {anio_desde}-{anio_hasta}. Fuente: INDEC")
    return fig

def plot_evolucion_share_animado(prop_mundial_sin_irrelevantes, anio_desde, anio_hasta):
    df_share = prop_mundial_sin_irrelevantes.copy()
    df_share.cmdDescE = df_share.cmdDescE.apply(lambda x: x[:40])
    df_share = df_share.rename({"partida":"Partida","prop":"Proporción","año":"Año", "expo_arg":"Exportaciones argentinas"},axis=1)
    df_share

    fig = px.scatter(df_share, x="Partida", y="Proporción", animation_frame="Año", 
                    size_max=40,
            size="Exportaciones argentinas", 
            hover_name="cmdDescE", 
            range_y=[0,.5],
            hover_data= {"Proporción": ':.2%',
                        "Exportaciones argentinas":":,.0f"
            
            }
            )
    fig.update_layout(template = None, separators = ",.", title_text = f"Evolución del share de la Argentina en las X mundiales por posición del SA<br><sup>Una historia animada {anio_desde}-{anio_hasta}. Fuente: INDEC")
    fig.update_xaxes(type='category', nticks = 50, title_text = "Partida")
    fig.update_yaxes(tickformat = ",.0%")
    
    return fig

def bilateral_xIndec_mEspejoComtrade(df_indec, df_comtrade_espejo):
    indec_anual = df_indec.copy()
    indec_anual.ncm = indec_anual.ncm.apply(lambda x: x[:4])
    indec_anual = indec_anual.drop(["pnet(kg)"],axis = 1)\
                    .rename({"ncm":"partida","fob(u$s)":"fob"},axis = 1)\
                    .groupby(["año","partida"],as_index=False).sum("fob")
    df_comtrade_espejo = df_comtrade_espejo.rename({"yr":"año","cmdCode":"partida","TradeValue":"fob"},axis = 1)\
        .groupby(["año", "partida","cmdDescE"],as_index=False).sum("fob")
    df_comtrade_espejo_anual = df_comtrade_espejo.groupby("año").sum("fob")
    indec_anual = indec_anual.groupby("año").sum("fob")

    bilateral = indec_anual.merge(df_comtrade_espejo_anual, how="right", on = "año", suffixes = ["_indec", "_espejoComtrade"])
    bilateral["Diferencia en Millones"] = (bilateral.fob_indec - bilateral.fob_espejoComtrade)/1000000
    return bilateral

def plot_diferencia_espejo(bilateral):
    fig = go.Figure()
    fig.add_trace(go.Bar(x = bilateral.index, y = bilateral.fob_indec/1000000, name = "Fob Indec"))
    fig.add_trace(go.Bar(x = bilateral.index, y = bilateral.fob_espejoComtrade/1000000, name = "Espejo Comtrade"))
    fig.add_trace(go.Bar(x = bilateral.index, y = bilateral["Diferencia en Millones"], name = "Diferencia"))
    fig.update_layout(template = None, separators = ",.", title_text = "Diferencia entre las exportaciones FOB reportadas por el INDEC y las importaciones CIF reportadas por los socios en COMTRADE")
    fig.update_yaxes(tickformat = ",")
    return fig

