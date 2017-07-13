#!/usr/bin/env python
"""UI reports related rdfvalues."""

from grr.lib.rdfvalues import structs as rdf_structs
from grr.proto.api import stats_pb2


class ApiReportDescriptor(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiReportDescriptor


class ApiReport(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiReport


class ApiReportData(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiReportData


class ApiStackChartReportData(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiStackChartReportData


class ApiReportTickSpecifier(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiReportTickSpecifier


class ApiPieChartReportData(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiPieChartReportData


class ApiLineChartReportData(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiLineChartReportData


class ApiAuditChartReportData(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiAuditChartReportData


class ApiReportDataPoint1D(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiReportDataPoint1D


class ApiReportDataSeries2D(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiReportDataSeries2D


class ApiReportDataPoint2D(rdf_structs.RDFProtoStruct):
  protobuf = stats_pb2.ApiReportDataPoint2D
