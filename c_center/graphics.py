#coding:utf-8

#
# Python imports
#
import datetime
from datetime import timedelta
import json
import sys

#
# Django imports
#
import django.http
import django.shortcuts
import django.utils.timezone
import django.template.context

#
# cidec imports
#
import data_warehouse.views
import variety


def build_electric_data_json(consumer_units_ids, electric_data, granularity, from_dates, to_dates):


    if not variety.are_array_same_length(consumer_units, from_dates, to_dates):
        return []

    data_arrays = []
    for index in range(0, len(consumer_units_ids)):
        consumer_unit_id = consumer_units_ids[index]
        from_date = from_dates[index]
        from_datetime = datetime.datetime(
                            year=from_date.year,
                            month=from_date.month,
                            day=from_date.day,
                            tzinfo=django.utils.timezone.get_current_timezone())

        to_date = to_dates[index]
        to_datetime = datetime.datetime(
                          year=to_date.year,
                          month=to_date.month,
                          day=to_date.day,
                          tzinfo=django.utils.timezone.get_current_timezone())


        data_array = data_warehouse.views.get_consumer_unit_electric_data(
                         consumer_unit_id,
                         electric_data,
                         granularity,
                         from_datetime,
                         to_datetime)

        if len(data_array) > 0:
            data_arrays.append(data_array)


def cut_electric_data_list_values(electric_data_list, data_values_length):

    for index in range(0, len(electric_data_list)):
        electric_data_list[index] = electric_data_list[index][:data_values_length]

    return True


def get_default_datetime_end():

    return datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=1),
                                     datetime.time(0))


def get_default_datetime_start():

    return get_default_datetime_end() - datetime.timedelta(days=1)


def get_electric_data_list_json(electric_data_list, limits = None):

    domains_number = len(electric_data_list)
    if domains_number < 1:
        return json.dumps([])

    electric_data_max_value = sys.float_info.min
    electric_data_min_value = sys.float_info.max
    rows = []
    rows_number = len(electric_data_list[0])
    for row_index in range(0, rows_number):
        row_data = []
        for domain_index in range(0, domains_number):
            current_datetime = electric_data_list[domain_index][row_index]["datetime"]
            current_electric_data =\
                electric_data_list[domain_index][row_index]["electric_data"]
            row_data.append(dict(datetime=current_datetime,
                                 electric_data=current_electric_data))

            if electric_data_max_value < current_electric_data:
                electric_data_max_value = current_electric_data

            if electric_data_min_value > current_electric_data:
                electric_data_min_value = current_electric_data


        rows.append(row_data)

    if electric_data_max_value < electric_data_min_value:
        electric_data_max_value = 100.0
        electric_data_min_value = -100.0

    if limits is not None:
        limits['max'] = electric_data_max_value
        limits['min'] = electric_data_min_value

    return json.dumps(rows)


def normalize_electric_data_list(electric_data_list):

    if len(electric_data_list) < 1:
        return 0

    minimum_length = len(electric_data_list[0])
    for electric_data_values in electric_data_list:
        current_length = len(electric_data_values)
        minimum_length = min(current_length, minimum_length)
        is_prepare_electric_data_successful = prepare_electric_data(electric_data_values)
        if not is_prepare_electric_data_successful:
            return 0


def prepare_electric_data(electric_data_values):

    electric_data_values_length = len(electric_data_values)
    first_valid_value_index = None
    last_valid_value_index = None
    for index in range(0, electric_data_values_length):
        try:
            if electric_data_values[index]['electric_data'] is not None:
                last_valid_value_index = index
                if first_valid_value_index is None:
                    first_valid_value_index = index

        except  KeyError:
            return False

    if first_valid_value_index is None or last_valid_value_index is None:
        return False

    for index_first in range(0, first_valid_value_index):
        electric_data_values[index_first]['electric_data'] = \
            electric_data_values[first_valid_value_index]['electric_data']

    for index_last in range(last_valid_value_index, electric_data_values_length):
        electric_data_values[index_last]['electric_data'] =\
            electric_data_values[last_valid_value_index]['electric_data']

    index_patch = first_valid_value_index + 1
    while index_patch < last_valid_value_index:
        if electric_data_values[index_patch]['electric_data'] is None:
            lower_index = index_patch - 1
            lower_value = electric_data_values[lower_index]['electric_data']
            while electric_data_values[index_patch]['electric_data'] is None and\
                  index_patch < last_valid_value_index:

                index_patch += 1

            upper_index = index_patch
            upper_value = electric_data_values[upper_index]['electric_data']
            none_count = upper_index - lower_index
            delta_value = (upper_value - lower_value) / float(none_count)
            for i in range(0, none_count):
                electric_data_values[lower_index + i]['electric_data'] =\
                    lower_value + (i * delta_value)

        else:
            index_patch += 1

    return True

