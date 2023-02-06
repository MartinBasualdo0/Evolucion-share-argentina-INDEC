import pandas as pd
from time import sleep
import datetime
import requests
import plotly.graph_objects as go
from itertools import zip_longest
import json
import codecs



def get_partidas_comtrade(anio_desde, anio_hasta):
    '''comtrade api para obtener subpartidas'''
    dfs = []
    for anio in range(int(anio_desde),int(anio_hasta)+1):
        sleep(10)
        json=requests.get('http://comtrade.un.org/api/get',
                    params=dict(
                        max=1000000,
                        type='C',
                        freq = 'A',
                        r = 32, #argentina
                        ps = anio, #anio mes
                        px = 'HS',
                        p = 0, #0 es mundo
                        rg = 2, #1 impo, 2 expo, "all"
                        cc = "AG4", #0101
                        fmt = 'json',            
                            )).json()
        df = pd.DataFrame(json['dataset'])
        df = df[["yr","rgDesc","rtTitle","aggrLevel","cmdCode","cmdDescE","TradeValue"]]
        df = df[df["aggrLevel"] == 4]
        dfs.append(df)
        print(str(anio), "|| Observaciones:" ,json["validation"]["count"]["value"], "|| Total:",len(dfs),"de",anio_hasta-anio_desde+1)
    df = pd.concat(dfs).reset_index(drop=True)
    df.yr = df.yr.astype(str)
    return df

def plot_secreto_comtrade(df):
    df_secreto = df[df.cmdCode == "9999"].copy()
    df_sin_secreto = df[(df.cmdCode != "9999")].copy()
    df_sin_secreto = df_sin_secreto.groupby("yr",as_index=False).sum("TradeValue")
    prop_secreto = df_sin_secreto.merge(df_secreto[["yr","TradeValue"]],how="left", on = "yr",suffixes=["_total","_secreto"])
    prop_secreto["proporcion"] = prop_secreto["TradeValue_secreto"] / prop_secreto["TradeValue_total"]*100
    prop_secreto = prop_secreto.drop(['aggrLevel'],axis=1)
    fig = go.Figure()
    fig.add_trace(go.Bar(x = df_secreto.yr, y = df_secreto["TradeValue"]/1000000, name = "9999"))
    fig.add_trace(go.Bar(x = df_sin_secreto.yr, y = df_sin_secreto["TradeValue"]/1000000, name = "FOB sin secreto"))
    fig.update_yaxes(tickformat = ",")
    fig.update_layout(template = None, separators = ",.", title_text = "Secreto estadístico a nivel partida en millones de USD<br>Fuente: Comtrade")
    return prop_secreto, fig

def grouped(iterable, n):
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    #return zip(*[iter(iterable)]*n)
    return list(zip_longest(*[iter(iterable)]*n, fillvalue="0"))

def get_datosmundiales(part_comunes, anio_desde="2011", anio_hasta="2021"):
    # inicio = datetime.datetime.now()
    dfs = []
    contador = 1
    for a,b,c,d,e in grouped(range(int(anio_desde),int(anio_hasta)+1),5):
        contador_subpartidas = 10
        years = [a, b, c, d, e]
        group_years = [years[i:i+5] for i in range(0, len(years), 5)]
        group_years = [[str(y) for y in year if int(y) >0] for year in group_years]
        ps = [','.join(group) for group in group_years][0]
        
        for q,r,s,t,u,v,w,x,y,z in grouped(part_comunes,10):
            try:
                json=requests.get('http://comtrade.un.org/api/get',
                            params=dict(
                                max=1000000,
                                type='C',
                                freq = 'A',
                                r = "all",
                                ps = ps, #anio mes
                                px = 'HS',
                                p = 0, #0 es mundo
                                rg = 2, #1 impo, 2 expo, "all"
                                cc = q+","+r+","+s+","+t+","+u+","+v+","+w+","+x+","+y+","+z,
                                fmt = 'json',            
                                    )).json()
                try:    
                    df = pd.DataFrame(json["dataset"])[["yr","rgDesc","rtTitle","cmdCode","cmdDescE","TradeValue"]]
                    dfs.append(df)
                    print(a,b,c,d,e,"||", q,r,s,t,u,v,w,x,y,z,"||","observaciones",json["validation"]["count"]["value"], "|| Progreso:",contador_subpartidas, "de", len(part_comunes), "|| consultas:",contador)
                except KeyError:
                    print("no hay data para", a,b,c,d,e,"||", q,r,s,t,u,v,w,x,y,z,) 
            except:
                print("Excessive number of requests. Sleeping an hour", datetime.datetime.now())
                sleep(3600)
                json=requests.get('http://comtrade.un.org/api/get',
                            params=dict(
                                max=1000000,
                                type='C',
                                freq = 'A',
                                r = "all",
                                ps = ps, #anio mes
                                px = 'HS',
                                p = 0, #0 es mundo
                                rg = 2, #1 impo, 2 expo, "all"
                                cc = q+","+r+","+s+","+t+","+u+","+v+","+w+","+x+","+y+","+z,
                                fmt = 'json',            
                                    )).json()                    
                try:    
                    df = pd.DataFrame(json["dataset"])[["yr","rgDesc","rtTitle","cmdCode","cmdDescE","TradeValue"]]
                    dfs.append(df)
                    print(a,b,c,d,e,"||", q,r,s,t,u,v,w,x,y,z,"||","observaciones",json["validation"]["count"]["value"], "|| Progreso:",contador_subpartidas, "de", len(part_comunes), "|| consultas:",contador)
                except KeyError:
                    print("no hay data para", a,b,c,d,e,"||", q,r,s,t,u,v,w,x,y,z,) 
                
            contador_subpartidas += 10
            contador += 1
            if contador >= 100:
                # momento_pausa = datetime.datetime.now()
                tiempo_pausa = 3600
                print(f"Límite de consultas alcanzado, deteniendo la ejecución por {tiempo_pausa} segundos",datetime.datetime.now())
                if tiempo_pausa > 0: sleep(tiempo_pausa) 
                contador = 0  # reiniciar el contador
        sleep(2)
        
    return dfs

