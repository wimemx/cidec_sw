# -*- coding: utf-8 -*-
# Create your views here.

from django.template import RequestContext
from django.http import *
from django.shortcuts import render_to_response
from math import *
from decimal import *

import collections
import datetime
from time import strftime

from dateutil.relativedelta import *
from calendar import monthrange


from c_center.models import *
from electric_rates.models import *

def demandafacturable(kwbase, kwintermedio, kwpunta, region, tarifa, fecha):
    df = 0

    #Se obtienen los Factores de Reduccion en base a la zona, la tarifa y la fecha
    factores_reduccion = ElectricRatesDetail.objects.filter(electric_rate = tarifa).filter(region_id = region).filter(date_init__lte = datetime.date(fecha.year, fecha.month, fecha.day)).filter(date_end__gte = datetime.date(fecha.year, fecha.month, fecha.day))
    fri = factores_reduccion[0].FRI
    frb = factores_reduccion[0].FRB

    primermax = kwintermedio - kwpunta
    if primermax < 0:
        primermax = 0

    segundomax = kwbase-max(kwintermedio, kwpunta)
    if segundomax < 0:
        segundomax = 0

    df = kwpunta + fri * primermax + frb * segundomax

    return int(ceil(df))

def demandafacturable_tarifa(kwbase, kwintermedio, kwpunta, tarifa):
    df = 0

    #Se obtienen los Factores de Reduccion en base a la zona, la tarifa y la fecha
    factores_reduccion = ElectricRatesDetail.objects.get(id = tarifa)
    fri = factores_reduccion.FRI
    frb = factores_reduccion.FRB

    primermax = kwintermedio - kwpunta
    if primermax < 0:
        primermax = 0

    segundomax = kwbase-max(kwintermedio, kwpunta)
    if segundomax < 0:
        segundomax = 0

    df = kwpunta + fri * primermax + frb * segundomax

    return int(ceil(df))


def costoenergia(kwbase, kwintermedio, kwpunta, region, tarifa, fecha):
    costo_energia = 0

    #Se obtienen las tarifas para cada kw
    tarifas = ElectricRatesDetail.objects.filter(electric_rate = tarifa).filter(region_id = region).filter(date_init__lte = datetime.date(fecha.year, fecha.month, fecha.day)).filter(date_end__gte = datetime.date(fecha.year, fecha.month, fecha.day))
    tarifa_kwbase = tarifas[0].KWHB
    tarifa_kwintermedio = tarifas[0].KWHI
    tarifa_kwpunta = tarifas[0].KWHP

    costo_energia = kwbase*tarifa_kwbase + kwintermedio*tarifa_kwintermedio + kwpunta*tarifa_kwpunta

    return costo_energia

def costoenergia_tarifa(kwbase, kwintermedio, kwpunta, tarifa_id):
    costo_energia = 0

    #Se obtienen las tarifas para cada kw
    tarifas = ElectricRatesDetail.objects.get(id = tarifa_id)

    tarifa_kwbase = tarifas.KWHB
    tarifa_kwintermedio = tarifas.KWHI
    tarifa_kwpunta = tarifas.KWHP

    costo_energia = kwbase*tarifa_kwbase + kwintermedio*tarifa_kwintermedio + kwpunta*tarifa_kwpunta

    return costo_energia


def costodemandafacturable(demandaf, region, tarifa, fecha):
    precio = 0

    #Se obtiene el precio de la demanda
    tarifas = ElectricRatesDetail.objects.filter(electric_rate = tarifa).filter(region_id = region).filter(date_init__lte = datetime.date(fecha.year, fecha.month, fecha.day)).filter(date_end__gte = datetime.date(fecha.year, fecha.month, fecha.day))
    tarifa_demanda = tarifas[0].KDF

    return (demandaf * tarifa_demanda)

def costodemandafacturable_tarifa(demandaf, tarifa_id):
    precio = 0

    #Se obtiene el precio de la demanda
    tarifas = ElectricRatesDetail.objects.get(id = tarifa_id)
    tarifa_demanda = tarifas.KDF

    return (demandaf * tarifa_demanda)


