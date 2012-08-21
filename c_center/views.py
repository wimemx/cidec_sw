#standard library imports
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import re
import time
#related third party imports

#local application/library specific imports
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template.context import RequestContext

from c_center.models import Building, ElectricData, ProfilePowermeter
from rbac.models import Operation, DataContextPermission
from rbac.rbac_functions import  has_permission
from c_center.calculations import tarifaHM
from c_center.models import ConsumerUnit
import json as simplejson


VIEW = Operation.objects.get(operation_name="view")
CREATE = Operation.objects.get(operation_name="create")
DELETE = Operation.objects.get(operation_name="delete")
UPDATE = Operation.objects.get(operation_name="update")

def get_intervals_1(get):
    """ get the interval for the graphs

    by default we get the data from the last 3 months

    """
    f1_init = date.today() - relativedelta( months = +1 )
    f1_end = date.today()

    if "f1_init" in get:
        f1_init = time.strptime(get['f1_init'], "%d/%m/%Y")
        f1_init = date(f1_init.tm_year, f1_init.tm_mon, f1_init.tm_mday)
        f1_end = time.strptime(get['f1_end'], "%d/%m/%Y")
        f1_end = date(f1_end.tm_year, f1_end.tm_mon, f1_end.tm_mday)

    return f1_init,f1_end

def get_intervals_2(get):
    """ gets the second date interval """
    f2_init = time.strptime(get['f2_init'], "%d/%m/%Y")
    f2_init = date(f2_init.tm_year, f2_init.tm_mon, f2_init.tm_mday)
    f2_end = time.strptime(get['f2_end'], "%d/%m/%Y")
    f2_end = date(f2_end.tm_year, f2_end.tm_mon, f2_end.tm_mday)

    return f2_init, f2_end

def main_page(request):
    """ in the mean time the main view is the graphics view """
    if has_permission(request.user, VIEW, "graphs") or request.user.is_superuser:
        #has perm to view graphs, now check what can the user see
        datacontext = DataContextPermission.objects.filter(user_role__user=request.user)

        if 'main_building' not in request.session:
            #sets the default building
            request.session['main_building'] = datacontext[0].building
        template_vars = {"type":"graphs", "datacontext":datacontext,'empresa':request.session['main_building']}
        template_vars_template = RequestContext(request, template_vars)
        return render_to_response("consumption_centers/main.html", template_vars_template)
    else:
        return render_to_response("generic_error.html", RequestContext(request))

def cfe_bill(request):
    if has_permission(request.user, VIEW, "CFE bill") or request.user.is_superuser:
        datacontext = DataContextPermission.objects.filter(user_role__user=request.user)
        if not request.session['main_building']:
            #sets the default building
            request.session['main_building'] = datacontext[0].building
        powermeter = ConsumerUnit.objects.get(building=datacontext[0].building)

        start_date, end_date = get_intervals_1(request.GET)
        t_hm=tarifaHM(powermeter.profile_powermeter,
            start_date, end_date, datacontext[0].building.region)
        template_vars={"type":"cfe", "datacontext":datacontext,
                       'empresa':request.session['main_building'],
                       'tarifaHM': t_hm}
        template_vars_template = RequestContext(request, template_vars)
        return render_to_response("consumption_centers/cfe.html", template_vars_template)
    else:
        return render_to_response("generic_error.html", RequestContext(request))

def potencia_activa(request):
    template_vars = {"type":"kw"}

    #second interval, None by default
    f2_init = None
    f2_end = None

    f1_init, f1_end = get_intervals_1(request.GET)

    if request.GET:

        if "f2_init" in request.GET:
            f2_init, f2_end = get_intervals_2(request.GET)
        for key in request.GET:
            if re.search('^compare_to\d+', key):
                # "compare", request.session['main_building'], "with building", key
                building_compare = Building.objects.get(pk=int(key))
                template_vars['compare_interval_kw'] = get_KW(building_compare, f1_init, f1_end)
                if f2_init:
                    template_vars['compare_interval2_kw'] = get_KW(building_compare, f2_init, f2_end)
    template_vars['building']=request.session['main_building'].pk
    template_vars['fi'], template_vars['ff'] = f1_init, f1_end
    #template_vars['main_interval_kw'], \
    #template_vars['fi'], \
    #template_vars['ff'] = get_KW(request.session['main_building'], f1_init, f1_end)

    if f2_init:
        template_vars['main_interval2_kw'] = get_KW(request.session['main_building'], f2_init, f2_end)

    template_vars_template = RequestContext(request, template_vars)
    return render_to_response("consumption_centers/graphs/potencia_activa.html", template_vars_template)

def get_kw_data(request):
    if 'building' in request.GET:
        building = get_object_or_404(Building, pk=int(request.GET['building']))
        f1_init, f1_end = get_intervals_1(request.GET)
        data=get_KW_json(building, f1_init, f1_end)
        return HttpResponse(content=data,content_type="application/json")
    else:
        raise Http404


