#coding:utf-8

class Constant:

    DECIMAL_FIELD_DECIMAL_PLACES = 6
    DECIMAL_FIELD_MAX_DIGITS = 20

    NAME_LENGTH = 255
    NAME_TRANSACTIONAL_LENGTH = 128


class ModelFieldName:

    #
    # Naming convention:
    # MODEL_NAME__FIELD_NAME
    #
    CONSUMER_UNIT_INSTANT_ELECTRIC_DATA__CONSUMER_UNIT_PROFILE =\
        u"Consumer Unit Profile"

    CONSUMER_UNIT_INSTANT_ELECTRIC_DATA__ELECTRICAL_PARAMETER =\
        u"Electrical Parameter"

    CONSUMER_UNIT_INSTANT_ELECTRIC_DATA__ID = u"Id"
    CONSUMER_UNIT_INSTANT_ELECTRIC_DATA__INSTANT = u"Instant"
    CONSUMER_UNIT_INSTANT_ELECTRIC_DATA__VALUE = u"Value"

    CONSUMER_UNIT_PROFILE__BUILDING_NAME = u"Consumer Unit Building Name"
    CONSUMER_UNIT_PROFILE__ELECTRIC_DEVICE_TYPE_NAME =\
        u"Consumer Unit Electric Device Type Name"

    CONSUMER_UNIT_PROFILE__PART_OF_BUILDING_NAME =\
        u"Consumer Unit Part Of Building Name"

    CONSUMER_UNIT_PROFILE__TRANSACTIONAL_ID = u"Consumer Unit Transactional Id"

    ELECTRICAL_PARAMETER__NAME = u"Electrical Parameter Name"
    ELECTRICAL_PARAMETER__NAME_TRANSACTIONAL =\
        u"Electrical Parameter Name Transactional"

    ELECTRICAL_PARAMETER__TYPE = u"Electrical Parameter Type"
    ELECTRICAL_PARAMETER__TYPE__CUMULATIVE = u"Cumulative"
    ELECTRICAL_PARAMETER__TYPE__INSTANT = u"Instant"

    INSTANT__INSTANT_DATETIME = u"Instant Datetime"
    INSTANT__INSTANT_DELTA = u"Instant Delta"

    INSTANT_DELTA__DELTA_SECONDS = u"Instant Delta Seconds"
    INSTANT_DELTA__NAME = u"Instant Delta Name"


class ModelFieldRelatedName:

    #
    # Naming convention:
    # MODEL_NAME
    #

    INSTANT = "instants"

    CONSUMER_UNIT_INSTANT_ELECTRIC_DATA = "electric_data"