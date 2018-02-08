goog.provide('grrUi.semantic.rekall');
goog.provide('grrUi.semantic.rekall.rekallModule');

goog.require('grrUi.core');  // USE: coreModule

goog.require('grrUi.semantic.rekall.logDirective');       // USE: LogDirective
goog.require('grrUi.semantic.rekall.metadataDirective');  // USE: MetadataDirective
goog.require('grrUi.semantic.rekall.registeredUnixTimeStampDirective');  // USE: RegisteredUnixTimeStampDirective
goog.require('grrUi.semantic.rekall.rekallDefaultValueDirective');  // USE: RekallDefaultValueDirective
goog.require('grrUi.semantic.rekall.rekallJsonDirective');  // USE: RekallJsonDirective
goog.require('grrUi.semantic.rekall.rekallRegistryService');  // USE: RekallRegistryService
goog.require('grrUi.semantic.rekall.rekallValueDirective');  // USE: RekallValueDirective
goog.require('grrUi.semantic.rekall.tableDirective');  // USE: TableDirective


/**
 * Module with directives that render Rekall messages.
 */
grrUi.semantic.rekall.rekallModule = angular.module('grrUi.semantic.rekall',
                                       [grrUi.core.coreModule.name,
                                        'ui.bootstrap']);

grrUi.semantic.rekall.rekallModule.directive(
    grrUi.semantic.rekall.logDirective.LogDirective.directive_name,
    grrUi.semantic.rekall.logDirective.LogDirective);
grrUi.semantic.rekall.rekallModule.directive(
    grrUi.semantic.rekall.metadataDirective.MetadataDirective.directive_name,
    grrUi.semantic.rekall.metadataDirective.MetadataDirective);
grrUi.semantic.rekall.rekallModule.directive(
    grrUi.semantic.rekall.registeredUnixTimeStampDirective.RegisteredUnixTimeStampDirective.directive_name,
    grrUi.semantic.rekall.registeredUnixTimeStampDirective.RegisteredUnixTimeStampDirective);
grrUi.semantic.rekall.rekallModule.directive(
    grrUi.semantic.rekall.rekallDefaultValueDirective.RekallDefaultValueDirective.directive_name,
    grrUi.semantic.rekall.rekallDefaultValueDirective.RekallDefaultValueDirective);
grrUi.semantic.rekall.rekallModule.directive(
    grrUi.semantic.rekall.rekallJsonDirective.RekallJsonDirective.directive_name,
    grrUi.semantic.rekall.rekallJsonDirective.RekallJsonDirective);
grrUi.semantic.rekall.rekallModule.directive(
    grrUi.semantic.rekall.rekallValueDirective.RekallValueDirective.directive_name,
    grrUi.semantic.rekall.rekallValueDirective.RekallValueDirective);
grrUi.semantic.rekall.rekallModule.directive(
    grrUi.semantic.rekall.tableDirective.TableDirective.directive_name,
    grrUi.semantic.rekall.tableDirective.TableDirective);

grrUi.semantic.rekall.rekallModule.service(
    grrUi.semantic.rekall.rekallRegistryService.RekallRegistryService
        .service_name,
    grrUi.semantic.rekall.rekallRegistryService.RekallRegistryService);

grrUi.semantic.rekall.rekallModule.run(function(grrRekallDirectivesRegistryService) {
  var registry = grrRekallDirectivesRegistryService;

  registry.registerDirective(
      grrUi.semantic.rekall.registeredUnixTimeStampDirective.RegisteredUnixTimeStampDirective.rekall_type,
      grrUi.semantic.rekall.registeredUnixTimeStampDirective.RegisteredUnixTimeStampDirective);
});
