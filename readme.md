# Evolución del share de las exportaciones Argentinas con datos del INDEC

La idea fue recrear el análisis de la evolución del _share_ del comercio Argentino utilizando como fuente de datos para las exportaciones argentinas al INDEC. Esto se realiza a sabiendas que a partir de marzo del 2018 hubo un quiebre con la metodología al presentar los datos relevantes para el presente trabajo con secreto estadístico.


## Librerías requeridas

`conda create -n share-indec pip pandas plotly ipykernel nbformat selenium requests`

## Metodología resumida:

- Fijación del período de análisis, respetando al trabajo original. 

- _Scrap_ de los datos publicados por el INDEC para las exportaciones.

- Consulta a la API de COMTRADE. 

Filtros a los datos:

- Las partidas tienen que haber sido exportadas todos los años bajo análisis

- Su participación en el comercio internacional tiene que ser relevante (se mantuvo el 0,1%)
  
- No tiene que presentar una diferencia significativa a lo reportado por COMTRADE. En realidad, importa que los datos de COMTRADE no sean significativamente mayores a los del INDEC, lo que indicaría que el secreto estadístico en dicha partida es sustantivo.

