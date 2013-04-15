#coding:utf-8

# Python imports
import datetime
import logging
import numpy
import time
import sys

# Django imports
import django.http
import django.shortcuts
import django.utils.timezone
import django.template.context

# Alarms imports
import alarms.models

# Reports imports
import reports.globals

# Data Warehouse Extended imports
import data_warehouse_extended.models
import data_warehouse_extended.views

# CCenter imports
import c_center.models
import c_center.c_center_functions
import c_center.graphics

# Other imports
import variety

logger = logging.getLogger("reports")

################################################################################
#
# Utility Scripts
#
################################################################################

def get_axis_dictionary (
        data_clusters_list_normalized,
        column_units_list
):

    data_clusters_list_length = len(data_clusters_list_normalized)
    column_units_list_length = len(column_units_list)
    if data_clusters_list_length != column_units_list_length:
        return None

    axis_dictionary = dict()
    for data_cluster_index in range(0, data_clusters_list_length):
        column_units = column_units_list[data_cluster_index]
        data_cluster = data_clusters_list_normalized[data_cluster_index]
        data_cluster_values_list =\
            [float(data_dictionary['value']) for data_dictionary in data_cluster]

        data_cluster_max_value = max(data_cluster_values_list)
        data_cluster_min_value = min(data_cluster_values_list)
        if axis_dictionary.has_key(column_units):
            axis_dictionary_value = axis_dictionary[column_units]
            axis_max_value = axis_dictionary_value['max']
            axis_dictionary_value['max'] = \
                max(axis_max_value, data_cluster_max_value)

            axis_min_value = axis_dictionary_value['min']
            axis_dictionary_value['min'] = \
                min(axis_min_value, data_cluster_min_value)

            axis_dictionary[column_units] = axis_dictionary_value

        else:
            axis_dictionary[column_units] = {
                'name': column_units,
                'max': data_cluster_max_value,
                'min': data_cluster_min_value
            }

    return axis_dictionary


def get_axis_dictionaries_list (
        axis_dictionary
):

    axis_dictionaries_list = []
    for _, value in axis_dictionary.items():
        axis_dictionaries_list.append(value)

    return axis_dictionaries_list


def get_column_strings_electrical_parameter(
        request_data_list_normalized,
):
    """
        Description:


        Arguments:


        Return:

    """

    column_strings_list = []
    for _, _, _, electrical_parameter_name\
        in request_data_list_normalized:

        column_strings_list.append(electrical_parameter_name)

    return column_strings_list


def get_column_units_axis_indexes(
        column_units_list,
        axis_dictionaries_list
):

    column_units_axis_indexes = []
    for column_unit in column_units_list:
        for axis_dictionary_index in range(0, len(axis_dictionaries_list)):
            axis_dictionary = axis_dictionaries_list[axis_dictionary_index]
            if column_unit == axis_dictionary['name']:
                column_units_axis_indexes.append(axis_dictionary_index)

    if len(column_units_axis_indexes) != len(column_units_list):
        return None

    return column_units_axis_indexes


def get_column_units_list(
        request_data_list_normalized
):
    column_units_list = []
    for _, _, _, electrical_parameter_name\
        in request_data_list_normalized:

        try:
            nm = data_warehouse_extended.models.ElectricalParameter.objects.get(
                name=electrical_parameter_name
            )
            nm = nm.name_transactional
            electrical_parameter_info =\
                alarms.models.ElectricParameters.objects.get(
                    name=nm)

        except alarms.models.ElectricParameters.DoesNotExist:
            logger.error()
            return None

        column_units_list.append(electrical_parameter_info.param_units)

    return column_units_list