def fpbonificacionrecargo(fp):
    fp_valor = 0

    if fp < 90:
        fp_valor = Decimal(3.0/5.0)*((Decimal(90.0)/fp)-1)*100
    else:
        fp_valor = Decimal(1.0/4.0)*(1-(Decimal(90.0)/fp))*100

    return float(fp_valor)

def costofactorpotencia(fp, costo_energia, costo_df):
    costo_fp = 0

    if fp < 90:
        costo_fp = float((costo_energia + costo_df)/100)*fpbonificacionrecargo(fp)
    else:
        costo_fp = float((costo_energia + costo_df)/100)*fpbonificacionrecargo(fp)*-1

    return costo_fp


def obtenerSubtotal(costo_energia, costo_df, costo_fp):
    return (float(costo_energia) + float(costo_df) + float(costo_fp))

def obtenerIva(c_subtotal, iva):
    iva = iva/100.0
    return float(c_subtotal)*float(iva)

def obtenerTotal(c_subtotal, iva):
    iva = iva/100.0 + 1
    return float(c_subtotal)*float(iva)

def factorpotencia(kwh, kvarh):
    fp = 0
    if kwh != 0 and kvarh != 0:
        fp =  (kwh/Decimal(pow((pow(kwh,2)+pow(kvarh,2)),.5)))*100
    return fp

def obtenerDemanda(arr_kw):
    demanda_maxima = 0
    if arr_kw:
        try:
            longitud = len(arr_kw)
            if longitud >= 3:
                for indice, demanda in enumerate(arr_kw):
                    if indice+1 < (longitud -1) and indice + 2 <= (longitud - 1):
                        prom = (arr_kw[indice] + arr_kw[indice+1] + arr_kw[indice+2])/Decimal(3.0)
                        if prom > demanda_maxima:
                            demanda_maxima = int(ceil(prom))
            else:
                demanda_maxima = 0

        except IndexError:
            print "IndexError"
            demanda_maxima = 0
        except TypeError:
            print "TypeError"
            demanda_maxima = 0

    return demanda_maxima


def obtenerFestivos(year):

    """
    Obtiene los dias festivos almacenados en la tabla Holidays.
    Regresa una lista con las fechas exactas de los dias festivos para este año

    Ejemplo:
    1, 01 -> 1 de enero de 2012
    1-Lun, 02 = 1er Lunes de Febrero 2012 -> 6 de febrero de 2012


    """
    lista_festivos = []

    actual_year = year
    holidays = Holydays.objects.all()

    lst_days = {}
    lst_days['1'] = 'Lun'
    lst_days['2'] = 'Mar'
    lst_days['3'] = 'Mie'
    lst_days['4'] = 'Jue'
    lst_days['5'] = 'Vie'
    lst_days['6'] = 'Sab'
    lst_days['0'] = 'Dom'

    if holidays:
        for hday in holidays:

            f_var = hday.day.split('-')
            if len(f_var) > 1:
                dia_mes = 1
                ahorita = 1
                n_day = f_var[0]
                w_day = f_var[1]
                month_days = monthrange(actual_year,hday.month)
                while(dia_mes < month_days[1]-1):
                    #st_time = time.strptime("%02d" % (c_day)+" "+"%02d" % (mes)+" "+str(actual_year), "%d %m %Y")
                    st_time = time.strptime("%02d" % (dia_mes)+" "+"%02d" % (hday.month)+" "+str(actual_year), "%d %m %Y")
                    week_day = strftime("%w", st_time)
                    if lst_days[week_day] == w_day:
                        if ahorita == int(n_day):
                            lista_festivos.append(strftime("%d %m %Y",st_time))
                            break
                        else:
                            ahorita += 1

                    dia_mes += 1
            else:
                # Si es 1 de diciembre, se verifica que sea año de elecciones.
                # En caso afirmativo se agrega a la lista de dias festivos
                if int(hday.day) == 1 and int(hday.month) == 12:
                    if (actual_year - 1946)%6 == 0:
                        st_time = time.strptime("%02d" % int(hday.day)+" "+"%02d" % int(hday.month)+" "+str(actual_year), "%d %m %Y")
                        lista_festivos.append(strftime("%d %m %Y", st_time))
                else:
                    st_time = time.strptime("%02d" % int(hday.day)+" "+"%02d" % int(hday.month)+" "+str(actual_year), "%d %m %Y")
                    lista_festivos.append(strftime("%d %m %Y", st_time))

    return lista_festivos