def get_kvar_data(request):
    if 'building' in request.GET:
        building = get_object_or_404(Building, pk=int(request.GET['building']))
        f1_init, f1_end = get_intervals_1(request.GET)
        data=get_KVar_json(request.session['main_building'], f1_init, f1_end)
        return HttpResponse(content=data,content_type="application/json")
    else:
        raise Http404

def get_pf_data(request):
    if 'building' in request.GET:
        building = get_object_or_404(Building, pk=int(request.GET['building']))
        f1_init, f1_end = get_intervals_1(request.GET)
        data=get_PF_json(request.session['main_building'], f1_init, f1_end)
        return HttpResponse(content=data,content_type="application/json")
    else:
        raise Http404

def get_pp_data(request):
    if 'building' in request.GET:
        building = get_object_or_404(Building, pk=int(request.GET['building']))
        f1_init, f1_end = get_intervals_1(request.GET)
        data=get_power_profile_json(request.session['main_building'], f1_init, f1_end)
        return HttpResponse(content=data,content_type="application/json")
    else:
        raise Http404


def potencia_reactiva(request):
    template_vars = {"type":"kvar"}
    #second interval, None by default
    f2_init = None
    f2_end = None

    f1_init, f1_end = get_intervals_1(request.GET)

    if request.GET:

        if "f2_init" in request.GET:
            f2_init, f2_end = get_intervals_2(request.GET)

        for key in request.GET:
            if re.search('^compare_to\d+', key):
                # "compare", request.session['main_building'], "with building", key
                building_compare = Building.objects.get(pk=int(key))
                template_vars['compare_interval_kw'] = get_KW(building_compare, f1_init, f1_end)
                if f2_init:
                    template_vars['compare_interval2_kw'] = get_KW(building_compare, f2_init, f2_end)
    template_vars['building']=request.session['main_building'].pk
    template_vars['fi'], template_vars['ff'] = f1_init, f1_end
    #template_vars['main_interval_kw'], \
    #template_vars['fi'], \
    #template_vars['ff'] = get_KW(request.session['main_building'], f1_init, f1_end)

    if f2_init:
        template_vars['main_interval2_kw'] = get_KW(request.session['main_building'], f2_init, f2_end)

    template_vars_template = RequestContext(request, template_vars)
    return render_to_response("consumption_centers/graphs/potencia_reactiva.html", template_vars_template)

def factor_potencia(request):
    template_vars = {"type":"pf"}
    #second interval, None by default
    f2_init = None
    f2_end = None

    f1_init, f1_end = get_intervals_1(request.GET)

    if request.GET:

        if "f2_init" in request.GET:
            f2_init, f2_end = get_intervals_2(request.GET)
        for key in request.GET:
            if re.search('^compare_to\d+', key):
                # "compare", request.session['main_building'], "with building", key
                building_compare = Building.objects.get(pk=int(key))
                template_vars['compare_interval_kw'] = get_KW(building_compare, f1_init, f1_end)
                if f2_init:
                    template_vars['compare_interval2_kw'] = get_KW(building_compare, f2_init, f2_end)
    template_vars['building']=request.session['main_building'].pk
    template_vars['fi'], template_vars['ff'] = f1_init, f1_end
    #template_vars['main_interval_kw'], \
    #template_vars['fi'], \
    #template_vars['ff'] = get_KW(request.session['main_building'], f1_init, f1_end)

    if f2_init:
        template_vars['main_interval2_kw'] = get_KW(request.session['main_building'], f2_init, f2_end)

    template_vars_template = RequestContext(request, template_vars)
    return render_to_response("consumption_centers/graphs/factor_potencia.html", template_vars_template)

def perfil_carga(request):
    template_vars = {"type":"profile"}
    #second interval, None by default
    f2_init = None
    f2_end = None

    f1_init, f1_end = get_intervals_1(request.GET)

    if request.GET:

        if "f2_init" in request.GET:
            f2_init, f2_end = get_intervals_2(request.GET)
        for key in request.GET:
            if re.search('^compare_to\d+', key):
                # "compare", request.session['main_building'], "with building", key
                building_compare = Building.objects.get(pk=int(key))
                template_vars['compare_interval_pf'] = get_PF(building_compare, f1_init, f1_end)
                template_vars['compare_interval_kvar'] = get_KVar(building_compare, f1_init, f1_end)
                template_vars['compare_interval_kw'] = get_KW(building_compare, f1_init, f1_end)
                if f2_init:
                    template_vars['compare_interval2_pf'] = get_PF(building_compare, f2_init, f2_end)
                    template_vars['compare_interval2_kvar'] = get_KVar(building_compare, f2_init, f2_end)
                    template_vars['compare_interval2_kw'] = get_KW(building_compare, f2_init, f2_end)
    template_vars['building']=request.session['main_building'].pk
    template_vars['fi'], template_vars['ff'] = f1_init, f1_end
    #template_vars['main_interval_kw'], \
    #template_vars['fi'], \
    #template_vars['ff'] = get_KW(request.session['main_building'], f1_init, f1_end)

    if f2_init:
        template_vars['main_interval2_pf'] = get_PF(request.session['main_building'], f2_init, f2_end)
        template_vars['main_interval_kvar_kw2'] = get_power_profile(request.session['main_building'], f2_init, f2_end)

    template_vars_template = RequestContext(request, template_vars)
    return render_to_response("consumption_centers/graphs/perfil_carga.html", template_vars_template)