def get_data_cluster_consumed_normalized (
        consumer_unit_id,
        datetime_from,
        datetime_to,
        electrical_parameter_name,
        granularity_seconds
):
    #
    # Localize datetimes (if neccesary) and convert to UTC
    #
    timezone_current = django.utils.timezone.get_current_timezone()
    datetime_from_local = datetime_from
    if datetime_from_local.tzinfo is None:
        datetime_from_local = timezone_current.localize(datetime_from)

    datetime_from_utc =\
        datetime_from_local.astimezone(django.utils.timezone.utc)

    datetime_to_local = datetime_to
    if datetime_to_local.tzinfo is None:
        datetime_to_local = timezone_current.localize(datetime_to)

    datetime_to_utc = datetime_to_local.astimezone(django.utils.timezone.utc)

    #
    # Get the Electrical Parameter
    #
    electrical_parameter =\
        data_warehouse_extended.views.get_electrical_parameter(
            electrical_parameter_name=electrical_parameter_name)

    if electrical_parameter is None:
        logger.error(
            reports.globals.SystemError.GET_DATA_CLUSTER_CONSUMED_JSON_ERROR)

        return None

    if electrical_parameter.type !=\
        data_warehouse_extended.models.ElectricalParameter.CUMULATIVE:

        logger.error(
            reports.globals.SystemError.GET_DATA_CLUSTER_CONSUMED_JSON_ERROR)

        return None

    try:
        consumer_unit =\
            c_center.models.ConsumerUnit.objects.get(pk=consumer_unit_id)

    except c_center.models.ConsumerUnit.DoesNotExist:
        logger.error(
            reports.globals.SystemError.GET_DATA_CLUSTER_CONSUMED_JSON_ERROR)

        return None

    #
    # Get the data cluster.
    #
    data_cluster =\
        get_consumer_unit_electrical_parameter_data_clustered(
            consumer_unit,
            datetime_from_utc,
            datetime_to_utc,
            electrical_parameter_name,
            granularity_seconds)

    normalize_data_cluster(data_cluster)

    #
    # Build the json.
    #
    data_cluster_json = []
    for data_index in range(0, len(data_cluster) - 1):
        data_dictionary_current = data_cluster[data_index]
        data_dictionary_next = data_cluster[data_index + 1]
        datetime_current = data_dictionary_current['datetime']
        value_current =\
            data_dictionary_next['value'] - \
            data_dictionary_current['value']

        certainty_current = \
            data_dictionary_current['certainty'] and \
            data_dictionary_next['certainty']

        data_dictionary_json = {
            'datetime': datetime_current,
            'value': float(value_current),
            'certainty': certainty_current
        }

        data_cluster_json.append(data_dictionary_json)

    return data_cluster_json


def get_data_cluster_limits (
        data_cluster_normalized
):

    maximum = sys.float_info.min
    minimum = sys.float_info.max
    for data_dictionary in data_cluster_normalized:
        data_dictionary_value = float(data_dictionary['value'])
        maximum = max(data_dictionary_value, maximum)
        minimum = min(data_dictionary_value, minimum)

    return maximum, minimum


def get_data_clusters_json(
        data_clusters_list_normalized
):
    """
        Description:


        Arguments:
            data_clusters_list_normalized -

        Return:

    """

    data_clusters_length = len(data_clusters_list_normalized)
    if data_clusters_length < 1:
        return None

    data_cluster_instants_number = len(data_clusters_list_normalized[0])
    if data_cluster_instants_number < 1:
        return None

    data_clusters_json = []
    for instant_index in range(0, data_cluster_instants_number):
        instant_json = []
        for data_cluster_index in range(0, data_clusters_length):
            data_cluster_dictionary =\
                data_clusters_list_normalized[data_cluster_index][instant_index]

            data_cluster_dictionary_copy = data_cluster_dictionary.copy()
            float_data_value = float(data_cluster_dictionary['value'])
            data_cluster_dictionary_copy['value'] = float_data_value
            instant_json.append(data_cluster_dictionary_copy)

        data_clusters_json.append(instant_json)

    return data_clusters_json