def obtenerCatalogoGrupos():
    """

    Se regresa un catálogo que indica a qué grupo pertenece cada día de la semana.

    """
    group_days_bd = Groupdays.objects.all();
    group_days = {}

    if group_days_bd:
        for g_days in group_days_bd:
            if g_days.sunday:
                group_days[0] = g_days.id
            if g_days.monday:
                group_days[1] = g_days.id
            if g_days.tuesday:
                group_days[2] = g_days.id
            if g_days.wednesday:
                group_days[3] = g_days.id
            if g_days.thursday:
                group_days[4] = g_days.id
            if g_days.friday:
                group_days[5] = g_days.id
            if g_days.saturday:
                group_days[6] = g_days.id
            if g_days.holydays:
                group_days[7] = g_days.id

    return group_days

def obtenerGrupo(catalogo_grupos, fecha):
    """
    A partir de una fecha, se obtiene a qué grupo de días pertenece: Lun a Vie, Sab o Dom y Festivos

    """

    num_dia = 0

    dias_festivos = obtenerFestivos(fecha.year)
    #if (str(fecha.day)+" "+str(fecha.month)+" "+str(fecha.year)) in dias_festivos:
    if fecha in dias_festivos:
        num_dia = 7
    else:
        st_time = time.strptime(str(fecha.day)+" "+str(fecha.month)+" "+str(fecha.year), "%d %m %Y")
        num_dia = strftime("%w", st_time)

    return catalogo_grupos[int(num_dia)]



def obtenerTipoPeriodo(fecha, region, tarifa, catalogo_grupos):
    """
    Se obtiene el tipo de periodo de una lectura, en base a la fecha y hora en que fue tomada, región y tarifa.

    """
    grupo_id = obtenerGrupo(catalogo_grupos, fecha)
    horario_ver_inv = [date.pk for date in DateIntervals.objects.filter(date_init__lte= datetime.date(fecha.year,fecha.month,fecha.day)).filter(date_end__gte = datetime.date(fecha.year,fecha.month,fecha.day))]#.filter(region = region)

    electric_type = ElectricRatesPeriods.objects.filter(region = region).filter(electric_rate = tarifa).filter(date_interval__in = horario_ver_inv).filter(groupdays = grupo_id).filter(time_init__lte = datetime.time(fecha.hour,fecha.minute)).filter(time_end__gte = datetime.time(fecha.hour,fecha.minute))

    return electric_type[0].period_type

def obtenerKWTarifa(pr_powermeter, tarifa_id, region, tipo_tarifa):
    """
    Recibe el medidor.
    tarifa_id = Identificar de las tarifas de un mes
    tipo_tarifa = Tarifa que tiene contratada (HM, OM...)

    """
    tarifaObj = ElectricRatesDetail.objects.get(id = tarifa_id)

    fecha_inicio = str(tarifaObj.date_init) + " 00:00:00"
    fecha_fin = str(tarifaObj.date_end) + " 23:59:59"
    lecturasObj = ElectricData.objects.filter(profile_powermeter = pr_powermeter, medition_date__range=(fecha_inicio, fecha_fin)).order_by('medition_date')

    catalogo_grupos = obtenerCatalogoGrupos();

    demanda_base = []
    demanda_intermedio = []
    demanda_punta = []

    valores_periodo = {}

    if lecturasObj:
        for lectura in lecturasObj:
            tipo_periodo = obtenerTipoPeriodo(lectura.medition_date, region, tipo_tarifa,catalogo_grupos)
            if tipo_periodo == 'base':
                demanda_base.append(lectura.kW)
            elif tipo_periodo == 'intermedio':
                demanda_intermedio.append(lectura.kW)
            elif tipo_periodo == 'punta':
                demanda_punta.append(lectura.kW)

        valores_periodo['base'] = obtenerDemanda(demanda_base)
        valores_periodo['intermedio'] = obtenerDemanda(demanda_intermedio)
        valores_periodo['punta'] = obtenerDemanda(demanda_punta)
    else:
        valores_periodo['base'] = 0
        valores_periodo['intermedio'] = 0
        valores_periodo['punta'] = 0

    return valores_periodo