def set_default_building(request, id_building):
    request.session['main_building'] = Building.objects.get(pk=id_building)
    if 'referer' in request.GET:
        if request.GET['referer'] == "cfe":
            return HttpResponseRedirect("/reportes/cfe/")
    return HttpResponse(status=200)

def recibocfe(request):

    #Obtiene los registros de un medidor en un determinado periodo de tiempo
    start_date, end_date = get_intervals_1(request.GET)
    consumer_unit = ConsumerUnit.objects.get(building=request.session['main_building'])
    pr_powermeter = ProfilePowermeter.objects.get(pk=consumer_unit.profile_powermeter.pk)
    region = request.session['main_building'].region

    vars=dict(tarifa=tarifaHM(pr_powermeter, start_date, end_date, region))

    variables = RequestContext(request, vars)
    return render_to_response('consumption_centers/cfe.html', variables)

def get_medition_in_time(building, datetime_from, datetime_to):
    """ Gets the meditions registered in a time window

    building = Building model instance
    datetime_from = lower date limit
    datetime_to = upper date limit

    Right now we are assuming that there is only a powermeter(and one consumer unit) per building

    """
    consumer_unit = ConsumerUnit.objects.get(building=building)
    profile_powermeter = ProfilePowermeter.objects.get(pk=consumer_unit.profile_powermeter.pk)
    meditions = ElectricData.objects.filter(profile_powermeter=profile_powermeter,
        medition_date__gte=datetime_from,medition_date__lte=datetime_to+timedelta(days=1)).order_by("medition_date")
    print "medition lenght", len(meditions)
    return meditions

def get_KW(building, datetime_from, datetime_to):
    """ Gets the KW data in a given interval"""
    meditions = get_medition_in_time(building, datetime_from, datetime_to)
    kw=[]
    fi = None
    for medition in meditions:
        if not fi:
            fi=medition.medition_date
        kw.append(dict(kw=medition.kW, date=medition.medition_date))
    ff = meditions[len(meditions)-1].medition_date
    return kw, fi, ff

def get_KW_json(building, datetime_from, datetime_to):
    """ Gets the KW data in a given interval"""
    meditions = get_medition_in_time(building, datetime_from, datetime_to)
    kw=[]
    for medition in meditions:
        kw.append(dict(kw=str(medition.kW), date=int(time.mktime(medition.medition_date.timetuple()))))

    return simplejson.dumps(kw)

def get_KVar(building, datetime_from, datetime_to):
    """ Gets the KW data in a given interval"""
    meditions = get_medition_in_time(building, datetime_from, datetime_to)
    kvar=[]
    for medition in meditions:
        kvar.append(dict(kvar=medition.kvar, date=medition.medition_date))

    return kvar

def get_KVar_json(building, datetime_from, datetime_to):
    """ Gets the KVar data in a given interval"""
    meditions = get_medition_in_time(building, datetime_from, datetime_to)
    kvar=[]
    for medition in meditions:
        kvar.append(dict(kvar=str(medition.kvar), date=int(time.mktime(medition.medition_date.timetuple()))))

    return simplejson.dumps(kvar)


def get_PF(building, datetime_from, datetime_to):
    """ Gets the KW data in a given interval"""
    meditions = get_medition_in_time(building, datetime_from, datetime_to)
    pf=[]
    for medition in meditions:
        pf.append(dict(pf=medition.PF, date=medition.medition_date))
    return pf

def get_PF_json(building, datetime_from, datetime_to):
    """ Gets the PF data in a given interval"""
    meditions = get_medition_in_time(building, datetime_from, datetime_to)
    pf=[]
    for medition in meditions:
        pf.append(dict(pf=str(medition.PF), date=int(time.mktime(medition.medition_date.timetuple()))))

    return simplejson.dumps(pf)


def get_power_profile(building, datetime_from, datetime_to):
    """ gets the data from the active and reactive energy for a building in a time window"""
    meditions = get_medition_in_time(building, datetime_from, datetime_to)
    kvar=[]
    kw=[]
    for medition in meditions:
        kw.append(dict(kw=medition.kW, date=medition.medition_date))
        kvar.append(dict(kvar=medition.kvar, date=medition.medition_date))
    return zip(kvar,kw)


def get_power_profile_json(building, datetime_from, datetime_to):
    """ gets the data from the active and reactive energy for a building in a time window"""
    meditions = get_medition_in_time(building, datetime_from, datetime_to)
    #kvar=[]
    kw=[]
    for medition in meditions:
        kw.append(dict(kw=str(medition.kW), kvar=str(medition.kvar), date=int(time.mktime(medition.medition_date.timetuple()))))
        #kvar.append(dict(kvar=str(medition.kvar), date=int(time.mktime(medition.medition_date.timetuple()))))
    return simplejson.dumps(kw)