def get_data_clusters_list(
        request_data_list_normalized,
        granularity
):
    """
        Description:


        Arguments:
            request_data_list_normalized -
            granularity
        Return:

    """

    data_clusters_list = []
    for consumer_unit_id, datetime_from, datetime_to, electrical_parameter_name\
        in request_data_list_normalized:

        try:
            consumer_unit =\
                c_center.models.ConsumerUnit.objects.get(pk=consumer_unit_id)

        except c_center.models.ConsumerUnit.DoesNotExist:
            logger.error(
                reports.globals.SystemError.GET_DATA_CLUSTERS_LIST_ERROR)

            return None
        if granularity == "raw":
            data_cluster = c_center.graphics.get_consumer_unit_electric_data_raw(
                electrical_parameter_name,
                consumer_unit_id,
                datetime_from,
                datetime_to
            )
        else:
            data_cluster =\
                get_consumer_unit_electrical_parameter_data_clustered(
                    consumer_unit,
                    datetime_from,
                    datetime_to,
                    electrical_parameter_name)

        if data_cluster is None:
            logger.error(
                reports.globals.SystemError.GET_DATA_CLUSTERS_LIST_ERROR)

            return None

        data_clusters_list.append(data_cluster)

    return data_clusters_list


def get_data_clusters_list_limits(
        data_clusters_list_normalized
):
    """
        Description:


        Arguments:
            data_clusters_list_normalized -

        Return:

    """
    maximum = sys.float_info.min
    minimum = sys.float_info.max
    for data_cluster in data_clusters_list_normalized:
        for data_dictionary in data_cluster:
            data_dictionary_value = float(data_dictionary['value'])
            maximum = max(data_dictionary_value, maximum)
            minimum = min(data_dictionary_value, minimum)

    return maximum, minimum


def get_instant_delta_from_timedelta(
        timedelta
):
    """
        Description:
            To-Do

        Arguments:
            timedelta -

        Return:

    """

    timedelta_seconds = timedelta.seconds + (timedelta.days * 24 * 3600)
    instant_deltas = data_warehouse_extended.views.get_instant_delta_all()
    if len(instant_deltas) < 1:
        logger.error(
            reports.globals.SystemError.GET_INSTANT_DELTA_FROM_TIMEDELTA_ERROR)

        return None

    #
    # Get the Instant Deltas which the number of points it'll generate is the
    # closest to the ideal number of points, to the maximum number of points and
    # to the minimum number of points.
    #
    ideal_closest_instant_delta = instant_deltas[0]
    ideal_closest_points =\
        abs(reports.globals.Constant.POINTS_IN_GRAPHICS_IDEAL -
            (timedelta_seconds / ideal_closest_instant_delta.delta_seconds))

    max_closest_instant_delta = instant_deltas[0]
    max_closest_points =\
        abs(reports.globals.Constant.POINTS_IN_GRAPHICS_MAX -
            (timedelta_seconds / max_closest_instant_delta.delta_seconds))

    min_closest_instant_delta = instant_deltas[0]
    min_closest_points =\
        abs(reports.globals.Constant.POINTS_IN_GRAPHICS_MIN -
            (timedelta_seconds / min_closest_instant_delta.delta_seconds))

    for instant_delta in instant_deltas:
        instant_delta_points_count =\
            timedelta_seconds / instant_delta.delta_seconds

        distance_to_ideal =\
            abs(reports.globals.Constant.POINTS_IN_GRAPHICS_IDEAL -
                instant_delta_points_count)

        if distance_to_ideal < ideal_closest_points:
            ideal_closest_instant_delta = instant_delta
            ideal_closest_points = distance_to_ideal

        distance_to_max =\
            abs(reports.globals.Constant.POINTS_IN_GRAPHICS_MAX -
                instant_delta_points_count)

        if distance_to_max < max_closest_points:
            max_closest_instant_delta = instant_delta
            max_closest_points = distance_to_max

        distance_to_min =\
            abs(reports.globals.Constant.POINTS_IN_GRAPHICS_MIN -
                instant_delta_points_count)

        if distance_to_min < min_closest_points:
            min_closest_instant_delta = instant_delta
            min_closest_points = distance_to_min

    is_instant_delta_lesser_than_max =\
        (reports.globals.Constant.POINTS_IN_GRAPHICS_IDEAL + ideal_closest_points) <\
        reports.globals.Constant.POINTS_IN_GRAPHICS_MAX

    is_instant_delta_greater_than_min =\
        (reports.globals.Constant.POINTS_IN_GRAPHICS_IDEAL - ideal_closest_points) >\
        reports.globals.Constant.POINTS_IN_GRAPHICS_MIN

    #
    # If the Instant Delta that generates the number of points closest to the
    # ideal number of points generates a number of points between the maximum
    # and the minimum number of points, return the Instant Delta
    #
    if is_instant_delta_greater_than_min and is_instant_delta_lesser_than_max:
        return ideal_closest_instant_delta

    #
    # Otherwise, return the Instant Delta which generates the number of points
    # closest to the minimum number of points or the maximum number of points.
    #
    else:
        if max_closest_points < min_closest_points:
            return max_closest_instant_delta

        return min_closest_instant_delta