def obtenerKWhNetosTarifa(pr_powermeter, tarifa_id):
    tarifaObj = ElectricRatesDetail.objects.get(id = tarifa_id)
    fecha_inicio = str(tarifaObj.date_init) + " 00:00:00"
    fecha_fin = str(tarifaObj.date_end) + " 23:59:59"

    kwh_netos = 0
    lecturasObj = ElectricData.objects.filter(profile_powermeter = pr_powermeter, medition_date__range=(fecha_inicio, fecha_fin)).order_by('medition_date')
    if lecturasObj:
        total_lecturas = len(lecturasObj)
        kwh_inicial = lecturasObj[0].kWhIMPORT
        kwh_final = lecturasObj[total_lecturas-1].kWhIMPORT
        kwh_netos = kwh_final - kwh_inicial

    return kwh_netos

def obtenerKWhTarifa(pr_powermeter, tarifa_id, region, tarifa_hm):
    """
    Recibe el medidor.
    tarifa_id = Identificar de las tarifas de un mes
    tipo_tarifa = Tarifa que tiene contratada (HM, OM...)

    """
    tarifaObj = ElectricRatesDetail.objects.get(id = tarifa_id)

    fecha_inicio = str(tarifaObj.date_init) + " 00:00:00"
    fecha_fin = str(tarifaObj.date_end) + " 23:59:59"
    lecturasObj = ElectricData.objects.filter(profile_powermeter = pr_powermeter, medition_date__range=(fecha_inicio, fecha_fin)).order_by('medition_date')

    catalogo_grupos = obtenerCatalogoGrupos();

    kwh_base = []
    kwh_intermedio = []
    kwh_punta = []

    valores_kwh = {}
    valores_kwh['base'] = 0
    valores_kwh['intermedio'] = 0
    valores_kwh['punta'] = 0

    tipo_tarifa_global = None
    kwh_primero = None
    kwh_ultimo = None

    if lecturasObj:
        for lectura in lecturasObj:
            tipo_tarifa_actual = obtenerTipoPeriodo(lectura.medition_date, region, tarifa_hm, catalogo_grupos)

            if not tipo_tarifa_global:
                tipo_tarifa_global = tipo_tarifa_actual

            #Primer Lectura
            if not kwh_primero:
                kwh_primero = lectura.kWhIMPORT
            kwh_ultimo = lectura.kWhIMPORT

            if tipo_tarifa_global != tipo_tarifa_actual:
                kwh_netos = kwh_ultimo - kwh_primero

                if tipo_tarifa_global == 'base':
                    kwh_base.append(kwh_netos)
                    valores_kwh['base'] += kwh_netos
                elif tipo_tarifa_global == 'intermedio':
                    kwh_intermedio.append(kwh_netos)
                    valores_kwh['intermedio'] += kwh_netos
                elif tipo_tarifa_global == 'punta':
                    kwh_punta.append(kwh_netos)
                    valores_kwh['punta'] += kwh_netos

                kwh_primero = kwh_ultimo
                tipo_tarifa_global = tipo_tarifa_actual


        kwh_netos = kwh_ultimo - kwh_primero

        if tipo_tarifa_global == 'base':
            kwh_base.append(kwh_netos)
            valores_kwh['base'] += kwh_netos
        elif tipo_tarifa_global == 'intermedio':
            kwh_intermedio.append(kwh_netos)
            valores_kwh['intermedio'] += kwh_netos
        elif tipo_tarifa_global == 'punta':
            kwh_punta.append(kwh_netos)
            valores_kwh['punta'] += kwh_netos
    else:
        valores_kwh['base'] = 0
        valores_kwh['intermedio'] = 0
        valores_kwh['punta'] = 0

    return valores_kwh