def consumed_graph(request):
    electric_data = request.GET['graph']
    granularity = request.GET['granularity']
    if electric_data == "kwh_consumido":
        electric_data = "kWhIMPORT"
    else:
        electric_data = "kvarhIMPORT"


    template_variables = dict()
    data = []
    consumer_unit_counter = 1
    consumer_unit_get_key = "consumer-unit%02d" % consumer_unit_counter
    date_start_get_key = "date-start%02d" % consumer_unit_counter
    date_end_get_key = "date-end%02d" % consumer_unit_counter
    while request.GET.has_key(consumer_unit_get_key):
        consumer_unit_id = request.GET[consumer_unit_get_key]
        if request.GET.has_key(date_start_get_key) and\
           request.GET.has_key(date_end_get_key):

            datetime_start = datetime.datetime.strptime(
                request.GET[date_start_get_key],
                "%Y-%m-%d")

            datetime_end = datetime.datetime.strptime(request.GET[date_end_get_key],
                "%Y-%m-%d")

        else:
            datetime_start = get_default_datetime_start()
            datetime_end = get_default_datetime_end()

        data.append((consumer_unit_id, datetime_start, datetime_end))
        consumer_unit_counter += 1
        consumer_unit_get_key = "consumer-unit%02d" % consumer_unit_counter
        date_start_get_key = "date-start%02d" % consumer_unit_counter
        date_end_get_key = "date-end%02d" % consumer_unit_counter

    electric_data_list = []
    consumer_unit_and_time_interval_information_list = []
    for id, start, end in data:#para cada intervalo
        inicio = start
        fin = end
        delta_days = inicio - fin
        if granularity == "five-minute":
            delta = timedelta(minutes=5)
            number_intervals = delta_days.days * 24 * 12
        elif granularity == "hour":
            delta = timedelta(hours=1)
            number_intervals = delta_days.days * 24
        elif granularity == "day":
            delta = timedelta(hours=1)
            number_intervals = delta_days.days
        else: # granularity == "week":
            delta = timedelta(hours=1)
            number_intervals = delta_days.days / 7

        fin = inicio + delta


        electric_data_values = data_warehouse.views.get_consumer_unit_electric_data(
            electric_data,
            granularity,
            id,
            inicio,
            fin)

        print electric_data_values

        electric_data_list.append(electric_data_values)

        consumer_unit_and_time_interval_information =\
        data_warehouse.views.get_consumer_unit_and_time_interval_information(
            id,
            start,
            end)

        consumer_unit_and_time_interval_information_list.append(
            consumer_unit_and_time_interval_information)


    minimum_values_number = normalize_electric_data_list(electric_data_list)

    is_cut_electric_data_list_successful = cut_electric_data_list_values(
        electric_data_list,
        minimum_values_number)

    limits = dict()
    template_variables['rows_data'] = get_electric_data_list_json(
        electric_data_list,
        limits)

    template_variables['columns'] = consumer_unit_and_time_interval_information_list
    template_variables['limits'] = limits

    template_context = django.template.context.RequestContext(request,
        template_variables)

    return django.shortcuts.render_to_response(
        "consumption_centers/graphs/graphics.html",
        template_context)

def render_graphics(request):

    if request.method == "GET":
        try:
            electric_data = request.GET['graph']
            granularity = request.GET['granularity']
            if electric_data == "TotalkWhIMPORT":
                electric_data = "kWhIMPORT"
            if electric_data == "TotalkvarhIMPORT":
                electric_data = "kvarhIMPORT"
        except KeyError:
            return django.http.HttpResponse("")

        if electric_data == "kwh_consumido" or electric_data == "kvarh_consumido" :
            return consumed_graph(request)
        template_variables = dict()
        data = []
        consumer_unit_counter = 1
        consumer_unit_get_key = "consumer-unit%02d" % consumer_unit_counter
        date_start_get_key = "date-start%02d" % consumer_unit_counter
        date_end_get_key = "date-end%02d" % consumer_unit_counter
        while request.GET.has_key(consumer_unit_get_key):
            consumer_unit_id = request.GET[consumer_unit_get_key]
            if request.GET.has_key(date_start_get_key) and\
               request.GET.has_key(date_end_get_key):

                datetime_start = datetime.datetime.strptime(
                                     request.GET[date_start_get_key],
                                     "%Y-%m-%d")

                datetime_end = datetime.datetime.strptime(request.GET[date_end_get_key],
                                                          "%Y-%m-%d")

            else:
                datetime_start = get_default_datetime_start()
                datetime_end = get_default_datetime_end()

            data.append((consumer_unit_id, datetime_start, datetime_end))
            consumer_unit_counter += 1
            consumer_unit_get_key = "consumer-unit%02d" % consumer_unit_counter
            date_start_get_key = "date-start%02d" % consumer_unit_counter
            date_end_get_key = "date-end%02d" % consumer_unit_counter

        electric_data_list = []
        consumer_unit_and_time_interval_information_list = []
        for id, start, end in data:
            electric_data_values = data_warehouse.views.get_consumer_unit_electric_data(
                                     electric_data,
                                     granularity,
                                     id,
                                     start,
                                     end)


            electric_data_list.append(electric_data_values)

            consumer_unit_and_time_interval_information =\
                data_warehouse.views.get_consumer_unit_and_time_interval_information(
                    id,
                    start,
                    end)

            consumer_unit_and_time_interval_information_list.append(
                consumer_unit_and_time_interval_information)


        minimum_values_number = normalize_electric_data_list(electric_data_list)

        is_cut_electric_data_list_successful = cut_electric_data_list_values(
                                                   electric_data_list,
                                                   minimum_values_number)

        limits = dict()
        template_variables['rows_data'] = get_electric_data_list_json(
                                                       electric_data_list,
                                                       limits)

        template_variables['columns'] = consumer_unit_and_time_interval_information_list
        template_variables['limits'] = limits

        template_context = django.template.context.RequestContext(request,
                                                                  template_variables)

        return django.shortcuts.render_to_response(
                   "consumption_centers/graphs/graphics.html",
                   template_context)

    else:
        raise django.http.Http404


def render_graphics_json(request):

    if request.method == "GET":
        try:
            type = request.GET['electric-data']
            granularity = request.GET['granularity']
            consumer_unit01 = request.GET['consumer-unit01']

        except KeyError:
            raise django.http.HttpResponse(status=500)
            raise django.http.HttpResponse(status=500)

    else:
        raise django.http.Http404