def get_request_data_list_normalized(
        request_data_list
):
    """
        Description:
            To-Do

        Arguments:
            request_data_list

        Return:

    """

    #
    # Get the minimum time delta.
    #
    minimum_time_delta = datetime.timedelta.max
    for consumer_unit_id, datetime_from, datetime_to, electrical_parameter_name\
        in request_data_list:

        current_time_delta = datetime_to - datetime_from
        if current_time_delta < datetime.timedelta(0):
            logger.error(
                reports.globals.SystemError.GET_NORMALIZED_REQUEST_DATA_LIST_ERROR)

            return None

        if current_time_delta < minimum_time_delta:
            minimum_time_delta = current_time_delta

    #
    # Set all the time deltas to the minimun time delta.
    #
    request_data_list_normalized = []
    for consumer_unit_id, datetime_from, datetime_to, electrical_parameter_name\
        in request_data_list:

        request_data_list_item_normalized =\
            (consumer_unit_id,
             datetime_from,
             datetime_from + minimum_time_delta,
             electrical_parameter_name)

        request_data_list_normalized.append(
            request_data_list_item_normalized)

    return request_data_list_normalized


def get_data_clusters_statistics(
        data_clusters_list_normalized
):
    """
        Description:


        Arguments:
            data_clusters_list_normalized -

        Return:

    """
    data_clusters_statistics = []
    for data_cluster in data_clusters_list_normalized:

        data_cluster_values_list = []
        for data_dictionary in data_cluster:
            data_cluster_values_list.append(float(data_dictionary['value']))

        data_cluster_values_array = numpy.array(data_cluster_values_list)
        data_cluster_values_array.sort()
        data_cluster_mean = data_cluster_values_array.mean()
        data_cluster_maximum = data_cluster_values_array.max()
        data_cluster_minimum = data_cluster_values_array.min()
        data_cluster_median = numpy.median(data_cluster_values_array)
        data_cluster_standard_deviation = data_cluster_values_array.std()

        data_clusters_statistics.append({
            "mean" : data_cluster_mean,
            "maximum" : data_cluster_maximum,
            "minimum" : data_cluster_minimum,
            "median": data_cluster_median,
            "standard_deviation" : data_cluster_standard_deviation
        })

    return  data_clusters_statistics


def get_timedelta_from_normalized_request_data_list(
        request_data_list_normalized
):
    """
        Description:
            To-Do

        Arguments:
            request_data_list

        Return:

    """
    if not len(request_data_list_normalized) > 0:
        logger.error(
            reports.globals.SystemError.
            GET_TIMEDELTA_FROM_NORMALIZED_REQUEST_DATA_LIST_ERROR)

        return None

    consumer_unit_id, datetime_from, datetime_to, electrical_parameter_name =\
        request_data_list_normalized[0]

    return datetime_to - datetime_from