def obtenerKVARHTarifa(pr_powermeter, tarifa_id):
    tarifaObj = ElectricRatesDetail.objects.get(id = tarifa_id)
    fecha_inicio = str(tarifaObj.date_init) + " 00:00:00"
    fecha_fin = str(tarifaObj.date_end) + " 23:59:59"

    kvarh_netos = 0
    lecturasObj = ElectricData.objects.filter(profile_powermeter = pr_powermeter, medition_date__range=(fecha_inicio, fecha_fin)).order_by('medition_date')
    if lecturasObj:
        total_lecturas = len(lecturasObj)
        kvarh_inicial = lecturasObj[0].kvarhNET
        kvarh_final = lecturasObj[total_lecturas-1].kvarhNET
        kvarh_netos = kvarh_final - kvarh_inicial

    return kvarh_netos

def obtenerFPTarifa(pr_powermeter, tarifa_id):
    kvarh = obtenerKVARHTarifa(pr_powermeter, tarifa_id)
    kwh = obtenerKWhNetosTarifa(pr_powermeter, tarifa_id)
    return factorpotencia(kwh, kvarh)

def obtenerDemandaMaximaTarifa(pr_powermeter, tarifa_id):
    arr_kw = []

    tarifaObj = ElectricRatesDetail.objects.get(id = tarifa_id)
    fecha_inicio = str(tarifaObj.date_init) + " 00:00:00"
    fecha_fin = str(tarifaObj.date_end) + " 23:59:59"

    lecturasObj = ElectricData.objects.filter(profile_powermeter = pr_powermeter, medition_date__range=(fecha_inicio, fecha_fin)).order_by('medition_date')

    for lectura in lecturasObj:
        arr_kw.append(lectura.kW)

    return obtenerDemanda(arr_kw)

def obtenerFactorCargaTarifa(pr_powermeter, tarifa_id):
    factor_carga = 0

    tarifaObj = ElectricRatesDetail.objects.get(id = tarifa_id)
    m_range = monthrange(tarifaObj.date_init.year, tarifaObj.date_init.month)
    num_dias = m_range[1]
    num_horas = 24 * num_dias
    demanda_maxima = obtenerDemandaMaximaTarifa(pr_powermeter, tarifa_id)
    energia_consumida = obtenerKWhNetosTarifa(pr_powermeter, tarifa_id)

    if demanda_maxima != 0 and energia_consumida != 0:
        factor_carga = (energia_consumida / (demanda_maxima * num_horas)) * 100

    return factor_carga

def obtenerCostoPromedioKWH(tarifa_id):
    costo = 0
    tarifaObj = ElectricRatesDetail.objects.get(id = tarifa_id)
    costo = (tarifaObj.KWHB + tarifaObj.KWHI + tarifaObj.KWHP)/Decimal(3.0)
    return costo


def obtenerHistorico(pr_powermeter, tarifa_id, region, num_meses, tipo_tarifa):

    arr_historico = []

    tarifaObj = ElectricRatesDetail.objects.get(id = tarifa_id)
    fecha_fin = tarifaObj.date_init
    fecha_inicio = fecha_fin+relativedelta(months=-num_meses)

    tarifasPeriodo = ElectricRatesDetail.objects.filter(region = region).filter(date_init__range=(fecha_inicio, fecha_fin)).order_by('date_init')
    for tarifaPer in tarifasPeriodo:
        dict_periodo = {}
        dict_periodo["fecha"] = tarifaPer.date_init
        dict_kw = obtenerKWTarifa(pr_powermeter, tarifaPer.id, region, tipo_tarifa)
        dict_periodo["kw_base"] = dict_kw['base']
        dict_periodo["kw_intermedio"] = dict_kw['intermedio']
        dict_periodo["kw_punta"] = dict_kw['punta']
        dict_periodo["demanda_maxima"] = obtenerDemandaMaximaTarifa(pr_powermeter, tarifaPer.id)
        dict_periodo["total_kwh"] = obtenerKWhNetosTarifa(pr_powermeter, tarifaPer.id)
        dict_periodo["kvarh"] =  obtenerKVARHTarifa(pr_powermeter, tarifaPer.id)
        dict_periodo["factor_potencia"] = factorpotencia(dict_periodo["total_kwh"], obtenerKVARHTarifa(pr_powermeter, tarifaPer.id))
        dict_periodo["factor_carga"] = obtenerFactorCargaTarifa(pr_powermeter, tarifaPer.id)
        dict_periodo["costo_promedio"] = obtenerCostoPromedioKWH(tarifaPer.id)

        arr_historico.append(dict_periodo)

    return arr_historico