def correccion_descrip_comtrade(df_comtrade_mundo):
    '''Existen partidas cuyas descripciones se diferencian por un "."
    '''
    df = df_comtrade_mundo.copy()
    cmd_dict = {}
    for _, row in df.iterrows():
        if row["cmdCode"] not in cmd_dict:
            cmd_dict[row["cmdCode"]] = row["cmdDescE"]
            
    df["cmdDescE"] = df["cmdCode"].map(cmd_dict)
    return df

def get_lista_paises_comtrade():
    url = "https://comtrade.un.org/Data/cache/reporterAreas.json"
    # url = "https://comtrade.un.org/Data/cache/classificationH4.json"

    response = requests.get(url)
    data = json.loads(codecs.decode(response.content, 'utf-8-sig'))
    return data["results"]

def get_expo_arg_espejo(anio_desde="2011", anio_hasta="2021"):
    # inicio = datetime.datetime.now()
    print("Inicio de pedidos a la api de COMTRADE:",datetime.datetime.now())
    data = get_lista_paises_comtrade()
    id_paises = [d['id'] for d in data][1:]
    dfs = []
    contador = 1
    for a,b,c,d,e in grouped(range(int(anio_desde),int(anio_hasta)+1),5):
        contador_paises = 5
        years = [a, b, c, d, e]
        group_years = [years[i:i+5] for i in range(0, len(years), 5)]
        group_years = [[str(y) for y in year if int(y) >0] for year in group_years]
        ps = [','.join(group) for group in group_years][0]
        
        for v,w,x,y,z in grouped(id_paises,5):
            try:
                json=requests.get('http://comtrade.un.org/api/get',
                            params=dict(
                                max=1000000,
                                type='C',
                                freq = 'A',
                                r = v+","+w+","+x+","+y+","+z,
                                ps = ps, #anio mes
                                px = 'HS',
                                p = 32, #0 es mundo
                                rg = 1, #1 impo, 2 expo, "all"
                                cc = "AG4",
                                fmt = 'json',            
                                    )).json()
                try:    
                    df = pd.DataFrame(json["dataset"])[["yr","rgDesc","rtTitle","cmdCode","cmdDescE","TradeValue"]]
                    dfs.append(df)
                    print(a,b,c,d,e,"||", v,w,x,y,z,"||","observaciones",json["validation"]["count"]["value"], "|| Progreso:",contador_paises, "de", len(id_paises), "|| consultas:",contador)
                except KeyError:
                    print("no hay data para estos países:",v,w,x,y,z,"en estos años:",a,b,c,d,e)
            except:
                print("Excessive number of requests. Sleeping for half an hour.", datetime.datetime.now())
                sleep(1800) # sleep for 1800 seconds (30 minutes)
            
            contador_paises += 5
            contador += 1
            if contador >= 100:
                # momento_pausa = datetime.datetime.now()
                tiempo_pausa = 3600
                print(f"Límite de consultas alcanzado, deteniendo la ejecución por {tiempo_pausa} segundos",datetime.datetime.now())
                if tiempo_pausa > 0: sleep(tiempo_pausa) 
                contador = 0  # reiniciar el contador
            sleep(2)
        
    return dfs    