def normalize_data_cluster(
        data_cluster
):
    """
        Description:


        Arguments:
            data_cluster -

        Return:

    """

    #
    # Get the first and last valid indexes
    #
    valid_index_first = None
    valid_index_last = None
    index_counter = 0
    for data_dictionary in data_cluster:
        data_dictionary_value =\
            data_dictionary['value']

        if data_dictionary_value is not None:
            if valid_index_first is None:
                valid_index_first = index_counter

            valid_index_last = index_counter

        index_counter += 1

    #
    # If any value is valid, set all the values to 0 and set a false certainty
    # for all of them.
    #
    if valid_index_first is None or valid_index_last is None:
        for data_dictionary in data_cluster:
            data_dictionary['value'] = 0
            data_dictionary['certainty'] = False

        return

    #
    # Fill the cluster with uncertain data until the first valid index is
    # reached.
    #
    if valid_index_first is not None:
        data_dictionary_valid_first = data_cluster[valid_index_first]
        data_dictionary_valid_first_value = data_dictionary_valid_first['value']

        for index in range(0, valid_index_first):
            data_dictionary_current = data_cluster[index]
            data_dictionary_current['value'] = data_dictionary_valid_first_value
            data_dictionary_current['certainty'] = False

    #
    # Fill the cluster with uncertain data from the last valid index until the
    # end is reached.
    #
    if valid_index_last is not None:
        data_dictionary_valid_last = data_cluster[valid_index_last]
        data_dictionary_valid_last_value = data_dictionary_valid_last['value']

        for index in range(valid_index_last, len(data_cluster)):
            data_dictionary_current = data_cluster[index]
            data_dictionary_current['value'] = data_dictionary_valid_last_value
            data_dictionary_current['certainty'] = False

    #
    # Patch all the invalid data using a linear interpolation and set certainty
    # as false for the patched data.
    #
    dictionary_index = valid_index_first + 1
    while dictionary_index < valid_index_last:
        data_dictionary_current = data_cluster[dictionary_index]
        data_dictionary_current_value = data_dictionary_current['value']

        if data_dictionary_current_value is None:
            #
            # Find the range that has invalid values
            #
            invalid_index = dictionary_index
            invalid_dictionary = data_cluster[invalid_index]
            invalid_dictionary_value = invalid_dictionary['value']
            while invalid_dictionary_value is None and invalid_index < valid_index_last:
                invalid_index += 1
                invalid_dictionary = data_cluster[invalid_index]
                invalid_dictionary_value = invalid_dictionary['value']

            #
            # Get the delta that will be used to patch the data.
            #
            valid_index_lower = dictionary_index - 1
            valid_dictionary_lower = data_cluster[valid_index_lower]
            valid_dictionary_lower_value = valid_dictionary_lower['value']

            valid_index_upper = invalid_index
            valid_dictionary_upper = data_cluster[valid_index_upper]
            valid_dictionary_upper_value = valid_dictionary_upper['value']

            value_difference =\
                valid_dictionary_upper_value - valid_dictionary_lower_value

            indexes_difference = valid_index_upper - valid_index_lower
            patch_delta = value_difference / indexes_difference

            #
            # Patch the data
            #
            for patch_index in range(1, indexes_difference):
                patch_dictionary = data_cluster[valid_index_lower + patch_index]
                patch_dictionary['value'] =\
                    valid_dictionary_lower_value + (patch_index * patch_delta)

        dictionary_index += 1

    return


def normalize_data_clusters_list(
        data_clusters_list
):
    """
        Description:


        Arguments:
            data_clusters_list -

        Return:

    """

    for data_cluster in data_clusters_list:
        normalize_data_cluster(data_cluster)

    return