def tarifaHM(pr_powermeter, start_date, end_date, region):
    readings = ElectricData.objects.filter(profile_powermeter = pr_powermeter, medition_date__range=(start_date, end_date)).order_by('medition_date')

    catalogo_grupos = obtenerCatalogoGrupos();

    tarifa = 1
    tarifas_id = []
    relacion_tarifa_lectura = collections.defaultdict(dict)

    if readings:
        for reading in readings:
            l_tar_co = ElectricRatesDetail.objects.filter(electric_rate = tarifa).filter(region_id = region).filter(date_init__lte = datetime.date(reading.medition_date.year,reading.medition_date.month,reading.medition_date.day)).filter(date_end__gte = datetime.date(reading.medition_date.year,reading.medition_date.month,reading.medition_date.day))

            """
               Se guarda una relación: Tarifa - Lectura - Tipo de Tarifa
               Ej: Tarifa Junio - Lectura No. 6789 - Intermedio

            """
            relacion_tarifa_lectura[l_tar_co[0].id][reading.id] = obtenerTipoPeriodo(reading.medition_date, region, tarifa,catalogo_grupos)

            tarifa_actual = l_tar_co[0].id
            if tarifa_actual not in tarifas_id:
                tarifas_id.append(tarifa_actual)


    #Variables que contienen toda la informacion del recibo de CFE
    demanda_facturable_total = 0
    factor_potencia_total = 0
    costo_energia_total = 0
    costo_demanda_facturable = 0
    costo_factor_potencia = 0
    subtotal_final = 0
    iva_total = 0
    total_final = 0
    kw_totales = 0
    kw_base_totales = 0
    kw_intermedio_totales = 0
    kw_punta_totales = 0
    kwh_totales = 0
    kwh_base_totales = 0
    kwh_intermedio_totales = 0
    kwh_punta_totales = 0
    kvarh_totales = 0

    tarifa_kwh_base = 0
    tarifa_kwh_intermedio = 0
    tarifa_kwh_punta = 0

    numero_tarifas = len(tarifas_id)
    ultima_tarifa = tarifas_id[numero_tarifas-1]

    for tarifa_id in tarifas_id:

        tarifasObj = ElectricRatesDetail.objects.get(id = tarifa_id)
        #Obtiene las tarifas del mes
        tarifa_kwh_base += tarifasObj.KWHB
        tarifa_kwh_intermedio += tarifasObj.KWHI
        tarifa_kwh_punta += tarifasObj.KWHP

        #KW
        dict_kw = obtenerKWTarifa(pr_powermeter, tarifa_id, region, 1)

        kw_base_t = dict_kw['base']
        kw_base_totales += kw_base_t
        kw_intermedio_t = dict_kw['intermedio']
        kw_intermedio_totales += kw_intermedio_t
        kw_punta_t = dict_kw['punta']
        kw_punta_totales += kw_punta_t

        kw_totales += kw_base_t + kw_intermedio_t + kw_punta_t

        #Kwh
        dict_kwh = obtenerKWhTarifa(pr_powermeter, tarifa_id, region, 1)
        kwh_base_t = dict_kwh['base']
        kwh_base_totales += kwh_base_t
        kwh_intermedio_t = dict_kwh['intermedio']
        kwh_intermedio_totales += kwh_intermedio_t
        kwh_punta_t = dict_kwh['punta']
        kwh_punta_totales += kwh_punta_t

        #Demanda Facturable
        df_t = demandafacturable_tarifa(kw_base_t, kw_intermedio_t, kw_punta_t, tarifa_id)
        demanda_facturable_total += df_t

        #KVARH
        kvarh_t = obtenerKVARHTarifa(pr_powermeter,tarifa_id)
        kvarh_totales += kvarh_t

        #KWh
        kwh_t = obtenerKWhNetosTarifa(pr_powermeter,tarifa_id)
        kwh_totales += kwh_t

        #Factor de Potencia
        fp = factorpotencia(kwh_t, kvarh_t)
        factor_potencia_total += fp

        #Costo Energía
        c_energia = costoenergia_tarifa(kwh_base_t, kwh_intermedio_t, kwh_punta_t,tarifa_id)
        costo_energia_total += c_energia


        #Costo Demanda Facturable
        c_df_t = costodemandafacturable_tarifa(df_t, tarifa_id)
        costo_demanda_facturable += c_df_t

        #Costo Factor Potencia
        c_factorpotencia = costofactorpotencia(fp, c_energia, c_df_t)
        costo_factor_potencia += c_factorpotencia

        #Subtotal
        c_subtotal = obtenerSubtotal(c_energia, c_df_t, c_factorpotencia)
        subtotal_final += c_subtotal

        #Total
        c_total = obtenerTotal(c_subtotal,16)
        total_final += c_total
        """"
        print "KW Base:", kw_base_t
        print "KW Intermedio:", kw_intermedio_t
        print "KW Punta:", kw_punta_t
        print "KWh Base:", kwh_base_t
        print "KWh Intermedio:", kwh_intermedio_t
        print "KWh Punta:", kwh_punta_t
        print "KWH TOtales", kwh_t
        print "Demanda Facturable:", df_t
        print "KARH", kvarh_t
        print "Factor Potencia:", fp
        print "Costo de Energia:", c_energia
        print "Costo de Demanda Facturable:", c_df_t
        print "Costo de Factor Potencia:", c_factorpotencia
        print "Subtotal", c_subtotal
        print "Iva", obtenerIva(c_subtotal, 16)
        print "Total", c_total

        print "========Termina una tarifa========"
        """


    diccionario_final_cfe = {}
    diccionario_final_cfe['costo_energia'] = costo_energia_total
    diccionario_final_cfe['costo_dfacturable'] = costo_demanda_facturable
    diccionario_final_cfe['costo_fpotencia'] = costo_factor_potencia
    diccionario_final_cfe['subtotal'] = subtotal_final
    diccionario_final_cfe['iva'] = obtenerIva(subtotal_final, 16)
    diccionario_final_cfe['total'] = total_final
    diccionario_final_cfe['kw_base'] = kw_base_totales
    diccionario_final_cfe['kw_intermedio'] = kw_intermedio_totales
    diccionario_final_cfe['kw_punta'] = kw_punta_totales
    diccionario_final_cfe['kwh_totales'] = kwh_totales
    diccionario_final_cfe['kvarh_totales'] = kvarh_totales
    diccionario_final_cfe['kwh_base'] = kwh_base_totales
    diccionario_final_cfe['kwh_intermedio'] = kwh_intermedio_totales
    diccionario_final_cfe['kwh_punta'] = kwh_punta_totales
    diccionario_final_cfe['demanda_facturable'] = demanda_facturable_total
    diccionario_final_cfe['factor_potencia'] = factor_potencia_total/numero_tarifas
    diccionario_final_cfe['tarifa_kwhb'] = tarifa_kwh_base/numero_tarifas
    diccionario_final_cfe['tarifa_kwhi'] = tarifa_kwh_intermedio/numero_tarifas
    diccionario_final_cfe['tarifa_kwhp'] = tarifa_kwh_punta/numero_tarifas
    diccionario_final_cfe['ultima_tarifa'] = ultima_tarifa

    return diccionario_final_cfe





def recibocfe(request):

    #Obtiene los registros de un medidor en un determinado periodo de tiempo
    pr_powermeter = 2
    region = 2
    tipo_tarifa = 1
    start_date = '2012-01-01 00:00:00'
    end_date = '2012-07-31 23:59:59'

    print tarifaHM(pr_powermeter, start_date, end_date, region)
    print "========================================================="
    print "========================================================="
    print tarifaHM__(pr_powermeter, start_date, end_date, region)
    print obtenerHistorico(pr_powermeter,9,region,7, tipo_tarifa)


    variables = RequestContext(request, vars)
    return render_to_response('consumption_centers/cfe.html', variables)