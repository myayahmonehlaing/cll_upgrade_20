""" ""Data models for various enumerations used in the application."""

# pylint: disable=invalid-enum-extension
from .enum_ext import EnumExt


class InvoiceStatus(EnumExt):
    """Enumeration for Invoice Statuses."""

    DRAFT = ("draft", "Draft")
    PAID = ("paid", "Paid")
    UNPAID = ("unpaid", "Unpaid")
    PARTIALLY = ("partially_paid", " Partially Paid")
    CANCELLED = ("cancelled", " cancelled")
    OPEN = ("open", " Open")
    CLOSED = ("closed", " Closed")


class VisitType(EnumExt):
    """Enumeration for Visit Types."""

    NEW = ("new", "1.New Patient Visit")
    FOLLOW = ("follow", "2.Follow-up Visit")
    CHECK = ("check", "3.Check-up Visit")
    VACCINATE = ("vaccination", "4.For Vaccination Service")
    MEDICAL = ("medical", "5.Home Medical Care")
    ATTENDANT = ("attendant", "6.Attendant Consult")


class PartOfPackage(EnumExt):
    """Enumeration for Package Inclusion."""

    YES = ("yes", "Yes")
    NO = ("no", "No")