################################################################################
#
# Data Retrieve Scripts
#
################################################################################

def get_consumer_unit_electrical_parameter_data_clustered(
        consumer_unit,
        datetime_from,
        datetime_to,
        electrical_parameter_name,
        granularity_seconds=None
):
    """
        Description:
            To-Do

        Arguments:
            consumer_unit - A Consumer Unit object.

            datetime_from - A Datetime object.

            datetime_to - A Datetime object.

            electrical_parameter - A String that represents the name of the
                electrical parameter.

            granularity_seconds - An Integer that represents the number of
                seconds between the points to be retrieved.

        Return:
            A list of dictionaries.
    """

    #
    # Localize datetimes (if neccesary) and convert to UTC
    #
    timezone_current = django.utils.timezone.get_current_timezone()
    datetime_from_local = datetime_from
    if datetime_from_local.tzinfo is None:
        datetime_from_local = timezone_current.localize(datetime_from)

    datetime_from_utc =\
        datetime_from_local.astimezone(django.utils.timezone.utc)

    datetime_to_local = datetime_to
    if datetime_to_local.tzinfo is None:
        datetime_to_local = timezone_current.localize(datetime_to)

    datetime_to_utc = datetime_to_local.astimezone(django.utils.timezone.utc)

    #
    # Get the Electrical Parameter
    #
    electrical_parameter =\
        data_warehouse_extended.views.get_electrical_parameter(
            electrical_parameter_name=electrical_parameter_name)

    if electrical_parameter is None:
        logger.error(
            reports.globals.SystemError.
            GET_CONSUMER_UNIT_ELECTRICAL_PARAMETER_DATA_CLUSTERED_ERROR)

        return None

    #
    # Get the Instants between the from and to datetime according to the Instant
    # Delta and create a dictionary with them.
    #
    if granularity_seconds is None:
        instant_delta =\
            get_instant_delta_from_timedelta(datetime_to - datetime_from)

    else:
        instant_delta =\
            data_warehouse_extended.views.get_instant_delta(
                delta_seconds=granularity_seconds)


    if instant_delta is None:
        logger.error(
            reports.globals.SystemError.
            GET_CONSUMER_UNIT_ELECTRICAL_PARAMETER_DATA_CLUSTERED_ERROR)

        return None

    instants =\
        data_warehouse_extended.views.get_instants_list(
            datetime_from_utc,
            datetime_to_utc,
            instant_delta)

    instants_dictionary = dict()
    instant_dictionary_generic_value = {
        'certainty' : True,
        'value' :None
    }

    for instant in instants:
        key_current = instant.instant_datetime.strftime(
            reports.globals.Constant.DATETIME_STRING_KEY_FORMAT)

        instants_dictionary[key_current] =\
            instant_dictionary_generic_value.copy()

    #
    # Get the dependent Consumer Units List and retrieve their data.
    #
    consumer_units_list =\
        c_center.c_center_functions.get_consumer_units(consumer_unit)

    for consumer_unit_item in consumer_units_list:
        #
        # Get a Consumer Unit Profile (from the app Data Warehouse Extended)
        #
        consumer_unit_profile =\
            data_warehouse_extended.views.get_consumer_unit_profile(
                consumer_unit_item.pk)

        if consumer_unit_profile is None:
            logger.error(
                reports.globals.SystemError.
                GET_CONSUMER_UNIT_ELECTRICAL_PARAMETER_DATA_CLUSTERED_ERROR)

            return None

        consumer_unit_data_list =\
            data_warehouse_extended.views.\
                get_consumer_unit_electrical_parameter_data_list(
                    consumer_unit_profile,
                    datetime_from_utc,
                    datetime_to_utc,
                    electrical_parameter,
                    instant_delta)

        #
        # Update the information in the Instants dictionary
        #
        for consumer_unit_data in consumer_unit_data_list:
            instant_key_current =\
                consumer_unit_data.instant.instant_datetime.strftime(
                    reports.globals.Constant.DATETIME_STRING_KEY_FORMAT)

            try:
                instant_dictionary_current =\
                    instants_dictionary[instant_key_current]

            except KeyError:
                instant_dictionary_current = instant_dictionary_generic_value

            certainty_current = instant_dictionary_current['certainty']
            certainty_current =\
                certainty_current and consumer_unit_data.value is not None

            instant_dictionary_current['certainty'] = certainty_current

            if certainty_current:
                value_current = instant_dictionary_current['value']
                if value_current is None:
                    value_current = consumer_unit_data.value

                else:
                    value_current += consumer_unit_data.value

                instant_dictionary_current['value'] = value_current

            instants_dictionary[instant_key_current] =\
                instant_dictionary_current.copy()

    #
    # Build the list of dictionaries that is to be retrieved.
    #
    consumer_units_data_dictionaries_list = []
    for instant in instants:
        key_current = instant.instant_datetime.strftime(
            reports.globals.Constant.DATETIME_STRING_KEY_FORMAT)

        try:
            instant_dictionary_current = instants_dictionary[key_current]

        except KeyError:
            instant_dictionary_current = instant_dictionary_generic_value

        data_dictionary_current = instant_dictionary_current

        datetime_localtime_timetuple =\
            django.utils.timezone.localtime(
                instant.instant_datetime
            ).timetuple()

        data_dictionary_current['datetime'] =\
                int(time.mktime(datetime_localtime_timetuple))

        consumer_units_data_dictionaries_list.append(
            data_dictionary_current.copy())

    return consumer_units_data_dictionaries_list



################################################################################
#
# Render Scripts
#
################################################################################

def render_instant_measurements(
        request
):

    template_variables = {
        'axis_list': None,
        'columns' : None,
        'columns_statistics' : None,
        'column_units': None,
        'column_unit_axis_indexes': None,
        'max' : None,
        'min' : None,
        'rows' : None
    }

    if not request.method == "GET":
        raise django.http.Http404

    if not "electrical-parameter-name01" in request.GET:
        return django.http.HttpResponse(content="", status=200)

    #
    # Build a request data list in order to normalize it.
    #
    request_data_list = []
    consumer_unit_counter = 1
    consumer_unit_get_key = "consumer-unit%02d" % consumer_unit_counter
    while request.GET.has_key(consumer_unit_get_key):
        date_from_get_key = "date-from%02d" % consumer_unit_counter
        date_to_get_key = "date-to%02d" % consumer_unit_counter
        electrical_parameter_name_get_key =\
            "electrical-parameter-name%02d" % consumer_unit_counter

        try:
            consumer_unit_id = request.GET[consumer_unit_get_key]
            date_from_string = request.GET[date_from_get_key]
            date_to_string = request.GET[date_to_get_key]
            electrical_parameter_name =\
                request.GET[electrical_parameter_name_get_key]

        except KeyError:
            logger.error(
                reports.globals.SystemError.RENDER_INSTANT_MEASUREMENTS_ERROR)

            raise django.http.Http404

        datetime_from = datetime.datetime.strptime(date_from_string, "%Y-%m-%d")
        datetime_to = datetime.datetime.strptime(date_to_string, "%Y-%m-%d")
        datetime_from = datetime_from.replace(hour=00, minute=00, second=00)
        datetime_to = datetime_to.replace(hour=23, minute=59, second=59)
        request_data_list_item =\
            (consumer_unit_id,
             datetime_from,
             datetime_to,
             electrical_parameter_name)

        request_data_list.append(request_data_list_item)
        consumer_unit_counter += 1
        consumer_unit_get_key = "consumer-unit%02d" % consumer_unit_counter

    #
    # Normalize the data list.
    #
    request_data_list_normalized =\
        get_request_data_list_normalized(request_data_list)

    #
    # Build the columns list.
    #
    column_strings =\
        get_column_strings_electrical_parameter(request_data_list_normalized)

    template_variables['columns'] = column_strings

    columns_units_list = get_column_units_list(request_data_list_normalized)
    template_variables['column_units'] = columns_units_list

    #
    # Build and normalize the data clusters list.
    #
    granularity = None
    if "granularity" in request.GET:
        if request.GET['granularity'] == "raw":
            granularity = "raw"
            template_variables['granularity'] = "raw_data"

    data_clusters_list = get_data_clusters_list(request_data_list_normalized,
                                                granularity)
    normalize_data_clusters_list(data_clusters_list)

    axis_dictionary = \
        get_axis_dictionary(data_clusters_list, columns_units_list)

    axis_dictionaries_list = get_axis_dictionaries_list(axis_dictionary)
    template_variables['axis_list'] = axis_dictionaries_list

    column_units_axis_indexes =\
        get_column_units_axis_indexes(
            columns_units_list,
            axis_dictionaries_list)

    template_variables['column_unit_axis_indexes'] = column_units_axis_indexes

    #
    # Create the json using the data clusters list normalized
    #
    data_clusters_json = get_data_clusters_json(data_clusters_list)

    if data_clusters_json is None:
        raise django.http.Http404

    template_variables['rows'] = data_clusters_json

    #
    # Get statistical values
    #
    maximum, minimum = get_data_clusters_list_limits(data_clusters_list)
    data_clusters_statistics = get_data_clusters_statistics(data_clusters_list)

    template_variables['max'] = maximum
    template_variables['min'] = minimum
    template_variables['columns_statistics'] = data_clusters_statistics
    template_variables['series'] = zip(
        template_variables['axis_list'],
        template_variables['column_unit_axis_indexes'] )
    template_context =\
        django.template.context.RequestContext(request, template_variables)

    return django.shortcuts.render_to_response(
               "reports/instant-measurements.html",
               template_context)


def render_report_consumed_by_month (
        request
):
    template_variables = {
        'max' : None,
        'min' : None,
        'rows' : None,
    }

    if not request.method == "GET":
        raise django.http.Http404
    if not "electrical-parameter-name" in request.GET:
        return django.http.HttpResponse(content="", status=200)
    try:
        consumer_unit_id = request.GET['consumer-unit-id']
        month = int(request.GET['month'])
        year = int(request.GET['year'])
        electrical_parameter_name = request.GET['electrical-parameter-name']

    except KeyError:
        raise django.http.Http404

    days = variety.getMonthDays(month, year)
    first_week_start_datetime = days[0]
    last_week_end_datetime = days[-1]

    #
    # For the purposes of this report, the granularity is an hour but this is
    # intended to be extended, it should be retrieved as GET parameter.
    #
    granularity_seconds = 3600
    data_cluster_consumed =\
        get_data_cluster_consumed_normalized (
            consumer_unit_id,
            first_week_start_datetime,
            last_week_end_datetime,
            electrical_parameter_name,
            granularity_seconds)

    template_variables['rows'] = data_cluster_consumed
    maximun, minimun = get_data_cluster_limits(data_cluster_consumed)

    if maximun <= minimun:
        minimun = 0

    template_variables['max'] = maximun
    template_variables['min'] = minimun

    template_variables['ff'] = last_week_end_datetime
    template_variables['fi'] = last_week_end_datetime - \
                               datetime.timedelta(days=7)
    template_variables['consumer_unit_id'] = request.GET['consumer-unit-id']
    template_variables['years'] = request.session['years']
    template_variables['current_week'] = variety.\
        get_week_of_month_from_datetime(first_week_start_datetime)
    template_variables['current_year'] = year
    template_variables['current_month'] = month

    template_variables['electric_data'] = electrical_parameter_name

    template_context =\
        django.template.context.RequestContext(request, template_variables)

    return django.shortcuts.render_to_response(
               "reports/consumed-by-month.html",
               template_context)